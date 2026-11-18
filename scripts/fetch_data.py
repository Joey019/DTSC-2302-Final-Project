import requests
from pathlib import Path

DATASETS = {
    "goodreads_books_mystery_thriller_crime.json.gz": "https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/byGenre/goodreads_books_mystery_thriller_crime.json.gz",
    "goodreads_reviews_mystery_thriller_crime.json.gz": "https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/byGenre/goodreads_reviews_mystery_thriller_crime.json.gz"
}

def download_datasets():
    raw_dir = Path("data") / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0'}

    for filename, url in DATASETS.items():
        file_path = raw_dir / filename
        if file_path.exists():
            print(f"{filename} already exists.")
            continue
            
        print(f"⬇ Downloading {filename}...")
        try:
            with requests.get(url, stream=True, headers=headers) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"✅ Successfully downloaded {filename}!")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    download_datasets()