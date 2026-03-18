"""Detect Manor Lords launch via Steam registry — zero CPU usage.

Uses Windows RegNotifyChangeKeyValue API to block until the registry
key changes. No polling, no psutil, no dependencies beyond stdlib.
"""

import ctypes
import logging
import threading
import webbrowser
import winreg

logger = logging.getLogger(__name__)

REG_NOTIFY_CHANGE_LAST_SET = 0x00000004
INFINITE = 0xFFFFFFFF

advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32

# Manor Lords Steam App ID
_REG_PATH = r"Software\Valve\Steam\Apps\1363080"


def _watch_registry(dashboard_url: str) -> None:
    """Block on registry changes for the Manor Lords app key."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_PATH,
            0,
            winreg.KEY_READ | winreg.KEY_NOTIFY,
        )
    except FileNotFoundError:
        logger.warning(
            "Steam registry key not found: HKCU\\%s — game detector disabled",
            _REG_PATH,
        )
        return

    logger.info("Game detector watching HKCU\\%s", _REG_PATH)
    was_running = False

    while True:
        # Create a Windows event object
        event = kernel32.CreateEventW(None, True, False, None)
        if not event:
            logger.error("CreateEventW failed")
            break

        # Register for notification — blocks until the key changes
        result = advapi32.RegNotifyChangeKeyValue(
            int(key), False, REG_NOTIFY_CHANGE_LAST_SET, event, True
        )
        if result != 0:
            kernel32.CloseHandle(event)
            logger.error("RegNotifyChangeKeyValue failed: %d", result)
            break

        # Wait — this sleeps the thread at zero CPU
        kernel32.WaitForSingleObject(event, INFINITE)
        kernel32.CloseHandle(event)

        # Check if the game started
        try:
            running, _ = winreg.QueryValueEx(key, "Running")
        except OSError:
            running = 0

        if running == 1 and not was_running:
            logger.info("Manor Lords detected — opening dashboard")
            webbrowser.open(dashboard_url)

        was_running = bool(running)


def start_game_detector(dashboard_url: str) -> None:
    """Start the registry watcher in a daemon thread."""
    t = threading.Thread(
        target=_watch_registry, args=(dashboard_url,), daemon=True
    )
    t.start()
    logger.info("Game detector started (zero-CPU registry watcher)")
