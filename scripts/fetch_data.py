"""
Downloads the Goodreads Mystery/Thriller/Crime datasets into data/raw/.

Every run re-downloads both files from scratch:
  1. The new copy is streamed to <name>.part. Any existing copy is left untouched.
  2. It is checked: byte count must match the server's Content-Length, and the
     gzip stream must decompress cleanly end to end.
  3. Only then does it replace the existing file (a single rename).

So a file in data/raw/ without a .part suffix is always a complete, verified
download, and a failed run never loses the previous good copy. If anything fails
(network drop, timeout, truncated or corrupt file, full disk, Ctrl+C) the .part
file is removed, the reason is printed, retries are attempted, and the script
ends with a FAILED summary and exit code 1.

Run from the repo root:
    python scripts/fetch_data.py
"""

import gzip
import shutil
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm

DATASETS = {
    "goodreads_books_mystery_thriller_crime.json.gz": "https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/byGenre/goodreads_books_mystery_thriller_crime.json.gz",
    "goodreads_reviews_mystery_thriller_crime.json.gz": "https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/byGenre/goodreads_reviews_mystery_thriller_crime.json.gz",
}
RAW_DIR = Path("data") / "raw"

MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 10  # doubled after each failed attempt
TIMEOUT = (15, 60)  # (connect, read) seconds; read = max silence between chunks
CHUNK_SIZE = 1024 * 1024  # 1 MB
HEADERS = {"User-Agent": "Mozilla/5.0"}


class DownloadError(Exception):
    """A download or verification step failed."""


def _remove(path: Path) -> None:
    if path.exists():
        path.unlink()


def _download_once(url: str, part_path: Path) -> int:
    """Stream url to part_path. Returns bytes written; raises DownloadError on any problem."""
    try:
        with requests.get(url, stream=True, headers=HEADERS, timeout=TIMEOUT) as r:
            r.raise_for_status()
            expected = r.headers.get("Content-Length")
            expected = int(expected) if expected is not None else None

            if expected is not None:
                free = shutil.disk_usage(part_path.parent).free
                if free < expected * 1.05:
                    raise DownloadError(
                        f"not enough disk space: need {expected / 1e6:,.0f} MB, "
                        f"have {free / 1e6:,.0f} MB free"
                    )

            written = 0
            with open(part_path, "wb") as f, tqdm(
                total=expected, unit="B", unit_scale=True, desc=part_path.stem, leave=False
            ) as bar:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
                    written += len(chunk)
                    bar.update(len(chunk))
    except requests.RequestException as e:
        raise DownloadError(f"network error: {e}") from e
    except OSError as e:
        raise DownloadError(f"could not write file: {e}") from e

    if expected is None:
        print("  (server sent no Content-Length; relying on the gzip check alone)")
    elif written != expected:
        raise DownloadError(
            f"incomplete download: got {written:,} of {expected:,} bytes "
            f"({written / expected:.1%}). The connection likely dropped partway."
        )
    return written


def _verify_gzip(path: Path) -> None:
    """Decompress the whole file once to prove it is a complete, uncorrupted gzip stream."""
    try:
        with gzip.open(path, "rb") as f:
            while f.read(CHUNK_SIZE * 8):
                pass
    except (OSError, EOFError) as e:
        raise DownloadError(f"file is corrupt or truncated (gzip check failed: {e})") from e


def download_file(filename: str, url: str, raw_dir: Path = RAW_DIR) -> None:
    final_path = raw_dir / filename
    part_path = raw_dir / (filename + ".part")

    # The existing copy (if any) is left alone until the new download is verified;
    # replace() below swaps it out in one step, so a failure never loses the old file.
    if final_path.exists():
        print(f"Existing {filename} found; it will be replaced only if the new download succeeds.")
    _remove(part_path)  # leftover from an earlier crashed run

    wait = RETRY_WAIT_SECONDS
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"Downloading {filename} (attempt {attempt}/{MAX_ATTEMPTS}) ...")
        try:
            size = _download_once(url, part_path)
            print("  Verifying gzip integrity ...")
            _verify_gzip(part_path)
            part_path.replace(final_path)
            print(f"  OK: {filename} ({size / 1e6:,.0f} MB)")
            return
        except DownloadError as e:
            _remove(part_path)
            last_error = e
            print(f"  Attempt {attempt} failed: {e}")
            if attempt < MAX_ATTEMPTS:
                print(f"  Retrying in {wait}s ...")
                time.sleep(wait)
                wait *= 2
        except BaseException:
            # Ctrl+C or an unexpected crash: never leave a partial file behind.
            _remove(part_path)
            raise

    raise DownloadError(f"all {MAX_ATTEMPTS} attempts failed. Last error: {last_error}")


def download_datasets(datasets: dict = DATASETS, raw_dir: Path = RAW_DIR) -> bool:
    """Download every dataset. Returns True only if all of them succeeded."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    failed = {}
    for filename, url in datasets.items():
        try:
            download_file(filename, url, raw_dir)
        except DownloadError as e:
            failed[filename] = str(e)

    print()
    if failed:
        print("=" * 70)
        print(f"FAILED: {len(failed)} of {len(datasets)} downloads did not complete.")
        for name, reason in failed.items():
            print(f"  - {name}: {reason}")
        print("No partial files were kept; any previous copies of these files are unchanged.")
        print("Re-run the script to try again.")
        print("=" * 70)
        return False
    print(f"All {len(datasets)} files downloaded and verified in {raw_dir}/")
    return True


if __name__ == "__main__":
    try:
        ok = download_datasets()
    except KeyboardInterrupt:
        print("\nFAILED: download cancelled by user (Ctrl+C). Partial file removed.")
        sys.exit(130)
    sys.exit(0 if ok else 1)
