
# DTSC-2302 Final Project: Unsupervised NLP Book Recommender

Team Members: Fiorella, Johan, Ashutosh, Yoani, Hamza and Kameron

## Getting Started: Local Environment Setup

To ensure compatibility across Windows, macOS, and Linux, do not commit OS-specific virtual environments or massive datasets to this repository.

### 1. Clone the repository

```bash
git clone https://github.com/Joey019/DTSC-2302-Final-Project.git
cd DTSC-2302-Final-Project
```

### 2. Create a virtual environment

Python 3.12 is recommended.

The project supports Python 3.10, 3.11, and 3.12. Avoid Python 3.13 or newer because of compatibility with the pinned NumPy and PyTorch versions.

Windows:

```powershell
py -3.12 -m venv .venv
```

macOS/Linux:

```bash
python3.12 -m venv .venv
```

### 3. Activate the virtual environment

Windows:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 4. Install project dependencies

```bash
pip install -r requirements.txt
```

### 5. Select the virtual environment in Jupyter

When opening a `.ipynb` notebook, select the `.venv` kernel to avoid missing-package errors.

## ⚠️ CRITICAL: DO NOT COMMIT DATA TO GITHUB

The raw dataset contains approximately 1.85 million rows.

Do not commit large `.json`, `.csv`, or `.gz` datasets.

The `.gitignore` is configured to exclude the `data/` directory.

To download the Mystery, Thriller, and Crime dataset, run:

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

---

## 📖 Plotwist — Book Recommendation Website

Plotwist is an interactive book recommendation website developed using Python and Streamlit for our Goodreads Mystery, Thriller, and Crime Recommendation System project.

The website allows users to explore featured books, search for books they enjoyed, and discover similar titles.

### How to Access the Website

First, complete the environment setup instructions above.

Then launch the Streamlit application from the project folder:

```bash
python -m streamlit run app.py
```

Open your browser and visit:

http://localhost:8501

The website should open automatically when Streamlit starts.

### Website Features

- Modern dark navy and gold interface
- Featured mystery, thriller, and crime books
- Book selection and recommendation cards
- Book covers and expandable details
- Personal reading list with save and remove functionality
- Shopping links to book retailers
- Interactive buttons and hover effects
- Save and remove notifications
- Recommendation loading indicator
- Welcome section and website footer

### Current Development Status

The Plotwist interface currently uses sample book recommendations for testing.

Integration with the group's Goodreads recommendation model is still in progress.

Once integrated, the website will display recommendations generated from the team's processed book dataset.
