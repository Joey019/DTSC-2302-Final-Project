
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

This creates the `data/raw/` directory and downloads compressed files from the UCSD server.

The Polars pipeline reads `.json.gz` files directly. Do not unzip them.

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
