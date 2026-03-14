#!/usr/bin/env python3
"""Dump a Manor Lords .sav file to JSON for inspection.

Usage:
    python tools/dump_save.py /saves/saveGame_1.sav
    python tools/dump_save.py /saves/saveGame_1.sav --output dump.json
    python tools/dump_save.py /saves/saveGame_1.sav --keys     # top-level property names
    python tools/dump_save.py /saves/saveGame_1.sav --state    # mapped GameState
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.parser.gvas_parser import parse_save
from src.mapper.state_mapper import map_state


def main():
    parser = argparse.ArgumentParser(description="Dump a Manor Lords .sav file to JSON")
    parser.add_argument("save_file", help="Path to .sav file")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--keys", action="store_true", help="Print top-level property names")
    parser.add_argument("--state", action="store_true", help="Show mapped GameState")
    args = parser.parse_args()

    try:
        props = parse_save(args.save_file)
    except Exception as e:
        print(f"Error parsing save file: {e}", file=sys.stderr)
        sys.exit(1)

    if args.keys:
        for key in sorted(props.keys()):
            val = props[key]
            if isinstance(val, dict):
                print(f"  {key}: dict ({len(val)} keys)")
            elif isinstance(val, list):
                print(f"  {key}: list ({len(val)} items)")
            elif isinstance(val, str):
                print(f"  {key}: {repr(val)[:80]}")
            else:
                print(f"  {key}: {type(val).__name__} = {repr(val)[:80]}")
        return

    if args.state:
        state = map_state(props)
        output = json.dumps(state.model_dump(), indent=2, ensure_ascii=False)
    else:
        output = json.dumps(props, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Written to {args.output} ({len(output)} bytes)")
    else:
        print(output)


if __name__ == "__main__":
    main()
