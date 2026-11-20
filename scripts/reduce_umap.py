"""
reduce_umap.py - Step 3 of the pipeline: one vector per book, then UMAP.

    python scripts/reduce_umap.py

Input:   data/processed/embeddings/          (from embed_books.py)
Output:  data/processed/clustering_inputs/   (read by notebooks/clustering.ipynb)
           books.parquet              book_id, title, genre_label, document, + book details
           embeddings_full.npy        one 384-number vector per book
           centering.npz              the average description and review vectors subtracted when CENTER is on
                                      (a NEW book must be combined with the same averages: see combine())
           embeddings_umap.npy        the same vectors reduced to UMAP_DIMENSIONS numbers (first seed)
           embeddings_umap_seed<N>.npy  the same, once per seed in UMAP_SEEDS (the notebook uses all of them
                                      to tell real differences between settings from UMAP's random luck)
           umap_model_seed<N>.joblib  the fitted UMAP model per seed, to reduce NEW books the same way later
                                      (use the seed named in clustering_results/summary.json):
                                          reducer = joblib.load(".../umap_model_seed42.joblib")
                                          new_reduced = reducer.transform(new_book_vectors)

What it does
  1. Combine each book's description and review embeddings into one vector:
         book = DESCRIPTION_WEIGHT * description + REVIEW_WEIGHT * trust * (average of its reviews)
     - Centering (CENTER): first subtract the average description vector from every description, and the
       average review vector from every review average. Two random books' review averages are very similar
       (most of each is general "review-ness"), so without this the reviews add less book-specific
       information than their weight suggests.
     - The review average is scaled to length 1, so the number of reviews doesn't change its length.
     - trust = n / (n + SHRINK_REVIEWS) for a book with n reviews: a book with 1-2 reviews leans more on
       its description. Books without reviews use the description only.
  2. Reduce the vectors with UMAP, so the clustering works on a few dimensions instead of 384.

The settings below were chosen by comparing the alternatives (centering on/off, SHRINK_REVIEWS 0/2/5,
review weight 0.3/0.5/0.7, UMAP neighbours 15-100, dimensions 10-25) on how well the clusters match
readers' sub-genre shelves. This step takes minutes, so it's the place to try other settings.
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

DESCRIPTION_WEIGHT = 0.3
REVIEW_WEIGHT = 0.7
CENTER = True         # subtract the average vector first (see above)
SHRINK_REVIEWS = 2    # trust in a book's reviews = n / (n + SHRINK_REVIEWS); 0 = trust every book's reviews fully

UMAP_DIMENSIONS = 15  # numbers per book after reduction
UMAP_NEIGHBORS = 50   # larger = focus on broader structure, smaller = on local detail
UMAP_MIN_DIST = 0.0   # 0 packs similar books tightly together, which helps clustering
UMAP_SEEDS = [42, 7, 123]  # UMAP is run once per seed (about 1.5 min each); the first one is the main result


def unit_length(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms > 0)


def combine(description: np.ndarray, review_average: np.ndarray, n_reviews: np.ndarray,
            averages: tuple | None = None) -> np.ndarray:
    # averages = (average description, average review vector); None = compute them from these books.
    # For NEW books, pass the saved ones: np.load("centering.npz") -> (f["description"], f["review"]).
    has_reviews = n_reviews > 0
    d, r = description.copy(), unit_length(review_average)  # books without reviews: zeros stay zeros
    if CENTER:
        d_avg, r_avg = averages if averages is not None else (d.mean(axis=0), r[has_reviews].mean(axis=0))
        d = unit_length(d - d_avg)
        r[has_reviews] = unit_length(r[has_reviews] - r_avg)
    trust = n_reviews / (n_reviews + SHRINK_REVIEWS) if SHRINK_REVIEWS else has_reviews.astype(np.float32)
    trust = np.where(has_reviews, trust, 0.0)[:, None]
    return unit_length(DESCRIPTION_WEIGHT * d + REVIEW_WEIGHT * trust * r).astype(np.float32)


def main() -> None:
    print("[1/3] Combining description and review embeddings...")
    books = pl.read_parquet(INPUT_DIR / "books.parquet")
    description = np.load(INPUT_DIR / "description_emb.npy").astype(np.float32)
    review_average = np.load(INPUT_DIR / "review_mean_emb.npy").astype(np.float32)
    n_reviews = books["n_reviews_used"].to_numpy().astype(np.float32)
    book_vectors = combine(description, review_average, n_reviews)
    print(f"      {book_vectors.shape[0]:,} books x {book_vectors.shape[1]} numbers")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[2/3] UMAP: {book_vectors.shape[1]} -> {UMAP_DIMENSIONS} dimensions, seeds {UMAP_SEEDS}...")
    for i, seed in enumerate(UMAP_SEEDS):
        reducer = umap.UMAP(n_components=UMAP_DIMENSIONS, n_neighbors=UMAP_NEIGHBORS, min_dist=UMAP_MIN_DIST,
                            metric="cosine", random_state=seed)
        reduced = np.asarray(reducer.fit_transform(book_vectors), dtype=np.float32)
        np.save(OUTPUT_DIR / f"embeddings_umap_seed{seed}.npy", reduced)
        # The model is needed to place NEW books into the clusters (about 370 MB per seed). The notebook
        # says in summary.json which seed its final K-Means model uses.
        joblib.dump(reducer, OUTPUT_DIR / f"umap_model_seed{seed}.joblib")
        if i == 0:  # the main result
            np.save(OUTPUT_DIR / "embeddings_umap.npy", reduced)
        print(f"      seed {seed} done")

    print("[3/3] Saving...")
    # The clustering notebook needs one unique id per book: use the work id (all editions of a book).
    books = books.rename({"book_id": "edition_book_id", "work_id": "book_id"})
    first = ["book_id", "title", "genre_label", "document"]
    books.select(first + [c for c in books.columns if c not in first]).write_parquet(OUTPUT_DIR / "books.parquet")
    np.save(OUTPUT_DIR / "embeddings_full.npy", book_vectors)
    r = unit_length(review_average)
    np.savez(OUTPUT_DIR / "centering.npz", description=description.mean(axis=0), review=r[n_reviews > 0].mean(axis=0))
    print(f"\nSaved clustering inputs for {len(book_vectors):,} books to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
