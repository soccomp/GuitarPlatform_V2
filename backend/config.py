from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

DATA_DIR = BACKEND_DIR / "data"
INDEX_FILE = DATA_DIR / "index.json"

LIBRARY_DIR = ROOT_DIR / "library"
COURSES_DIR = LIBRARY_DIR / "courses"
SONGS_DIR = LIBRARY_DIR / "songs"
COLLECTED_DIR = LIBRARY_DIR / "collected"
