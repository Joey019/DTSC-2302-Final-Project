"""
embed_books.py - Step 2 of the pipeline: turn each book's text into embeddings.

    python scripts/embed_books.py

Input:   data/processed/cleaned_books.parquet, cleaned_reviews.parquet  (from clean_data.py)
Output:  data/processed/embeddings/
           books.parquet          the books, plus the text used for each (for cluster keywords later)
           description_emb.npy    one embedding per book description
           review_mean_emb.npy    the average embedding of each book's reviews (zeros if it has none)
           review_emb.npy         one embedding per selected review
           review_index.parquet   which book each row of review_emb.npy belongs to

What it does
  1. Pick up to REVIEWS_PER_BOOK reviews for every book, with the SAME rule for every book:
     reviews of a medium length first, rotating through the star ratings the book has.
     Votes and other popularity signals are never used, so popular books get no advantage.
  2. Split texts that are longer than the model's limit into pieces (instead of cutting them off).
  3. Embed descriptions and reviews separately with a sentence-transformer model.
     Descriptions and reviews are saved separately so they can be weighted later (reduce_umap.py).

This step is slow on a laptop CPU (hours for the full data). It saves its progress every
CHUNK_SIZE texts: if it stops, run it again and it continues where it left off.
"""

import shutil
import time
from pathlib import Path

import numpy as np
import polars as pl
import torch
from sentence_transformers import SentenceTransformer

# =============================================================================
# SETTINGS
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]  # the project folder
INPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "data" / "processed" / "embeddings"

REVIEWS_PER_BOOK = 10            # at most this many reviews per book (same for every book)
PREFERRED_MIN_WORDS = 30         # reviews between these lengths are picked first
PREFERRED_MAX_WORDS = 300
SEED = 42                        # makes the "random" review order repeatable

MODEL = "BAAI/bge-small-en-v1.5"  # 384 numbers per text; reads up to 512 tokens
MAX_TOKENS = 512
BATCH_SIZE = 32                  # texts per batch; lower it if you run out of memory
CHUNK_SIZE = 20_000              # progress is saved after every chunk of this many texts


# =============================================================================
# 1. PICK REVIEWS
# =============================================================================
def pick_reviews(reviews: pl.DataFrame) -> pl.DataFrame:
    """Up to REVIEWS_PER_BOOK reviews per book, the same rule for every book.

    Order of preference within a book:
      - reviews of PREFERRED_MIN_WORDS..PREFERRED_MAX_WORDS words come first;
      - then rotate through the star ratings: the first review of each rating, then the
        second of each rating, and so on (within a rating, the order is random but repeatable).
    """
    reviews = reviews.with_columns(
        pl.col("word_count").is_between(PREFERRED_MIN_WORDS, PREFERRED_MAX_WORDS).alias("good_length"),
        pl.col("review_id").hash(SEED).alias("random_order"),
    )
    reviews = reviews.with_columns(
        # 1 = the first review of its star rating (for this book), 2 = the second, ...
        pl.col("random_order").rank("ordinal").over(["work_id", "good_length", "rating"]).alias("turn")
    )
    return (
        reviews.sort(["work_id", "good_length", "turn", "random_order"], descending=[False, True, False, False])
        .group_by("work_id", maintain_order=True)
        .head(REVIEWS_PER_BOOK)
    )


# =============================================================================
# 2. SPLIT LONG TEXTS
# =============================================================================
def split_long_texts(texts: list[str], tokenizer) -> tuple[list[str], list[int]]:
    """Split texts longer than MAX_TOKENS into pieces.

    Returns the pieces, and for each piece the position of the text it came from.
    """
    limit = MAX_TOKENS - 2  # the model adds 2 special tokens to every text
    pieces, source = [], []
    for i, text in enumerate(texts):
        tokens = tokenizer(text, add_special_tokens=False)["input_ids"]
        for start in range(0, max(len(tokens), 1), limit):
            pieces.append(text if len(tokens) <= limit else tokenizer.decode(tokens[start : start + limit]))
            source.append(i)
    return pieces, source


