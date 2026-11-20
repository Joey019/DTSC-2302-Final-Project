"""
genre_tags.py - Step 4 of the pipeline: sub-genre tags for every book, used to SCORE the clusters.

    python scripts/genre_tags.py

Input:   data/processed/clustering_inputs/books.parquet  (from reduce_umap.py)
         data/raw/goodreads_books_mystery_thriller_crime.json.gz  (the shelves readers put each book on)
Output:  data/processed/clustering_inputs/genre_tags.parquet, one row per book (same order as books.parquet):
           book_id
           tags           every sub-genre the book carries (a book can have several: "british", "victorian", "cozy")
           primary_genre  the book's most DISTINCTIVE tag (its share of the book's shelf votes x how rare the tag
                          is overall), or "general" if it has none
           <one column per sub-genre>  share of the book's shelf votes that went to that sub-genre

A book carries a tag when at least MIN_VOTES readers used a matching shelf (see subgenres.py) AND those votes
are at least MIN_SHARE of all its shelf votes (shelves like "to-read" or "kindle" don't count).
The tags are never used to build the clusters, only to check them: readers' shelves are an independent
opinion of what each book is about. Takes about a minute.
"""

from pathlib import Path

import numpy as np
import polars as pl

from subgenres import SUBGENRES, match_shelf

# =============================================================================
# SETTINGS
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]  # the project folder
RAW_BOOKS = ROOT / "data" / "raw" / "goodreads_books_mystery_thriller_crime.json.gz"
DATA_DIR = ROOT / "data" / "processed" / "clustering_inputs"

MIN_VOTES = 2
MIN_SHARE = 0.01
# Shelves about reading status / ownership / format, not content: left out of the total.
STATUS_SHELVES = (r"to-?read|currently|^read|-read$|reading|default|own|kindle|e-?books?|nook|kobo|library|wish|"
                  r"favou?rite|tbr|buy|purchase|audio|audible|^books?$|\d{4}|dnf|did-not-finish|finish|abandon|"
                  r"giveaway|netgalley|arc|review|stars?$|series|maybe|want|have|shelf|unread|free|borrowed|calibre")


def build(books: pl.DataFrame) -> pl.DataFrame:
    edition_ids = books["edition_book_id"].cast(pl.Utf8)
    raw = (
        pl.scan_ndjson(RAW_BOOKS, infer_schema_length=10_000)
        .select("book_id", "popular_shelves")
        .filter(pl.col("book_id").is_in(edition_ids.implode()))
        .collect()
    )
    shelves = (
        raw.explode("popular_shelves").unnest("popular_shelves")
        .with_columns(pl.col("count").cast(pl.Int64, strict=False).fill_null(0), pl.col("name").str.to_lowercase())
    )
    names = shelves["name"].unique().to_list()
    shelf_map = pl.DataFrame([(n, g) for n in names for g in match_shelf(n)], schema=["name", "genre"], orient="row")
    total = (shelves.filter(~pl.col("name").str.contains(STATUS_SHELVES))
             .group_by("book_id").agg(pl.col("count").sum().alias("total")))
    votes = (
        shelves.join(shelf_map, on="name")
        .group_by("book_id", "genre").agg(pl.col("count").sum().alias("votes"))
        .join(total, on="book_id")
        .with_columns((pl.col("votes") / pl.col("total")).alias("share"))
        .with_columns(((pl.col("votes") >= MIN_VOTES) & (pl.col("share") >= MIN_SHARE)).alias("tagged"))
    )
    # How rare each tag is: rarer tags say more about a book ("victorian" vs "romance").
    n_books = books.height
    tag_books = votes.filter("tagged").group_by("genre").len()
    idf = tag_books.with_columns(np.log(n_books / pl.col("len")).alias("idf")).select("genre", "idf")
    tagged = votes.filter("tagged").join(idf, on="genre").with_columns((pl.col("share") * pl.col("idf")).alias("weight"))
    per_book = tagged.sort("weight", descending=True).group_by("book_id", maintain_order=True).agg(
        pl.col("genre").first().alias("primary_genre"), pl.col("genre").sort().alias("tags"))
    shares = votes.pivot(on="genre", index="book_id", values="share")
    for g in SUBGENRES:
        if g not in shares.columns:
            shares = shares.with_columns(pl.lit(0.0).alias(g))
    out = (
        books.select("book_id", pl.col("edition_book_id").cast(pl.Utf8).alias("edition"))
        .join(per_book.rename({"book_id": "edition"}), on="edition", how="left")
        .join(shares.rename({"book_id": "edition"}), on="edition", how="left")
        .with_columns(pl.col("primary_genre").fill_null("general"), pl.col("tags").fill_null([]),
                      *[pl.col(g).fill_null(0.0) for g in SUBGENRES])
        .select("book_id", "tags", "primary_genre", *SUBGENRES)
    )
    assert out["book_id"].to_list() == books["book_id"].to_list()
    return out


def main() -> None:
    books = pl.read_parquet(DATA_DIR / "books.parquet", columns=["book_id", "edition_book_id"])
    out = build(books)
    out.write_parquet(DATA_DIR / "genre_tags.parquet")
    n_tags = out["tags"].list.len()
    print(f"{out.height:,} books; with at least one tag: {(n_tags > 0).mean():.1%}; "
          f"median tags per book: {n_tags.median():.0f}; no tag ('general'): {(out['primary_genre'] == 'general').mean():.1%}")
    print(f"Saved {DATA_DIR / 'genre_tags.parquet'}")


if __name__ == "__main__":
    main()
