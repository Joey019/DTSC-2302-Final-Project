# Visuals for the poster and final report

Charts about the data and the clustering model, made from the full run on all 72,473 books (K-Means k = 41
as the main model). Every chart is saved twice:

- `png/<name>.png`: 300 dpi, ready to print or paste into the report.
- `svg/<name>.svg`: vector version, scales to any poster size and can be edited (e.g. in Illustrator, Inkscape or PowerPoint).

**Colours** are a colour-blind-safe palette. In charts about clusters, they show what kind of cluster it is:
**blue** = setting/premise clusters (a place, era, profession or situation), **orange** = mood or format
clusters, **aqua** = broad categories. Cluster names were written by hand from each cluster's top sub-genre
tags, top words and best-known books.

What the scores mean (purity lift, premise lift, c-TF-IDF lift, ARI) is explained at the top of
[`notebooks/clustering.ipynb`](../notebooks/clustering.ipynb).

## Suggested poster set

| Chart | Why |
|---|---|
| 09 Book map | The main image: every book on one map, labelled with cluster names. |
| 20 Cluster cards | Makes the clusters concrete: top words and well-known books. |
| 08 Cluster sizes | All 41 clusters at a glance; 58% of books are in setting/premise clusters. |
| 02 Reviews per book | Most books have only a handful of reviews, the challenge the method has to handle. |
| 03 Popularity skew | Why popularity is kept out of the clustering. |
| 12 Combining gains | What tuning the way vectors are combined bought. |
| 15 Rating by cluster | An interesting result for the recommender. |

The rest fit better in the final report.

## All charts

### The data

| # | Chart | What it shows | Takeaway |
|---|---|---|---|
| 01 | [Data funnel](png/01_data_funnel.png) | From the raw Goodreads mystery/thriller/crime data to the clustering input: 219,235 editions → 89,869 books → 72,473 books; 1.85M → 1.41M reviews after cleaning → 393K picked reviews. | Merging editions and keeping only books with an English description shapes the dataset. |
| 02 | [Reviews per book](png/02_reviews_per_book.png) | How many usable reviews each book has. | Median 5; 32% of books have 2 or fewer, 32% have 10 or more. Every book uses at most 10, so popular books don't get extra weight. |
| 03 | [Popularity skew](png/03_popularity_skew.png) | Ratings per book, and the share of all ratings held by the most-rated books. | The top 1% of books hold 50% of all ratings, the top 10% hold 85%. Clustering on popularity would just separate bestsellers from the rest. |
| 04 | [Review length](png/04_review_length.png) | Words per review. | Median 79 words; 72% of reviews are 30–300 words, the length range picked first. |
| 05 | [Star ratings](png/05_star_ratings.png) | Star ratings of all reviews vs the picked reviews. | Rotating through star ratings gives critical (1–2★) reviews a little more voice (15% vs 11%). |
| 06 | [Publication year](png/06_publication_year.png) | Publication year of the editions in the data. | Mostly editions from the 2000s. Caveat: this is the year of the edition, not of first publication, so reprinted classics look recent. |
| 07 | [Sub-genre tags](png/07_subgenre_tags.png) | The 30 most common of the 87 sub-genre tags taken from readers' shelves. | The tags used to check and name the clusters (never to build them). |

### The model

| # | Chart | What it shows | Takeaway |
|---|---|---|---|
| 08 | [Cluster sizes](png/08_cluster_sizes.png) | All 41 K-Means clusters by size, coloured by kind. | No catch-all cluster (the largest holds about 5% of books); 58% of books are in setting/premise clusters. |
| 09 | [Book map](png/09_book_map.png) | All 72,473 books on a 2-D map (UMAP), coloured by cluster and labelled with cluster names. | Similar books sit together; related clusters are neighbours. For looking only: the model clusters in 15 dimensions, not on this map. |
| 10 | [Cluster × tag heatmap](png/10_cluster_tag_heatmap.png) | For each cluster, the share of its books carrying each sub-genre tag. | A near-diagonal pattern: most clusters match one reader sub-genre, found without using the tags. |
| 11 | [Choosing k](png/11_choosing_k.png) | Purity lift, premise lift and c-TF-IDF lift for k = 15–50, with the spread across 3 UMAP seeds. | Purity and premise lift rise with k, c-TF-IDF lift falls; k = 41 is the most stable of the settings tied for best. |
| 12 | [Combining gains](png/12_combining_gains.png) | Purity lift and the share of books in clearly named clusters for three ways of combining description and review vectors. | Centering plus less trust in books with few reviews: purity lift 0.234 → 0.267, books in named clusters 60% → 68%. |
| 13 | [Fit by number of reviews](png/13_fit_by_reviews.png) | Share of books carrying their cluster's main sub-genre tag, by number of reviews. | 44% for books with 0 reviews, 70% with 10 (chance is about 9%). Reviews help, but description-only books are still placed far better than chance. |
| 14 | [Fit by popularity](png/14_fit_by_popularity.png) | The same share, by popularity fifth. | 49% for the least-rated fifth, 71% for the most-rated. Little-known books are clustered meaningfully too. |
| 15 | [Rating by cluster](png/15_rating_by_cluster.png) | Average rating of the books in each cluster. | Paranormal and romance clusters rate highest, dark literary bestsellers lowest. Ratings were never used to build the clusters. |
| 16 | [Edition year by cluster](png/16_year_by_cluster.png) | Publication year of the editions in each cluster. | Same caveat as chart 06 (edition year, not first publication). |
| 17 | [Niche clusters](png/17_niche_clusters.png) | The 30 largest clusters found by natural HDBSCAN. | Very specific groups (e.g. cozy island mysteries, legal thrillers set in Florida, LGBTQ romantic suspense) that can add a niche label on top of the K-Means cluster. |
| 18 | [Series stay together](png/18_series_together.png) | Share of a series' books that land in that series' main cluster. | 69% vs 23% for random clusters, even though character names are masked. |
| 19 | [Seed stability](png/19_seed_stability.png) | Agreement between UMAP seeds (ARI) for each k. | Clusters are mostly the same across seeds: 0.83 at k = 41. |
| 20 | [Cluster cards](png/20_cluster_cards.png) | 8 example clusters with their top words and best-known books. | What the clusters look like from a reader's point of view. |
