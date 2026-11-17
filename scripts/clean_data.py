"""
clean_data.py - Step 1 of the pipeline: clean the raw Goodreads data.

    python scripts/clean_data.py

Input:   data/raw/  (downloaded by fetch_data.py)
Output:  data/processed/cleaned_books.parquet    one row per book, with an English description
         data/processed/cleaned_reviews.parquet  cleaned English reviews of those books

What it does
  Books
    1. Load every edition of every book.
    2. Clean the descriptions: remove HTML, quoted blurbs, and short marketing sentences.
    3. Detect the language of each description from its text.
    4. Merge the editions of the same book (they share a "work_id") into one row.
  Reviews
    5. Load the reviews of those books (from every edition).
    6. Clean the text: remove spoilers, HTML, links, and "free copy for an honest review" lines.
    7. Drop reviews that are too short.
    8. Keep only English reviews.
    9. Remove duplicates.
"""

import re
from pathlib import Path

import polars as pl
from lingua import LanguageDetectorBuilder

# =============================================================================
# SETTINGS
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]  # the project folder
RAW_BOOKS = ROOT / "data" / "raw" / "goodreads_books_mystery_thriller_crime.json.gz"
RAW_REVIEWS = ROOT / "data" / "raw" / "goodreads_reviews_mystery_thriller_crime.json.gz"
OUTPUT_DIR = ROOT / "data" / "processed"

MIN_DESCRIPTION_CHARS = 100  # shorter descriptions count as missing
MIN_REVIEW_WORDS = 15        # shorter reviews are dropped
# Editions with one of these language codes, or no code at all, get their language checked.
# Editions with any other code (e.g. "spa", "ger") are treated as not English.
ENGLISH_CODES = ["eng", "en-US", "en-GB", "en-CA"]
SAMPLE_BOOKS = None          # e.g. 300 for a quick test run; None = all books

# Review sentences that contain any of these are removed (not case-sensitive).
REVIEW_BOILERPLATE = [
    r"in exchange for (?:an?|my) (?:honest|unbiased|fair|candid)",  # "...for an honest review"
    r"\b(?:netgalley|net galley|edelweiss|first ?reads|goodreads giveaway|librarything|bookish first)\b",
    r"\b(?:advanced? (?:readers?'?s?|review|reading) copy|review copy|galley)\b",
    r"\b(?:received|was given|was provided|got|won) (?:a |an |this |my )?(?:free |complimentary |digital |e-?)?(?:copy|arc|e-?arc|galley)\b",
    r"\b(?:my blog|full review (?:is )?(?:at|on|can be found)|(?:this|my) review (?:was )?(?:originally )?(?:posted|published|appears))\b",
]
# Short description sentences that contain any of these are removed (not case-sensitive).
DESCRIPTION_MARKETING = [
    r"best[- ]?sell",                                                     # "bestselling author"
    r"new york times|usa today|wall street journal|sunday times|publishers weekly|kirkus|booklist|library journal|starred review",
    r"#1\b|number one",
    r"award[- ]winning|winner of the .{0,40}(?:award|prize)|(?:shortlisted|longlisted|nominated|finalist) for",
    r"\b(?:edgar|agatha|anthony|macavity|dagger|shamus|barry|thriller) awards?\b",
    r"praise for|now a major|soon to be a major|major motion picture|(?:netflix|hbo|bbc|tv) (?:series|adaptation)",
    r"from the (?:author|creator|bestselling|acclaimed|award)",
    r"million copies|copies sold|international (?:sensation|phenomenon)|published in \d+ (?:countries|languages)",
    r"(?:perfect )?for fans of|will love this|don't miss",
]

