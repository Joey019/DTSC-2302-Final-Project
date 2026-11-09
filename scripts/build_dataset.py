from pathlib import Path
import polars as pl


def build_cleaned_corpus(
    min_word_count: int = 15,
    max_reviews_per_book: int = 40,
    output_path: Path = Path("data/processed/cleaned_reviews.parquet"),
) -> None:
    books_file = Path("data/raw/goodreads_books_mystery_thriller_crime.json.gz")
    reviews_file = Path("data/raw/goodreads_reviews_mystery_thriller_crime.json.gz")

    print("[1/5] Initializing lazy scan on raw gzip streams...")
    # Scan books metadata
    lazy_books = pl.scan_ndjson(books_file).select(
        [
            pl.col("book_id").cast(pl.Utf8),
            pl.col("title").fill_null("Unknown Title"),
            pl.col("description").fill_null(""),
        ]
    )

    # Scan reviews
    lazy_reviews = pl.scan_ndjson(reviews_file).select(
        [
            pl.col("review_id"),
            pl.col("book_id").cast(pl.Utf8),
            pl.col("rating").cast(pl.Int8),
            pl.col("review_text"),
        ]
    )

    print("[2/5] Cleaning review text and stripping spoiler tags...")
    cleaned_reviews = (
        lazy_reviews
        # 1. Remove spoiler tags and any inner text
        .with_columns(
            pl.col("review_text")
            .str.replace_all(r"(?is)<spoiler>.*?</spoiler>", " ")
            .str.replace_all(r"\s+", " ")
            .str.strip_chars()
            .alias("cleaned_text")
        )
        # 2. Compute word counts using whitespace split
        .with_columns(
            pl.col("cleaned_text")
            .str.split(" ")
            .list.len()
            .alias("word_count")
        )
        # 3. Filter minimum substantive review threshold
        .filter(pl.col("word_count") >= min_word_count)
    )

    print("[3/5] Joining reviews with book metadata...")
    joined = cleaned_reviews.join(lazy_books, on="book_id", how="inner")

    print(
        f"[4/5] Capping reviews at {max_reviews_per_book} per book to mitigate popularity bias..."
    )
    # Deduplicate / sample within each book group
    processed_corpus = (
        joined.with_columns(
            pl.col("review_id").cum_count().over("book_id").alias("review_rank")
        )
        .filter(pl.col("review_rank") <= max_reviews_per_book)
        .drop("review_rank")
    )

    print(f"[5/5] Executing computation and writing to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Stream query execution plan directly to Parquet
    processed_corpus.sink_parquet(output_path, compression="zstd")
    print("Preprocessing complete!")


if __name__ == "__main__":
    build_cleaned_corpus()