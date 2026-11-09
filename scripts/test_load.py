from pathlib import Path
import polars as pl

books_path = Path("data/raw/goodreads_books_mystery_thriller_crime.json.gz")
reviews_path = Path("data/raw/goodreads_reviews_mystery_thriller_crime.json.gz")

print(f"Books file exists: {books_path.exists()}")
print(f"Reviews file exists: {reviews_path.exists()}")

if books_path.exists() and reviews_path.exists():
    print("\nScanning books dataset (first 2 rows)...")
    books_df = (
        pl.scan_ndjson(books_path)
        .select(["book_id", "title"])
        .limit(2)
        .collect()
    )
    print(books_df)

    print("\nScanning reviews dataset (first 2 rows)...")
    reviews_df = (
        pl.scan_ndjson(reviews_path)
        .select(["book_id", "rating", "review_text"])
        .limit(2)
        .collect()
    )
    print(reviews_df)
    print("\nPipeline ready for preprocessing.")
else:
    print("\nError: One or both files missing in data/raw/.")