# Sub-genre labels, taken from the shelves readers put a book on. Used only to EVALUATE the
# clusters later (genre purity), never to build them. Broad shelves such as "mystery" or
# "thriller" are left out on purpose: almost every book has them.
GENRE_PATTERNS = {
    "cozy": r"cozy|cozies",
    "psychological": r"psychological",
    "police_procedural": r"police|procedural",
    "historical": r"historical",
    "romantic_suspense": r"romance|romantic",
    "horror_supernatural": r"horror|paranormal|supernatural|ghost",
    "espionage_action": r"espionage|spy|spies|military|political-thriller|action",
    "legal": r"legal",
    "noir_hardboiled": r"noir|hard-?boiled|pulp",
    "true_crime": r"true-crime",
    "young_adult": r"young-adult|^ya$|teen|middle-grade|juvenile|children",
    "classics": r"^classics?$|golden-age",
    "scifi_fantasy": r"fantasy|sci-fi|science-fiction|dystopi",
    "humor": r"humou?r|funny|comedy",
}


# =============================================================================
# TEXT CLEANING
# =============================================================================
def remove_html(text: pl.Expr) -> pl.Expr:
    return (
        text.str.replace_all(r"(?i)<br\s*/?>", " ")
        .str.replace_all(r"<[^>]{1,200}>", " ")
        .str.replace_all("&amp;", "&", literal=True)
        .str.replace_all("&quot;", '"', literal=True)
        .str.replace_all("&#39;", "'", literal=True)
        .str.replace_all("&lt;", "<", literal=True)
        .str.replace_all("&gt;", ">", literal=True)
        .str.replace_all("&nbsp;", " ", literal=True)
    )


def tidy_spaces(text: pl.Expr) -> pl.Expr:
    return (
        text.str.replace_all(r"\s+", " ")
        .str.replace_all(r"([.!?])(?:\s*\.)+", "${1}")  # ". ." left over from removed sentences
        .str.replace_all(r"^[\s.!?,;:]+", "")
        .str.strip_chars()
    )


def clean_review(text: pl.Expr) -> pl.Expr:
    text = text.fill_null("")
    # Spoilers come in two formats on Goodreads; remove both, including the hidden text.
    text = text.str.replace_all(r"(?is)<spoiler>.*?</spoiler>", " ")
    text = text.str.replace_all(r"(?is)\(view spoiler\)\[.*?\(hide spoiler\)\]", " ")
    text = text.str.replace_all(r"(?i)\((?:view|hide) spoiler\)", " ")
    text = remove_html(text)
    text = text.str.replace_all(r"https?://\S+|www\.\S+", " ")  # links
    # Whole sentences containing boilerplate phrases.
    text = text.str.replace_all(r"(?i)[^.!?\n]*(?:" + "|".join(REVIEW_BOILERPLATE) + r")[^.!?\n]*[.!?]*", " ")
    # Sentences mentioning an "ARC" (advance copy). Upper case only, so "story arc" is kept.
    text = text.str.replace_all(r"[^.!?\n]*\be?ARCs?\b[^.!?\n]*[.!?]*", " ")
    text = text.str.replace_all(r"(?i)\bDNF(?:'?d|ed)?\b(?:\s*(?:at|@)\s*(?:page\s*)?\d+\s*%?)?", " ")  # "DNF at 30%"
    return tidy_spaces(text)


def clean_description(text: pl.Expr) -> pl.Expr:
    text = remove_html(text.fill_null(""))
    # Quoted blurbs with a source, e.g.  "Gripping!" -- The Washington Post
    text = text.str.replace_all(r"[\"“][^\"”]{5,400}[\"”]\s*[—–-]{1,2}\s*[A-Z][^.!?\n]{0,80}", " ")
    # Short sentences (up to ~200 characters) with marketing phrases. Long sentences are kept,
    # because they usually describe the plot too ("...in this thriller from the bestselling author").
    # The sentence start (group 1) is matched and put back. Run twice to catch back-to-back sentences.
    short_marketing = (r"(?i)(^|[.!?\n]\s*)[^.!?\n]{0,100}(?:" + "|".join(DESCRIPTION_MARKETING)
                       + r")[^.!?\n]{0,100}(?:[.!?]+|\n|$)")
    text = text.str.replace_all(short_marketing, "${1}").str.replace_all(short_marketing, "${1}")
    return tidy_spaces(text)


