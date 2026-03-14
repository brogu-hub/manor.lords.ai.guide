"""GVAS save file parser using Oodle Kraken decompression + uesave CLI.

Manor Lords saves are Oodle Kraken compressed. Pipeline:
  1. Decompress with Kraken_Decompress (ooz shared library via ctypes)
  2. Parse decompressed GVAS with uesave CLI → JSON
  3. Return parsed dict
"""

import ctypes
import json
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the compiled ooz shared library (built from rarten/ooz)
_OOZ_LIB_PATH = "/opt/libooz.so"
_UESAVE_PATH = "/usr/local/bin/uesave"

# Lazy-loaded decompressor
_kraken_fn = None


def _get_kraken():
    """Lazy-load the Kraken decompression function from libooz.so."""
    global _kraken_fn
    if _kraken_fn is not None:
        return _kraken_fn

    lib = ctypes.CDLL(_OOZ_LIB_PATH)
    # C++ mangled name for: int Kraken_Decompress(const byte*, size_t, byte*, size_t)
    fn = lib._Z17Kraken_DecompressPKhmPhm
    fn.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t]
    fn.restype = ctypes.c_int
    _kraken_fn = fn
    logger.info("Loaded Kraken decompressor from %s", _OOZ_LIB_PATH)
    return fn


def _get_uncompressed_size(save_path: Path) -> int | None:
    """Try to read uncompressed size from the companion _descr.sav file."""
    descr_path = save_path.parent / (save_path.stem + "_descr.sav")
    if not descr_path.exists():
        return None

    try:
        result = subprocess.run(
            [_UESAVE_PATH, "to-json"],
            stdin=open(descr_path, "rb"),
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        descr = json.loads(result.stdout)
        return descr.get("root", {}).get("properties", {}).get("UncompressedSize_0")
    except Exception as e:
        logger.warning("Could not read descr file: %s", e)
        return None


def decompress_save(file_path: str | Path) -> bytes:
    """Decompress an Oodle Kraken compressed .sav file.

    Returns the raw decompressed GVAS bytes.
    """
    path = Path(file_path)
    compressed = path.read_bytes()

    # Try to get uncompressed size from descr file
    uncompressed_size = _get_uncompressed_size(path)
    if uncompressed_size is None:
        # Estimate: Manor Lords saves compress ~5:1
        uncompressed_size = len(compressed) * 8
        logger.warning(
            "No descr file found, estimating uncompressed size: %d", uncompressed_size
        )

    kraken = _get_kraken()
    dst = ctypes.create_string_buffer(uncompressed_size + 65536)
    result = kraken(compressed, len(compressed), dst, uncompressed_size)

    if result <= 0:
        raise RuntimeError(
            f"Kraken decompression failed (returned {result}). "
            f"Compressed: {len(compressed)} bytes, target: {uncompressed_size}"
        )

    logger.info(
        "Decompressed %d → %d bytes", len(compressed), result
    )
    return dst.raw[:result]


def parse_save(file_path: str | Path) -> dict:
    """Parse a Manor Lords .sav file and return the game state as a dict.

    Steps:
      1. Decompress with Oodle Kraken
      2. Parse decompressed GVAS with uesave CLI
      3. Return the root properties dict

    Args:
        file_path: Path to the .sav file.

    Returns:
        The parsed save data as a nested dict (uesave JSON format).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Save file not found: {path}")

    logger.info("Parsing save file: %s", path.name)

    # Step 1: Decompress
    decompressed = decompress_save(path)

    # Step 2: Parse with uesave
    result = subprocess.run(
        [_UESAVE_PATH, "to-json"],
        input=decompressed,
        capture_output=True,
        timeout=120,
    )

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"uesave parsing failed: {stderr}")

    raw = json.loads(result.stdout)

    # Extract the properties dict from uesave's output format
    properties = raw.get("root", {}).get("properties", {})
    logger.info("Parsed successfully — %d top-level properties", len(properties))

    return properties


def parse_save_to_json_string(file_path: str | Path) -> str:
    """Parse a .sav file and return the JSON as a formatted string."""
    raw = parse_save(file_path)
    return json.dumps(raw, indent=2, ensure_ascii=False)
