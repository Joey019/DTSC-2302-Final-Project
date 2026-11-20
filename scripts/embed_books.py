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
  0. Mask character and author names (MASK_NAMES), so clusters form around what books are about, not
     around one series' names. spaCy finds PERSON names in every text; every name word found anywhere in
     a book's description or reviews is replaced with NAME_PLACEHOLDER in all of that book's texts (and in
     all books by the same author). Words used mostly by one author ("series words": Maigret, Bayport) are
     masked too; normal words, genre words and real places are kept. Masked texts are cached, so a
     restart skips this step.
  1. Pick up to REVIEWS_PER_BOOK reviews for every book, with the SAME rule for every book (pick_reviews.py):
     reviews of a medium length first, rotating through the star ratings the book has, preferring reviews
     that describe the book (not just opinion), are typical of its other reviews, and differ from the
     ones already picked. Votes and other popularity signals are never used, so popular books get no advantage.
  2. Split texts that are longer than the model's limit into pieces (instead of cutting them off).
  3. Embed descriptions and reviews separately with a sentence-transformer model.
     Descriptions and reviews are saved separately so they can be weighted later (reduce_umap.py).

This step is slow on a laptop CPU (hours for the full data). It saves its progress every
CHUNK_SIZE texts: if it stops, run it again and it continues where it left off.
"""

import re
import shutil
import time
from collections import Counter
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
SKIP_UNRATED_REVIEWS = True      # skip reviews with no star rating (rating 0): often notes or progress updates
SEED = 42                        # makes the "random" review order repeatable

MODEL = "BAAI/bge-small-en-v1.5"  # 384 numbers per text; reads up to 512 tokens
MAX_TOKENS = 512
BATCH_SIZE = 16                  # texts per batch; lower it if you run out of memory
CHUNK_SIZE = 20_000              # progress is saved after every chunk of this many texts

MASK_NAMES = True                # replace character/author names before embedding
NAME_PLACEHOLDER = "someone"     # a plain word (also an English stop word, so it never becomes a cluster keyword)
NAME_MODEL = "en_core_web_sm"    # spaCy model; python -m spacy download en_core_web_sm
NAME_PROCESSES = 1               # spaCy worker processes (each loads its own copy of the model)
# Words that can appear inside a detected name but aren't names themselves (titles, ranks, small words).
NOT_NAMES = {"Mr", "Mrs", "Ms", "Miss", "Dr", "Sir", "Lady", "Lord", "Detective", "Inspector", "Sergeant",
             "Agent", "Captain", "Chief", "Officer", "Professor", "Father", "Sister", "Brother", "Uncle",
             "Aunt", "Saint", "St", "The", "A", "An", "And", "Of", "I", "He", "She", "It", "We", "They",
             "DI", "DCI", "DS", "DC", "PC", "DSI", "Supt", "Superintendent", "Constable", "Commissario",
             "Sgt", "Lt", "Lieutenant", "Col", "Colonel", "Gen", "General", "Major", "Det", "Insp", "Rev",
             "Reverend", "Pastor", "Prof", "Judge", "Sheriff", "Deputy", "Marshal", "Mma", "Rra", "Jr", "Sr",
             "Mom", "Dad", "Mum", "Grandma", "Granny", "Grandpa", "Nurse", "Doc", "Madame", "Monsieur"}
# Which words count as names:
COMMON_WORD_SHARE = 0.7      # (a) a word written in lowercase at least this often is a normal word: never masked
MIN_WORD_COUNT = 20          #     ...judged only for words seen at least this often (rarer words: treated as names)
ANY_CASE_SHARE = 0.1         # (b) a name written in lowercase at most this often is also masked in lowercase ("reacher")
MIN_AUTHOR_BOOKS = 2         # (c) a name found in this many books by an author is masked in all of that author's books
SERIES_AUTHOR_SHARE = 0.5    # (d) a capitalised word with at least this share of its books by one author...
SERIES_MIN_BOOKS = 3         #     ...in at least this many of that author's books...
SERIES_MAX_LOWER = 0.3       #     ...and rarely written in lowercase, is a series word: masked in that author's books
PLACE_LABELS = {"GPE", "LOC", "NORP", "FAC"}  # words spaCy mostly tags as places/nationalities (in that author's
SERIES_PLACE_AUTHORS = 5     # books) are kept, unless it's a series word used by fewer authors than this (invented place)
REAL_PLACE_SHARE = 0.8       # a word tagged as a place at least this often across all books (vs person/organisation),
REAL_PLACE_MIN_TAGS = 30     # ...with at least this many tags, by at least SERIES_PLACE_AUTHORS authors: never masked
# Countries, US states, regions and peoples that are never masked (spaCy often tags them as persons/organisations).
REAL_PLACES_FILE = Path(__file__).resolve().parent / "real_places.txt"


# =============================================================================
# 0. MASK NAMES
# =============================================================================
def name_words(doc) -> set[str]:
    """Capitalised words inside the PERSON names spaCy found in one text."""
    words = set()
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            for w in re.findall(r"[A-Z][\w'.]*", ent.text):  # split at hyphens ("Husband-of-the-Year")
                w = re.sub(r"(?:'s|'|\.)$", "", w)
                if len(w) > 1 and w not in NOT_NAMES:
                    words.add(w)
    return words


CAPITALISED = re.compile(r"\b[A-Z][a-z][\w'-]*")
LOWERCASE = re.compile(r"\b[a-z][\w'-]*")


def word_stats(texts: list[str], owner: list[int], author_of_book: list) -> dict:
    """Counts over all texts (no spaCy): how often each word is written in lowercase, and series words (d)."""
    capital, lower = Counter(), Counter()
    words_of_book: dict[int, set[str]] = {}
    for text, b in zip(texts, owner):
        found = CAPITALISED.findall(text)
        capital.update(found)
        lower.update(LOWERCASE.findall(text))
        # series-word candidates: plain words only ("Botswana's" -> "Botswana", hyphenated words skipped)
        words_of_book.setdefault(b, set()).update(
            w for w in (re.sub(r"'s?$", "", x) for x in found) if len(w) >= 3 and "-" not in w and "'" not in w)

    def lower_share(w: str) -> float:
        n_low = lower.get(w.lower(), 0)
        return n_low / (n_low + capital.get(w, 0) + 1e-9)

    # (d) series words: capitalised words used mostly in one author's books
    books_per_author: dict[str, Counter] = {}
    for b, ws in words_of_book.items():
        if author_of_book[b] is None:
            continue
        for w in ws:
            books_per_author.setdefault(w, Counter())[author_of_book[b]] += 1
    series_words: dict = {}
    n_authors = {w: len(by_author) for w, by_author in books_per_author.items()}
    for w, by_author in books_per_author.items():
        top_author, top_books = by_author.most_common(1)[0]
        if (top_books >= SERIES_MIN_BOOKS and top_books / sum(by_author.values()) >= SERIES_AUTHOR_SHARE
                and lower_share(w) < SERIES_MAX_LOWER):
            series_words.setdefault(top_author, set()).add(w)
    return {"capital": capital, "lower": lower, "lower_share": lower_share, "series_words": series_words,
            "n_authors": n_authors}


def mask_names(texts: list[str], owner: list[int], author_of_book: list, stats: dict | None = None) -> list[str]:
    """Mask names and series words, book by book, in all texts of that book (rules a-d in the settings)."""
    import spacy

    stats = stats or word_stats(texts, owner, author_of_book)
    nlp = spacy.load(NAME_MODEL, disable=["parser", "lemmatizer", "attribute_ruler", "tagger", "morphologizer"])
    names_of_book: dict[int, set[str]] = {}
    label = Counter()  # (author, word, "person"/"place") -> times spaCy tagged it so in that author's books
    started = time.time()
    docs = nlp.pipe(texts, batch_size=256, n_process=NAME_PROCESSES)
    for i, doc in enumerate(docs):
        names_of_book.setdefault(owner[i], set()).update(name_words(doc))
        a = author_of_book[owner[i]]
        for ent in doc.ents:
            kind = ("person" if ent.label_ == "PERSON" else "place" if ent.label_ in PLACE_LABELS
                    else "org" if ent.label_ == "ORG" else None)
            if kind:
                label.update((a, w, kind) for w in CAPITALISED.findall(ent.text))
        if (i + 1) % 50_000 == 0:
            print(f"      names: {i + 1:,}/{len(texts):,} texts ({(time.time() - started) / 60:.0f} min)", flush=True)

    capital, lower, lower_share = stats["capital"], stats["lower"], stats["lower_share"]
    n_authors, series_words = stats["n_authors"], stats["series_words"]

    # A clearly real place (London, Botswana): across all books, mostly tagged as a place, often enough, and by
    # several authors. Organisation tags count against it (the small model often tags names like "Lucas Davenport"
    # as an organisation or a place inside one author's books).
    tags, place_authors = Counter(), {}
    for (a, w, kind), n in label.items():
        tags[(w, kind)] += n
        if kind == "place":
            place_authors.setdefault(w, set()).add(a)
    real_place = {w for (w, kind), n in tags.items() if kind == "place" and n >= REAL_PLACE_MIN_TAGS
                  and n / (n + tags[(w, "person")] + tags[(w, "org")]) >= REAL_PLACE_SHARE
                  and len(place_authors[w]) >= SERIES_PLACE_AUTHORS}
    real_place |= {line.strip() for line in REAL_PLACES_FILE.read_text(encoding="utf-8").splitlines()
                   if line.strip() and not line.startswith("#") and " " not in line.strip()}

    def maskable(w: str) -> bool:
        if w in NOT_NAMES or w in real_place:
            return False
        seen = capital.get(w, 0) + lower.get(w.lower(), 0)
        return not (seen >= MIN_WORD_COUNT and lower_share(w) >= COMMON_WORD_SHARE)  # (a) a normal word

    def place(w: str, a) -> bool:
        # (d) only: a series word that spaCy mostly tags as a place in this author's books, and that at least
        # SERIES_PLACE_AUTHORS authors use, is a real setting (Venice, Botswana, Arapaho): keep it. Invented places
        # (Isola, Idaville) are used by fewer authors and are masked. Names spaCy found as PERSON are not checked:
        # the small model often tags character names as places/organisations ("Lucas Davenport").
        return label[(a, w, "place")] > label[(a, w, "person")] and n_authors.get(w, 0) >= SERIES_PLACE_AUTHORS

    # (c) names found in at least MIN_AUTHOR_BOOKS books by the same author
    author_names: dict = {}
    for b, names in names_of_book.items():
        if author_of_book[b] is not None:
            author_names.setdefault(author_of_book[b], Counter()).update(names)

    any_case, exact_case = {}, {}
    for b in set(owner):
        a = author_of_book[b]
        names = set(names_of_book.get(b, ()))
        series = series_words.get(a, set()) if a is not None else set()  # (d)
        if a is not None:
            names |= {w for w, n in author_names.get(a, Counter()).items() if n >= MIN_AUTHOR_BOOKS}  # (c)
        words = {w for w in names if maskable(w)} | {w for w in series - names if maskable(w) and not place(w, a)}
        loose = {w for w in words if lower_share(w) <= ANY_CASE_SHARE}  # (b)
        alt = lambda ws: r"\b(?:" + "|".join(sorted(map(re.escape, ws), key=len, reverse=True)) + r")\b"
        if loose:
            any_case[b] = re.compile(alt(loose), re.IGNORECASE)
        if words - loose:
            exact_case[b] = re.compile(alt(words - loose))

    repeat = re.compile(rf"{NAME_PLACEHOLDER}(?:[\s.-]+{NAME_PLACEHOLDER})+")
    masked = []
    for text, b in zip(texts, owner):
        for pattern in (any_case.get(b), exact_case.get(b)):
            if pattern is not None:
                text = pattern.sub(NAME_PLACEHOLDER, text)
        masked.append(repeat.sub(NAME_PLACEHOLDER, text))
    n_series = sum(len(s) for s in series_words.values())
    print(f"      {n_series:,} series words for {len(series_words):,} authors; "
          f"{sum(a != b for a, b in zip(texts, masked)):,} of {len(texts):,} texts changed")
    return masked


def masked_texts(texts: list[str], owner: list[int], author_of_book: list) -> list[str]:
    """mask_names(), cached in OUTPUT_DIR so a restarted run doesn't redo it."""
    cache = OUTPUT_DIR / "masked_texts.parquet"
    if cache.exists():
        cached = pl.read_parquet(cache)["text"].to_list()
        if len(cached) == len(texts):
            print("      using cached masked texts")
            return cached
    masked = mask_names(texts, owner, author_of_book)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"text": masked}).write_parquet(cache)
    return masked