def genre_from_shelves(shelves) -> str:
    """The sub-genre whose shelves got the most votes, or 'general' if none match."""
    votes = dict.fromkeys(GENRE_PATTERNS, 0)
    for shelf in shelves or []:
        for genre, pattern in GENRE_PATTERNS.items():
            if re.search(pattern, shelf["name"]):
                votes[genre] += int(shelf["count"] or 0)
    best = max(votes, key=lambda g: votes[g])
    return best if votes[best] > 0 else "general"


def detect_language(texts: list[str]) -> list[str]:
    """Two-letter language code for each text ("en", "es", ...), based on its first 500 characters."""
    detector = LanguageDetectorBuilder.from_all_languages().with_preloaded_language_models().build()
    codes = []
    for start in range(0, len(texts), 200_000):  # in batches, to limit memory use
        batch = [t[:500] for t in texts[start : start + 200_000]]
        for language in detector.detect_languages_in_parallel_of(batch):
            codes.append(language.iso_code_639_1.name.lower() if language else "unknown")
    return codes


# =============================================================================
# BOOKS
# =============================================================================
def build_books() -> tuple[pl.DataFrame, pl.DataFrame]:
    print("[1/9] Loading book editions...")
    editions = (
        pl.scan_ndjson(RAW_BOOKS, infer_schema_length=10_000)
        .select(
            pl.col("book_id").cast(pl.Utf8),
            pl.col("work_id").cast(pl.Utf8),
            "title",
            pl.col("description").alias("description_raw"),
            pl.col("language_code").fill_null(""),
            pl.col("ratings_count").cast(pl.Int64, strict=False).fill_null(0),
            pl.col("text_reviews_count").cast(pl.Int64, strict=False).fill_null(0),
            pl.col("average_rating").cast(pl.Float64, strict=False),
            pl.col("publication_year").cast(pl.Int32, strict=False),
            pl.col("num_pages").cast(pl.Int32, strict=False),
            "authors", "popular_shelves",
        )
        .collect()
    )
    # An edition without a work_id is treated as its own book.
    editions = editions.with_columns(
        pl.when(pl.col("work_id").fill_null("") == "").then("b" + pl.col("book_id"))
        .otherwise(pl.col("work_id")).alias("work_id")
    )
    print(f"      {editions.height:,} editions of {editions['work_id'].n_unique():,} books")

    print("[2/9] Cleaning descriptions...")
    editions = editions.with_columns(clean_description(pl.col("description_raw")).alias("description"))

    print("[3/9] Detecting the language of each description...")
    to_check = editions.filter(
        (pl.col("description").str.len_chars() >= MIN_DESCRIPTION_CHARS)
        & (pl.col("language_code").is_in(ENGLISH_CODES) | (pl.col("language_code") == ""))
    )
    to_check = to_check.with_columns(pl.Series("language", detect_language(to_check["description"].to_list())))
    english_ids = to_check.filter(pl.col("language") == "en")["book_id"]
    editions = editions.with_columns(pl.col("book_id").is_in(english_ids.implode()).alias("is_english"))
    print(f"      {len(english_ids):,} editions have an English description")

    print("[4/9] Merging editions into one row per book...")
    # Popularity numbers are added up over all editions. They are kept for the recommender,
    # NOT used for clustering.
    popularity = editions.group_by("work_id").agg(
        pl.len().alias("n_editions"),
        pl.col("ratings_count").sum(),
        pl.col("text_reviews_count").sum(),
        ((pl.col("average_rating") * pl.col("ratings_count")).sum() / pl.col("ratings_count").sum()).alias("average_rating"),
    )
    # For everything else, use the English edition with the most ratings.
    books = (
        editions.filter(pl.col("is_english"))
        .sort(["ratings_count", pl.col("description").str.len_chars()], descending=True)
        .unique(subset="work_id", keep="first", maintain_order=True)
    )
    if SAMPLE_BOOKS:
        books = books.head(SAMPLE_BOOKS)  # the most-rated books, for a quick test
    first_author = pl.col("authors").list.first().struct.field("author_id")
    books = (
        books.select("work_id", "book_id", "title", "description", first_author.alias("author_id"),
                     "publication_year", "num_pages", "popular_shelves")
        .join(popularity, on="work_id")
    )
    books = books.with_columns(
        pl.Series("genre_label", [genre_from_shelves(s) for s in books["popular_shelves"].to_list()])
    ).drop("popular_shelves")
    print(f"      {books.height:,} books kept")
    return books, editions.select("book_id", "work_id")


