#!/usr/bin/env python3
"""Search a raw GVAS JSON dump for a specific value.

Used for reverse-engineering Manor Lords save file property paths.
Load the game, note a value on screen, save, dump to JSON, then search.

Usage:
    python tools/discover_paths.py dump.json 340          # find integer 340
    python tools/discover_paths.py dump.json 67.0 --float # find float 67.0
    python tools/discover_paths.py dump.json "Winter"     # find string "Winter"
    python tools/discover_paths.py dump.json 0.67 --float # find float 0.67 (approval as 0-1)
"""

import argparse
import json
import sys
from pathlib import Path


def search_json(data, target, path="", tolerance=0.01):
    """Recursively search JSON for a target value, yielding matching paths."""
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            yield from search_json(value, target, current_path, tolerance)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            yield from search_json(item, target, current_path, tolerance)
    else:
        match = False
        if isinstance(target, str):
            if isinstance(data, str) and target.lower() in data.lower():
                match = True
        elif isinstance(target, float):
            if isinstance(data, (int, float)) and abs(float(data) - target) < tolerance:
                match = True
        elif isinstance(target, int):
            if isinstance(data, int) and data == target:
                match = True
            elif isinstance(data, float) and abs(data - float(target)) < tolerance:
                match = True

        if match:
            yield path, data


def main():
    parser = argparse.ArgumentParser(description="Search GVAS JSON for a value")
    parser.add_argument("json_file", help="Path to the raw JSON dump")
    parser.add_argument("value", help="Value to search for")
    parser.add_argument("--float", dest="as_float", action="store_true",
                        help="Treat value as float")
    parser.add_argument("--tolerance", type=float, default=0.01,
                        help="Tolerance for float comparison (default: 0.01)")
    parser.add_argument("--max", type=int, default=50,
                        help="Maximum results to show (default: 50)")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"File not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Parse the target value
    if args.as_float:
        target = float(args.value)
    else:
        try:
            target = int(args.value)
        except ValueError:
            try:
                target = float(args.value)
            except ValueError:
                target = args.value  # string search

    print(f"Searching for: {target!r} (type: {type(target).__name__})")
    print(f"{'─' * 80}")

    count = 0
    for path, found_value in search_json(data, target, tolerance=args.tolerance):
        print(f"  {path}")
        print(f"    → {found_value!r}")
        print()
        count += 1
        if count >= args.max:
            print(f"... showing first {args.max} results. Use --max to increase.")
            break

    if count == 0:
        print("  No matches found.")
        if isinstance(target, int):
            print(f"  Try: --float to search for {float(target)}")
            print(f"  Try: searching for {target / 100.0} (might be stored as 0-1 range)")
    else:
        print(f"Found {count} match(es).")


if __name__ == "__main__":
    main()
