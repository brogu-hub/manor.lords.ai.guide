"""GVAS save file parser wrapping SavConverter."""

import json
import logging
from pathlib import Path

from SavConverter import read_sav, sav_to_json

logger = logging.getLogger(__name__)


def parse_save(file_path: str | Path) -> list | dict:
    """Parse a UE4 .sav file and return the raw GVAS property tree.

    SavConverter returns a list of property objects, each with:
        - type: e.g. "HeaderProperty", "StructProperty", "IntProperty"
        - name: the property name
        - value: the property value (can be nested)

    Args:
        file_path: Path to the .sav file.

    Returns:
        The full GVAS property tree (typically a list of property dicts).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Save file not found: {path}")

    logger.info("Parsing save file: %s", path)
    props = read_sav(str(path))
    raw = sav_to_json(props, string=False)

    count = len(raw) if isinstance(raw, (list, dict)) else 0
    logger.info("Parsed successfully — %d top-level properties", count)
    return raw


def parse_save_to_json_string(file_path: str | Path) -> str:
    """Parse a .sav file and return the JSON as a formatted string."""
    raw = parse_save(file_path)
    return json.dumps(raw, indent=2, ensure_ascii=False)


def properties_to_dict(props: list) -> dict:
    """Convert a SavConverter property list to a nested dict for easier traversal.

    Converts:
        [{"type": "IntProperty", "name": "year", "value": 3}, ...]
    Into:
        {"year": 3, ...}

    For StructProperty with nested values, recurses into the value list.
    For ArrayProperty, preserves the array structure.
    """
    result = {}
    for prop in props:
        if not isinstance(prop, dict):
            continue

        prop_type = prop.get("type", "")
        name = prop.get("name", "")

        if prop_type in ("NoneProperty", "FileEndProperty", "HeaderProperty"):
            continue

        if not name:
            continue

        if prop_type == "StructProperty":
            value = prop.get("value", [])
            if isinstance(value, list):
                result[name] = properties_to_dict(value)
            else:
                result[name] = value

        elif prop_type == "ArrayProperty":
            arr_values = prop.get("value", [])
            if isinstance(arr_values, list) and arr_values and isinstance(arr_values[0], dict):
                # Array of structs
                result[name] = [
                    properties_to_dict(item) if isinstance(item, list)
                    else properties_to_dict(item.get("value", [])) if isinstance(item, dict) and "value" in item and isinstance(item["value"], list)
                    else item.get("value", item) if isinstance(item, dict)
                    else item
                    for item in arr_values
                ]
            else:
                result[name] = arr_values

        elif prop_type == "MapProperty":
            result[name] = prop.get("value", {})

        else:
            # Simple types: IntProperty, FloatProperty, BoolProperty, StrProperty, etc.
            result[name] = prop.get("value")

    return result