# =============================================================================
# REVIEWS
# =============================================================================
def build_reviews(books: pl.DataFrame, editions: pl.DataFrame) -> pl.DataFrame:
    print("[5/9] Loading the reviews of those books (all editions)...")
    edition_to_book = editions.filter(pl.col("work_id").is_in(books["work_id"].implode()))
    reviews = (
        pl.scan_ndjson(RAW_REVIEWS)
        .select("review_id", pl.col("book_id").cast(pl.Utf8), "user_id", pl.col("rating").cast(pl.Int8),
                "review_text", "n_votes", "date_added")
        .join(edition_to_book.lazy(), on="book_id")
    )

    print("[6/9] Cleaning review text...")
    reviews = reviews.with_columns(clean_review(pl.col("review_text")).alias("cleaned_text")).drop("review_text")
    reviews = reviews.with_columns(pl.col("cleaned_text").str.split(" ").list.len().alias("word_count"))

    print(f"[7/9] Dropping reviews under {MIN_REVIEW_WORDS} words...")
    reviews = reviews.filter(pl.col("word_count") >= MIN_REVIEW_WORDS).collect()
    print(f"      {reviews.height:,} reviews left")

    print("[8/9] Keeping English reviews...")
    reviews = reviews.with_columns(pl.Series("language", detect_language(reviews["cleaned_text"].to_list())))
    reviews = reviews.filter(pl.col("language") == "en")
    print(f"      {reviews.height:,} reviews left")

    print("[9/9] Removing duplicate reviews...")
    reviews = (
        reviews.sort("word_count", descending=True)
        .unique(subset=["user_id", "work_id"], keep="first")        # same person, several editions
        .unique(subset=["work_id", "cleaned_text"], keep="first")  # copy-pasted text
        .sort(["work_id", "review_id"])
    )
    print(f"      {reviews.height:,} reviews left")
    return reviews.join(books.select("work_id", "title"), on="work_id", how="left")


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    books, editions = build_books()
    reviews = build_reviews(books, editions)

    # How many usable reviews each book has (some have none; they are still kept).
    review_counts = reviews.group_by("work_id").len().rename({"len": "n_reviews_available"})
    books = (
        books.join(review_counts, on="work_id", how="left")
        .with_columns(pl.col("n_reviews_available").fill_null(0))
        .sort("work_id")
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    books.write_parquet(OUTPUT_DIR / "cleaned_books.parquet")
    reviews.write_parquet(OUTPUT_DIR / "cleaned_reviews.parquet")

    print(f"\nSaved {books.height:,} books and {reviews.height:,} reviews to {OUTPUT_DIR}")
    print(f"Books with no usable reviews: {(books['n_reviews_available'] == 0).sum():,}")
    print("Sub-genre labels:")
    for genre, n in books.group_by("genre_label").len().sort("len", descending=True).iter_rows():
        print(f"  {genre:<22} {n:>7,}  ({n / books.height:.1%})")


if __name__ == "__main__":
    main()
