from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from routers import courses, songs, videos

app = FastAPI(title="Guitar Learning Platform V2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(courses.router)
app.include_router(songs.router)
app.include_router(videos.router)

# Static files
BASE_DIR = Path(__file__).parent
app.mount("/library", StaticFiles(directory=str(BASE_DIR / "library")), name="library")
app.mount("/data", StaticFiles(directory=str(BASE_DIR / "data")), name="data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)