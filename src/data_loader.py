import gzip
import json
from typing import Dict, Generator, List, Set
import pandas as pd


def stream_books_metadata(
    books_archive_path: str,
    target_languages: Set[str] = {"eng", "en-US", "en-GB"}
) -> Dict[str, dict]:
    """
    Streams the raw books metadata archive and filters for English editions.
    """
    valid_books = {}
    with gzip.open(books_archive_path, "rt", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            lang = item.get("language_code", "")
            
            if lang in target_languages and item.get("description"):
                b_id = item.get("book_id")
                valid_books[b_id] = {
                    "book_id": b_id,
                    "title": item.get("title"),
                    "publication_year": item.get("publication_year"),
                    "average_rating": item.get("average_rating"),
                    "description": item.get("description"),
                }
    return valid_books


def stream_and_filter_reviews(
    reviews_archive_path: str,
    valid_book_ids: Set[str],
    min_char_len: int = 75,
    max_reviews: int = 50000
) -> pd.DataFrame:
    """
    Streams deduplicated reviews, matching against valid books and applying length thresholds.
    """
    retained_reviews: List[dict] = []
    
    with gzip.open(reviews_archive_path, "rt", encoding="utf-8") as f:
        for line in f:
            rev = json.loads(line)
            b_id = rev.get("book_id")
            
            if b_id in valid_book_ids:
                text = rev.get("review_text", "").strip()
                if len(text) >= min_char_len:
                    retained_reviews.append({
                        "review_id": rev.get("review_id"),
                        "book_id": b_id,
                        "user_id": rev.get("user_id"),
                        "rating": rev.get("rating"),
                        "review_text": text,
                        "n_votes": rev.get("n_votes", 0)
                    })
                    
            if len(retained_reviews) >= max_reviews:
                break
                
    return pd.DataFrame(retained_reviews)