"""
reduce_umap.py - Step 3 of the pipeline: one vector per book, then UMAP.

    python scripts/reduce_umap.py

Input:   data/processed/embeddings/          (from embed_books.py)
Output:  data/processed/clustering_inputs/   (read by notebooks/clustering.ipynb)
           books.parquet          book_id, title, genre_label, document, + book details
           embeddings_full.npy    one 384-number vector per book
           embeddings_umap.npy    the same vectors reduced to UMAP_DIMENSIONS numbers
           umap_model.joblib      the fitted UMAP model, to reduce NEW books the same way later:
                                      reducer = joblib.load(".../umap_model.joblib")
                                      new_reduced = reducer.transform(new_book_vectors)

What it does
  1. Combine each book's description and review embeddings into one vector:
         book = DESCRIPTION_WEIGHT * description + REVIEW_WEIGHT * (average of its reviews)
     The review average is first scaled to length 1, so the number of reviews a book has
     doesn't change how much its reviews count. Books without reviews use the description only.
  2. Reduce the vectors with UMAP, so the clustering works on a few dimensions instead of 384.

This step takes minutes, so it's the place to try different weights or UMAP settings.
"""

from pathlib import Path

import joblib
import numpy as np
import polars as pl
import umap

# =============================================================================
# SETTINGS
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]  # the project folder
INPUT_DIR = ROOT / "data" / "processed" / "embeddings"
OUTPUT_DIR = ROOT / "data" / "processed" / "clustering_inputs"

DESCRIPTION_WEIGHT = 0.5
REVIEW_WEIGHT = 0.5

UMAP_DIMENSIONS = 10  # numbers per book after reduction
UMAP_NEIGHBORS = 15   # larger = focus on broader structure, smaller = on local detail
UMAP_MIN_DIST = 0.0   # 0 packs similar books tightly together, which helps clustering
SEED = 42


def unit_length(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms > 0)


def main() -> None:
    print("[1/3] Combining description and review embeddings...")
    books = pl.read_parquet(INPUT_DIR / "books.parquet")
    description = np.load(INPUT_DIR / "description_emb.npy")
    review_average = unit_length(np.load(INPUT_DIR / "review_mean_emb.npy"))  # zeros stay zeros
    book_vectors = unit_length(DESCRIPTION_WEIGHT * description + REVIEW_WEIGHT * review_average)
    print(f"      {book_vectors.shape[0]:,} books x {book_vectors.shape[1]} numbers")

    print(f"[2/3] UMAP: {book_vectors.shape[1]} -> {UMAP_DIMENSIONS} dimensions...")
    reducer = umap.UMAP(n_components=UMAP_DIMENSIONS, n_neighbors=UMAP_NEIGHBORS, min_dist=UMAP_MIN_DIST,
                        metric="cosine", random_state=SEED)
    reduced = np.asarray(reducer.fit_transform(book_vectors), dtype=np.float32)

    print("[3/3] Saving...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # The clustering notebook needs one unique id per book: use the work id (all editions of a book).
    books = books.rename({"book_id": "edition_book_id", "work_id": "book_id"})
    first = ["book_id", "title", "genre_label", "document"]
    books.select(first + [c for c in books.columns if c not in first]).write_parquet(OUTPUT_DIR / "books.parquet")
    np.save(OUTPUT_DIR / "embeddings_full.npy", book_vectors.astype(np.float32))
    np.save(OUTPUT_DIR / "embeddings_umap.npy", reduced)
    joblib.dump(reducer, OUTPUT_DIR / "umap_model.joblib")  # needed to place new books into the clusters
    print(f"\nSaved clustering inputs for {len(reduced):,} books to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
