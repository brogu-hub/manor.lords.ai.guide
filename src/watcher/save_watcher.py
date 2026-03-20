"""File watcher for Manor Lords save files.

Uses watchdog for native OS events + a polling fallback for Docker volume mounts
where inotify events don't propagate from the Windows host.
"""

import asyncio
import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from src.config import SAVE_FOLDER, DEBOUNCE_SECONDS

logger = logging.getLogger(__name__)

POLL_INTERVAL = 5.0  # seconds between polling checks


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
        if "_descr" in path.stem or path.stem == "rtsSettings":
            return

        now = time.time()
        if now - self._last_trigger < DEBOUNCE_SECONDS:
            return
        self._last_trigger = now

        logger.info("Save file changed: %s", path.name)
        asyncio.run_coroutine_threadsafe(self._callback(str(path)), self._loop)

    def trigger(self, path: Path):
        """Manually trigger from the polling fallback."""
        now = time.time()
        if now - self._last_trigger < DEBOUNCE_SECONDS:
            return
        self._last_trigger = now

        logger.info("Save file changed (poll): %s", path.name)
        asyncio.run_coroutine_threadsafe(self._callback(str(path)), self._loop)


def _poll_loop(watch_path: Path, handler: SaveFileHandler, stop_event: threading.Event):
    """Polling fallback — checks file mtimes periodically.

    Docker Desktop volume mounts (Windows → Linux) don't forward inotify events,
    so we poll as a reliable backup. Only triggers if a .sav file's mtime changed.
    """
    known_mtimes: dict[str, float] = {}

    # Seed with current mtimes
    for f in watch_path.glob("*.sav"):
        if "_descr" in f.stem or f.stem == "rtsSettings":
            continue
        try:
            known_mtimes[f.name] = f.stat().st_mtime
        except OSError:
            pass

    logger.info("Poll watcher seeded with %d save files", len(known_mtimes))

    while not stop_event.is_set():
        stop_event.wait(POLL_INTERVAL)
        if stop_event.is_set():
            break

        try:
            for f in watch_path.glob("*.sav"):
                if "_descr" in f.stem or f.stem == "rtsSettings":
                    continue
                try:
                    mtime = f.stat().st_mtime
                except OSError:
                    continue

                prev = known_mtimes.get(f.name)
                if prev is None or mtime > prev:
                    known_mtimes[f.name] = mtime
                    if prev is not None:  # Skip initial seed
                        handler.trigger(f)
        except Exception as e:
            logger.warning("Poll watcher error: %s", e)


def start_watcher(callback, loop: asyncio.AbstractEventLoop) -> Observer:
    """Start watching the Manor Lords save folder.

    Uses both watchdog (OS events) and a polling fallback for Docker mounts.

    Args:
        callback: Async function to call with the save file path.
        loop: The asyncio event loop to schedule callbacks on.

    Returns:
        The watchdog Observer (already started).
    """
    watch_path = Path(SAVE_FOLDER)
    logger.info("Watching save folder: %s", watch_path)

    handler = SaveFileHandler(callback, loop)

    # Start watchdog (works for native FS, may not work in Docker)
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.daemon = True
    observer.start()

    # Start polling fallback (always reliable)
    stop_event = threading.Event()
    poll_thread = threading.Thread(
        target=_poll_loop,
        args=(watch_path, handler, stop_event),
        daemon=True,
        name="save-poll-watcher",
    )
    poll_thread.start()

    logger.info("Save watcher started (watchdog + poll every %.0fs)", POLL_INTERVAL)
    return observer
