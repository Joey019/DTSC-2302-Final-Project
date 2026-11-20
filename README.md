# DTSC-2302 Final Project: Unsupervised NLP Book Recommender
Team Members: Fiorella, Johan, Ashutosh, Yoani, Hamza and Kameron

## Getting Started: Local Environment Setup
To ensure compatibility across both Windows and macOS/Linux environments, do not commit OS-specific `.venv` folders or massive datasets to this repository. Follow these steps to sync your local machine.

### 1. Clone the repository and navigate into it

```bash
git clone <your-github-repo-url>
cd DTSC-2302-Final-Project
```

### 2. Create a virtual environment (Python 3.12 recommended)

This project needs Python 3.10, 3.11, or 3.12. Python 3.13 or newer will NOT work, because our pinned numpy (<2.0) and torch (<2.5) versions don't support it, so `pip install` will fail.

Check your version first:

```bash
python3 --version   # Windows: py --version
```

If you're on 3.13+, install 3.12 from python.org (macOS can also use `brew install python@3.12`).

Windows:

```powershell
py -3.12 -m venv .venv
```

macOS / Linux:

```bash
python3.12 -m venv .venv
```

### 3. Activate the virtual environment

Windows:

```powershell
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 4. Install project dependencies

```bash
pip install -r requirements.txt
```

### 5. Select the .venv kernel in notebooks

When you open a `.ipynb` file, click **Select Kernel** (top right) and choose `.venv`. Otherwise you'll get `ModuleNotFoundError` even though everything is installed.

## ⚠️ CRITICAL: DO NOT COMMIT DATA TO GITHUB
The raw dataset is approximately 1.85 million rows. Committing `.json`, `.csv`, or `.gz` files will crash the repository. Our `.gitignore` is configured to block the `data/` folder.

To get the exact Mystery, Thriller, and Crime subset onto your local machine, run the automated `fetch_data.py` script. This script will build the `data/raw/` folder and stream the compressed files directly from the UCSD server.

```bash
python scripts/fetch_data.py
```

The script re-downloads both files every time it runs. Each new file is checked (size and gzip integrity) before it replaces your existing copy, so if a download fails, your old files are kept and the script prints a `FAILED` summary.

Note: The Polars pipeline is designed to read the `.json.gz` files directly. Do not unzip the files after downloading them.

## Data Pipeline

After downloading the data, one command prepares everything for clustering:

```bash
python scripts/pipeline.py
```

`pipeline.py` runs four scripts in order. You can also run any of them on its own.

Step 2 needs a small spaCy model (to find character names), once:

```bash
python -m spacy download en_core_web_sm
```

| Order | Script | What it does | Output (in `data/processed/`) |
|---|---|---|---|
| 1 | `clean_data.py` | Cleans the raw data: one row per book (editions merged), English books with a description, cleaned reviews | `cleaned_books.parquet`, `cleaned_reviews.parquet` |
| 2 | `embed_books.py` | Picks up to 10 meaningful reviews per book (`pick_reviews.py`), masks character and author names, and turns descriptions and reviews into embeddings | `embeddings/` |
| 3 | `reduce_umap.py` | Combines each book's embeddings into one vector (description 0.3, reviews 0.7) and shrinks it with UMAP, once per seed | `clustering_inputs/` |
| 4 | `genre_tags.py` | Sub-genre tags from readers' shelves (`subgenres.py`: 87 sub-genres), used only to score the clusters | `clustering_inputs/genre_tags.parquet` |

Then open `notebooks/clustering.ipynb`, select the `.venv` kernel and click **Run All** (about 1 h 45 min). Results are saved to `data/processed/clustering_results/`: every book's K-Means cluster (the main model) and HDBSCAN clusters, a description of each cluster, and the scores.

Charts of the data and the clusters (for the poster and report) are in [`visuals/`](visuals/README.md).

**Good to know**

- **It takes a while.** Step 2 can take about 6 hours on a laptop CPU (much faster with a GPU, which is used automatically). Steps 1, 3 and 4 take a few minutes each.
- **If step 2 stops** (laptop sleeps, you close it), run `python scripts/embed_books.py` again. It continues from where it stopped.
- **Quick test:** set `SAMPLE_BOOKS = 3000` at the top of `scripts/clean_data.py`, then run the pipeline and the notebook (about 30 minutes in total; with fewer books the notebook may find no usable HDBSCAN setting). Set it back to `None` for the real run.
- **Settings** (review limits, model, weights, UMAP) are in the `SETTINGS` block at the top of each script.
- **Running it again overwrites** the previous output.
- **Popularity is never used** to build the clusters: every book gets the same treatment, however many reviews or ratings it has. Popularity data (rating counts, average rating) is kept in the book table for the recommender.
- **Already set up before the pipeline existed?** Run `pip install -r requirements.txt` again to install the new packages.
