# DTSC-2302 Final Project: Unsupervised NLP Book Recommender
Team Members: Fiorella, Johan, Ashutosh, Yoani, Hamza and Kameron

## Getting Started: Local Environment Setup
To ensure compatibility across both Windows and macOS/Linux environments, do not commit OS-specific .venv folders or massive datasets to this repository. Follow these steps to sync your local machine.

1. Clone the repository and navigate into it

Bash
git clone <your-github-repo-url>
cd DTSC-2302-Final-Project

2. Create a virtual environment (Python 3.12 recommended)

This project needs Python 3.10, 3.11, or 3.12. Python 3.13 or newer will NOT work, because our pinned numpy (<2.0) and torch (<2.5) versions don't support it, so pip install will fail.

Check your version first: python3 --version (Windows: py --version). If you're on 3.13+, install 3.12 from python.org (macOS can also use: brew install python@3.12).

Windows: py -3.12 -m venv .venv

macOS / Linux: python3.12 -m venv .venv

3. Activate the virtual environment

Windows: .venv\Scripts\activate

macOS / Linux: source .venv/bin/activate

4. Install project dependencies

5. Select the .venv kernel in notebooks

When you open a .ipynb file, click Select Kernel (top right) and choose .venv. Otherwise you'll get ModuleNotFoundError even though everything is installed.

Bash
pip install -r requirements.txt

## ⚠️ CRITICAL: DO NOT COMMIT DATA TO GITHUB
The raw dataset is approximately 1.85 million rows. Committing .json, .csv, or .gz files will crash the repository. Our .gitignore is configured to block the data/ folder.

To get the exact Mystery, Thriller, and Crime subset onto your local machine, run the automated fetch_data.py script. This script will build the data/raw/ folder and stream the compressed files directly from the UCSD server.

Bash
python scripts/fetch_data.py

Note: The Polars pipeline is designed to read the .json.gz files directly. Do not unzip the files after downloading them.