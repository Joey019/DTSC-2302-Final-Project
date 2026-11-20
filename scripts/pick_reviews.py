"""
pick_reviews.py - used by embed_books.py: pick up to REVIEWS_PER_BOOK *meaningful* reviews per book.

Same rule for every book (popularity-neutral, no votes):
  1. Length window: reviews of PREFERRED_MIN_WORDS..PREFERRED_MAX_WORDS words are used first;
     shorter/longer ones only fill up a book that has fewer than REVIEWS_PER_BOOK in the window.
  2. Star-rating rotation (unchanged): one review of each star rating the book has, then a second of each, ...
  3. Within a rating, the next review is the one with the best score:
        quality  = average of two within-book percentile ranks
                     content score:  share of a review's words that are NOT opinion filler
                     representative: word similarity to the book's other reviews
        score    = quality - DIVERSITY_WEIGHT * (highest similarity to a review already picked)

Opinion filler = words at least FILLER_RATIO times more common in reviews than in book descriptions
("loved", "recommend", "stars", "enjoyed", "ending"...), found from the data itself.
Only lowercase words are used, so names (capitalised) never count as content.
Books with REVIEWS_PER_BOOK or fewer usable reviews simply get all of them.
"""

import numpy as np
import polars as pl
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer, TfidfVectorizer

REVIEWS_PER_BOOK = 10
PREFERRED_MIN_WORDS = 30
PREFERRED_MAX_WORDS = 300
SKIP_UNRATED_REVIEWS = True
SEED = 42

FILLER_RATIO = 3.0           # word is "opinion filler" if this many times more common in reviews than descriptions
FILLER_MIN_SHARE = 0.002     # ...and in at least 0.2% of reviews
DIVERSITY_WEIGHT = 2.0       # how strongly picks should differ from the ones already picked
MAX_CANDIDATES = 150         # per book and length group, a repeatable random subset (keeps it fast)
FIT_SAMPLE = 200_000         # reviews used to learn the word lists and weights
WORDS = r"\b[a-z][a-z']{2,}\b"  # lowercase words of 3+ letters (capitalised words = mostly names, ignored)


def filler_words(reviews: list[str], descriptions: list[str]) -> list[str]:
    cv = CountVectorizer(token_pattern=WORDS, lowercase=False, stop_words=list(ENGLISH_STOP_WORDS),
                         min_df=20, binary=True)
    cv.fit(reviews + descriptions)
    in_reviews = np.asarray(cv.transform(reviews).mean(0)).ravel()
    in_descriptions = np.asarray(cv.transform(descriptions).mean(0)).ravel()
    ratio = (in_reviews + 1e-4) / (in_descriptions + 1e-4)
    keep = (ratio >= FILLER_RATIO) & (in_reviews >= FILLER_MIN_SHARE)
    return sorted(cv.get_feature_names_out()[keep])


def pick_reviews(reviews: pl.DataFrame, descriptions: list[str]) -> pl.DataFrame:
    """reviews: work_id, review_id, rating, word_count, cleaned_text. Returns the picked rows."""
    if SKIP_UNRATED_REVIEWS:
        reviews = reviews.filter(pl.col("rating") > 0)
    reviews = reviews.with_columns(
        pl.col("word_count").is_between(PREFERRED_MIN_WORDS, PREFERRED_MAX_WORDS).alias("good_length"),
        pl.col("review_id").hash(SEED).alias("random_order"),
    )
    n_usable = reviews.group_by("work_id").len()
    small = n_usable.filter(pl.col("len") <= REVIEWS_PER_BOOK)["work_id"]
    taken_all = reviews.filter(pl.col("work_id").is_in(small.implode()))  # nothing to choose
    rest = reviews.filter(~pl.col("work_id").is_in(small.implode()))
    # repeatable random subset per book and length group, to keep the scoring fast
    rest = (rest.with_columns(pl.col("random_order").rank("ordinal").over(["work_id", "good_length"]).alias("r"))
            .filter(pl.col("r") <= MAX_CANDIDATES).drop("r").sort(["work_id", "random_order"]))

    sample = reviews.sample(min(FIT_SAMPLE, reviews.height), seed=SEED)["cleaned_text"].to_list()
    filler = filler_words(sample, descriptions)
    stop = list(ENGLISH_STOP_WORDS | set(filler))
    tfidf = TfidfVectorizer(token_pattern=WORDS, lowercase=False, stop_words=stop, min_df=5,
                            sublinear_tf=True, dtype=np.float32).fit(sample)
    counter = CountVectorizer(token_pattern=WORDS, lowercase=False, stop_words=list(ENGLISH_STOP_WORDS))
    analyze = counter.build_analyzer()
    filler_set = set(filler)

    texts = rest["cleaned_text"].to_list()
    content = np.array([(lambda t: sum(w not in filler_set for w in t) / len(t) if t else 0.0)(analyze(x))
                        for x in texts], dtype=np.float32)
    V = tfidf.transform(texts)  # rows are already unit length
    work = rest["work_id"].to_numpy()
    good = rest["good_length"].to_numpy()
    rating = rest["rating"].to_numpy()
    starts = np.flatnonzero(np.r_[True, work[1:] != work[:-1]])
    ends = np.r_[starts[1:], len(work)]

    chosen = []
    for s, e in zip(starts, ends):
        picked = []
        for group in (True, False):  # length window first, then the rest if needed
            idx = np.arange(s, e)[good[s:e] == group]
            if len(idx) == 0 or len(picked) >= REVIEWS_PER_BOOK:
                continue
            Vg = V[idx]
            # similarity of each review to the sum of the book's OTHER reviews (vectors have length 1):
            #   v.(T - v) / |T - v|  =  (v.T - 1) / sqrt(|T|^2 - 2 v.T + 1)
            total = np.asarray(Vg.sum(0)).ravel()
            vt = Vg @ total
            rep = (vt - 1) / np.sqrt(np.maximum(total @ total - 2 * vt + 1, 1e-9)) if len(idx) > 1 else np.ones(1)
            rank = lambda x: (np.argsort(np.argsort(x)) + 1) / len(x)
            quality = (rank(content[idx]) + rank(rep)) / 2
            left = list(range(len(idx)))
            ratings = sorted(set(rating[idx]))
            while left and len(picked) < REVIEWS_PER_BOOK:
                for r in ratings:
                    options = [i for i in left if rating[idx[i]] == r]
                    if not options or len(picked) >= REVIEWS_PER_BOOK:
                        continue
                    if picked:
                        sim = (V[[idx[i] for i in options]] @ V[picked].T).max(axis=1).toarray().ravel()
                    else:
                        sim = np.zeros(len(options))
                    best = options[int(np.argmax(quality[options] - DIVERSITY_WEIGHT * sim))]
                    picked.append(idx[best])
                    left.remove(best)
        chosen.extend(picked)

    picked_rest = rest[chosen].with_columns(pl.Series("content_score", content[chosen]))
    return pl.concat([taken_all.with_columns(pl.lit(None, dtype=pl.Float32).alias("content_score")),
                      picked_rest], how="diagonal_relaxed").drop("good_length", "random_order").sort("work_id")
