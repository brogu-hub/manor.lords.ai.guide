import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import CORS_ORIGINS, ENABLE_GAME_DETECTION, SAVE_FOLDER
from src.dashboard.routes import router
from src.pipeline import load_guides, process_save
from src.watcher.save_watcher import start_watcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the file watcher and load guides on startup."""
    # Load guide documents for LLM context
    load_guides()

    # Start the save file watcher
    loop = asyncio.get_running_loop()
    observer = None

    if SAVE_FOLDER.exists():
        observer = start_watcher(process_save, loop)
        logger.info("Advisor ready — watching %s", SAVE_FOLDER)
    else:
        logger.warning("Save folder not found: %s — watcher not started", SAVE_FOLDER)
        logger.warning("Set SAVE_FOLDER in .env to your Manor Lords save path")

    # Start game detector (Windows only, local only)
    if sys.platform == "win32" and ENABLE_GAME_DETECTION:
        try:
            from src.watcher.game_detector import start_game_detector

            start_game_detector("http://localhost:7860")
        except Exception as e:
            logger.warning("Game detector failed to start: %s", e)

    yield

    # Cleanup
    if observer is not None:
        observer.stop()
        observer.join(timeout=5)
        logger.info("Save watcher stopped")


app = FastAPI(title="Manor Lords AI Advisor", lifespan=lifespan)

# CORS for local dev (Remix on :7860, Python API on :7861)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