# =============================================================================
# 3. EMBED (with progress saved to disk)
# =============================================================================
def embed(pieces: list[str], model: SentenceTransformer) -> np.ndarray:
    chunk_dir = OUTPUT_DIR / "chunks"
    # Chunks are only left behind by a run that stopped early (a finished run deletes them).
    # They are reused only if that run had the same number of texts; otherwise start over.
    check_file = chunk_dir / "text_count.txt"
    if chunk_dir.exists() and (not check_file.exists() or check_file.read_text() != str(len(pieces))):
        shutil.rmtree(chunk_dir)
    chunk_dir.mkdir(parents=True, exist_ok=True)
    check_file.write_text(str(len(pieces)))

    results = []
    n_chunks = (len(pieces) + CHUNK_SIZE - 1) // CHUNK_SIZE
    started = time.time()
    for c in range(n_chunks):
        chunk_file = chunk_dir / f"chunk_{c:04d}.npy"
        if chunk_file.exists():
            print(f"      chunk {c + 1}/{n_chunks}: already done, loading it")
        else:
            batch = pieces[c * CHUNK_SIZE : (c + 1) * CHUNK_SIZE]
            vectors = model.encode(batch, batch_size=BATCH_SIZE, normalize_embeddings=True)
            np.save(chunk_file, vectors.astype(np.float16))  # float16 halves the file size
            minutes = (time.time() - started) / 60
            print(f"      chunk {c + 1}/{n_chunks} done ({minutes:.0f} min so far)")
        results.append(np.load(chunk_file).astype(np.float32))
    return np.vstack(results)


def average_by_group(vectors: np.ndarray, groups: np.ndarray, n_groups: int) -> np.ndarray:
    """Average the vectors that share a group number. Groups with no vectors get zeros."""
    sums = np.zeros((n_groups, vectors.shape[1]), dtype=np.float32)
    np.add.at(sums, groups, vectors)
    counts = np.bincount(groups, minlength=n_groups)[:, None]
    return np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)


def unit_length(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms > 0)


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    print("[1/4] Loading cleaned books and reviews...")
    books = pl.read_parquet(INPUT_DIR / "cleaned_books.parquet").sort("work_id")
    reviews = pl.read_parquet(INPUT_DIR / "cleaned_reviews.parquet",
                              columns=["work_id", "review_id", "rating", "word_count", "cleaned_text"])
    print(f"      {books.height:,} books, {reviews.height:,} reviews")

    print(f"[2/4] Picking up to {REVIEWS_PER_BOOK} reviews per book...")
    picked = pick_reviews(reviews)
    del reviews
    row_of_book = {work_id: i for i, work_id in enumerate(books["work_id"].to_list())}
    picked = picked.with_columns(pl.col("work_id").replace_strict(row_of_book, return_dtype=pl.Int64).alias("book_row"))
    reviews_used = np.bincount(picked["book_row"].to_numpy(), minlength=books.height)
    print(f"      {picked.height:,} reviews picked; {(reviews_used == 0).sum():,} books have none")

    print("[3/4] Splitting long texts...")
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    model = SentenceTransformer(MODEL, device=device)
    model.max_seq_length = MAX_TOKENS
    texts = books["description"].to_list() + picked["cleaned_text"].to_list()  # descriptions first
    pieces, source = split_long_texts(texts, model.tokenizer)
    print(f"      {len(texts):,} texts -> {len(pieces):,} pieces")

    print(f"[4/4] Embedding with {MODEL} on {device} (the slow part)...")
    piece_vectors = embed(pieces, model)
    text_vectors = unit_length(average_by_group(piece_vectors, np.array(source), len(texts)))  # pieces -> texts

    n_books = books.height
    description_emb = text_vectors[:n_books]
    review_emb = text_vectors[n_books:]
    review_mean_emb = average_by_group(review_emb, picked["book_row"].to_numpy(), n_books)

    # The text of each book (description + picked reviews), used later for cluster keywords.
    review_text = picked.group_by("book_row").agg(pl.col("cleaned_text").str.join(" ").alias("review_text"))
    books = (
        books.with_row_index("book_row")
        .with_columns(pl.Series("n_reviews_used", reviews_used))
        .join(review_text.with_columns(pl.col("book_row").cast(pl.UInt32)), on="book_row", how="left")
        .with_columns(pl.concat_str(["description", pl.col("review_text").fill_null("")], separator=" ")
                      .str.strip_chars().alias("document"))
        .drop("book_row", "review_text")
    )

    books.write_parquet(OUTPUT_DIR / "books.parquet")
    np.save(OUTPUT_DIR / "description_emb.npy", description_emb)
    np.save(OUTPUT_DIR / "review_mean_emb.npy", review_mean_emb)
    np.save(OUTPUT_DIR / "review_emb.npy", review_emb.astype(np.float16))
    picked.select("book_row", "work_id", "review_id", "rating", "word_count").write_parquet(OUTPUT_DIR / "review_index.parquet")
    shutil.rmtree(OUTPUT_DIR / "chunks")  # finished, so the saved progress is no longer needed
    print(f"\nSaved embeddings for {n_books:,} books and {len(review_emb):,} reviews to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