# =============================================================================
# 1. PICK REVIEWS
# =============================================================================
def pick_reviews(reviews: pl.DataFrame, descriptions: list[str]) -> pl.DataFrame:
    """Meaningful reviews (length window + star rotation + content, representativeness, diversity).

    The rule lives in pick_reviews.py (same folder); its settings are at the top of that file.
    """
    import pick_reviews as picker

    # use the settings at the top of THIS file (pick_reviews.py has the same names as defaults)
    picker.REVIEWS_PER_BOOK, picker.PREFERRED_MIN_WORDS, picker.PREFERRED_MAX_WORDS = (
        REVIEWS_PER_BOOK, PREFERRED_MIN_WORDS, PREFERRED_MAX_WORDS)
    picker.SKIP_UNRATED_REVIEWS, picker.SEED = SKIP_UNRATED_REVIEWS, SEED
    picked = picker.pick_reviews(reviews, descriptions)
    return picked.drop("content_score")


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
    picked = pick_reviews(reviews, books["description"].to_list())
    del reviews
    row_of_book = {work_id: i for i, work_id in enumerate(books["work_id"].to_list())}
    picked = picked.with_columns(pl.col("work_id").replace_strict(row_of_book, return_dtype=pl.Int64).alias("book_row"))
    reviews_used = np.bincount(picked["book_row"].to_numpy(), minlength=books.height)
    print(f"      {picked.height:,} reviews picked; {(reviews_used == 0).sum():,} books have none")

    if MASK_NAMES:
        print(f"[2b] Masking names with spaCy {NAME_MODEL} (about an hour on a laptop CPU)...")
        all_texts = books["description"].to_list() + picked["cleaned_text"].to_list()
        owner = list(range(books.height)) + picked["book_row"].to_list()
        masked = masked_texts(all_texts, owner, books["author_id"].to_list())
        books = books.with_columns(pl.Series("description", masked[: books.height]))
        picked = picked.with_columns(pl.Series("cleaned_text", masked[books.height :]))

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
