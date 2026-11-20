"""
pipeline.py - Run the whole data pipeline, top to bottom.

    python scripts/pipeline.py

Runs, in order:
  1. clean_data.py    raw data  -> data/processed/cleaned_books.parquet, cleaned_reviews.parquet
  2. embed_books.py   cleaned   -> data/processed/embeddings/          (the slow step: hours on a CPU)
  3. reduce_umap.py   embeddings -> data/processed/clustering_inputs/  (read by notebooks/clustering.ipynb)
  4. genre_tags.py    sub-genre tags from readers' shelves, used to score the clusters (about a minute)

Every step overwrites its previous output. The settings are at the top of each script.
Download the raw data first, once:  python scripts/fetch_data.py
"""

import time

import clean_data
import embed_books
import genre_tags
import reduce_umap

STEPS = [
    ("Step 1/4: clean the data", clean_data),
    ("Step 2/4: embed the books", embed_books),
    ("Step 3/4: UMAP", reduce_umap),
    ("Step 4/4: sub-genre tags", genre_tags),
]

if __name__ == "__main__":
    pipeline_start = time.time()
    for title, step in STEPS:
        print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
        step_start = time.time()
        step.main()
        print(f"({title} took {(time.time() - step_start) / 60:.1f} min)")
    print(f"\nPipeline finished in {(time.time() - pipeline_start) / 60:.1f} min.")
    print("Next: open notebooks/clustering.ipynb and click Run All.")
