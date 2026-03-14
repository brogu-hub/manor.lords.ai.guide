import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import SAVE_FOLDER
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

    yield

    # Cleanup
    if observer is not None:
        observer.stop()
        observer.join(timeout=5)
        logger.info("Save watcher stopped")


app = FastAPI(title="Manor Lords AI Advisor", lifespan=lifespan)

app.include_router(router)

static_dir = Path(__file__).parent.parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
