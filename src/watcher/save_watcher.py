"""File watcher for Manor Lords save files using watchdog."""

import asyncio
import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from src.config import SAVE_FOLDER, DEBOUNCE_SECONDS

logger = logging.getLogger(__name__)


class SaveFileHandler(FileSystemEventHandler):
    """Handles save file changes with debouncing."""

    def __init__(self, callback, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self._callback = callback
        self._loop = loop
        self._last_trigger: float = 0.0

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".sav":
            return

        now = time.time()
        if now - self._last_trigger < DEBOUNCE_SECONDS:
            return
        self._last_trigger = now

        logger.info("Save file changed: %s", path.name)
        asyncio.run_coroutine_threadsafe(self._callback(str(path)), self._loop)


def start_watcher(callback, loop: asyncio.AbstractEventLoop) -> Observer:
    """Start watching the Manor Lords save folder.

    Args:
        callback: Async function to call with the save file path.
        loop: The asyncio event loop to schedule callbacks on.

    Returns:
        The watchdog Observer (already started).
    """
    watch_path = str(SAVE_FOLDER)
    logger.info("Watching save folder: %s", watch_path)

    handler = SaveFileHandler(callback, loop)
    observer = Observer()
    observer.schedule(handler, watch_path, recursive=False)
    observer.daemon = True
    observer.start()

    logger.info("Save watcher started")
    return observer
