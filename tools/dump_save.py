#!/usr/bin/env python3
"""Dump a Manor Lords .sav file to JSON for inspection.

Usage:
    python tools/dump_save.py /saves/autosave_0.sav
    python tools/dump_save.py /saves/autosave_0.sav --output dump.json
    python tools/dump_save.py /saves/autosave_0.sav --keys     # top-level property names
    python tools/dump_save.py /saves/autosave_0.sav --dict      # convert to nested dict
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.parser.gvas_parser import parse_save, properties_to_dict


def main():
    parser = argparse.ArgumentParser(description="Dump a UE4 .sav file to JSON")
    parser.add_argument("save_file", help="Path to .sav file")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--keys", action="store_true", help="Print top-level property names")
    parser.add_argument("--dict", action="store_true", help="Convert to nested dict format")
    args = parser.parse_args()

    try:
        raw = parse_save(args.save_file)
    except Exception as e:
        print(f"Error parsing save file: {e}", file=sys.stderr)
        sys.exit(1)

    if args.keys:
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    name = item.get("name", "unnamed")
                    ptype = item.get("type", "unknown")
                    if ptype == "StructProperty":
                        sub = item.get("subtype", "")
                        val = item.get("value", [])
                        count = len(val) if isinstance(val, list) else "?"
                        print(f"  {name} ({ptype}/{sub}): {count} children")
                    elif ptype in ("HeaderProperty", "FileEndProperty", "NoneProperty"):
                        print(f"  [{ptype}]")
                    else:
                        val = item.get("value", "")
                        print(f"  {name} ({ptype}): {repr(val)[:80]}")
        elif isinstance(raw, dict):
            for key in sorted(raw.keys()):
                val = raw[key]
                if isinstance(val, dict):
                    print(f"  {key}: dict ({len(val)} keys)")
                elif isinstance(val, list):
                    print(f"  {key}: list ({len(val)} items)")
                else:
                    print(f"  {key}: {type(val).__name__} = {repr(val)[:80]}")
        return

    # Convert to nested dict if requested
    data = raw
    if args.dict and isinstance(raw, list):
        data = properties_to_dict(raw)

    output = json.dumps(data, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Written to {args.output} ({len(output)} bytes)")
    else:
        print(output)


if __name__ == "__main__":
    main()
