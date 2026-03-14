"""Fetch Manor Lords patch notes and Workshop guides from Steam."""

import html
import json
import logging
import re
import urllib.request
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

STEAM_APP_ID = 1363080
STORE_PATH = Path(__file__).parent.parent.parent / "data" / "patch_notes.json"
WORKSHOP_STORE_PATH = Path(__file__).parent.parent.parent / "data" / "workshop_guides.json"

# Workshop guide IDs to fetch (add more here)
WORKSHOP_GUIDE_IDS = [
    "3427105626",
]


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    # Collapse excessive whitespace but keep paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _load_stored() -> list[dict]:
    """Load previously stored patch notes."""
    if not STORE_PATH.exists():
        return []
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_stored(notes: list[dict]):
    """Persist patch notes to disk."""
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_patch_notes(count: int = 5) -> list[dict]:
    """Fetch latest Manor Lords patch notes from Steam API."""
    url = (
        f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
        f"?appid={STEAM_APP_ID}&count={count}&maxlength=0"
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.warning("Failed to fetch Steam patch notes: %s", e)
        return []

    items = data.get("appnews", {}).get("newsitems", [])

    notes = []
    for item in items:
        # Only official developer posts
        if item.get("feedlabel") != "Community Announcements":
            continue
        notes.append({
            "gid": item["gid"],
            "title": item.get("title", ""),
            "date": item.get("date", 0),
            "date_str": datetime.fromtimestamp(item.get("date", 0)).strftime("%Y-%m-%d"),
            "content": _strip_html(item.get("contents", "")),
        })

    return notes


def update_guide_cache() -> int:
    """Fetch new patch notes and merge with stored ones. Returns count of new notes."""
    stored = _load_stored()
    known_gids = {n["gid"] for n in stored}

    fetched = fetch_patch_notes()
    new_notes = [n for n in fetched if n["gid"] not in known_gids]

    if not new_notes:
        logger.info("Patch notes up to date (%d stored)", len(stored))
        return 0

    stored.extend(new_notes)
    # Sort by date descending, keep most recent 20
    stored.sort(key=lambda n: n["date"], reverse=True)
    stored = stored[:20]
    _save_stored(stored)
    logger.info("Added %d new patch notes (%d total stored)", len(new_notes), len(stored))
    return len(new_notes)


def get_patch_context(max_notes: int = 5) -> str:
    """Format stored patch notes as markdown for LLM context injection."""
    notes = _load_stored()
    if not notes:
        return ""

    # Most recent first, limited
    recent = notes[:max_notes]
    lines = ["\n\nRECENT MANOR LORDS PATCH NOTES (from Steam):"]
    for note in recent:
        lines.append(f"\n--- {note['title']} ({note['date_str']}) ---")
        # Truncate very long patch notes to keep context reasonable
        content = note["content"]
        if len(content) > 2000:
            content = content[:2000] + "\n[... truncated]"
        lines.append(content)

    return "\n".join(lines)


# -- Steam Workshop Guides --

def _load_workshop_guides() -> list[dict]:
    """Load stored Workshop guides."""
    if not WORKSHOP_STORE_PATH.exists():
        return []
    try:
        return json.loads(WORKSHOP_STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_workshop_guides(guides: list[dict]):
    """Persist Workshop guides to disk."""
    WORKSHOP_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKSHOP_STORE_PATH.write_text(
        json.dumps(guides, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def fetch_workshop_guide(guide_id: str) -> dict | None:
    """Fetch a Steam Workshop guide page and extract its content."""
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={guide_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ManorLordsAdvisor/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw_html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("Failed to fetch Workshop guide %s: %s", guide_id, e)
        return None

    # Extract title
    title_match = re.search(r'<div class="workshopItemTitle">([^<]+)</div>', raw_html)
    title = _strip_html(title_match.group(1)) if title_match else f"Guide {guide_id}"

    # Extract guide body — Workshop guides use subSectionDesc divs
    sections = re.findall(
        r'<div class="subSectionDesc">(.*?)</div>\s*(?:</div>|\s*<div class="subSection)',
        raw_html,
        re.DOTALL,
    )
    if sections:
        # Also grab section titles
        titles = re.findall(
            r'<div class="subSectionTitle">([^<]+)</div>',
            raw_html,
        )
        parts = []
        for i, section_html in enumerate(sections):
            if i < len(titles):
                parts.append(f"\n## {_strip_html(titles[i])}\n")
            parts.append(_strip_html(section_html))
        content = "\n".join(parts)
    else:
        # Fallback: try workshopItemDescription
        body_match = re.search(
            r'<div class="workshopItemDescription"[^>]*>(.*?)</div>',
            raw_html,
            re.DOTALL,
        )
        if not body_match:
            logger.warning("Could not extract content from Workshop guide %s", guide_id)
            return None
        content = _strip_html(body_match.group(1))
    if len(content) < 100:
        logger.warning("Workshop guide %s content too short (%d chars)", guide_id, len(content))
        return None

    return {
        "guide_id": guide_id,
        "title": title,
        "content": content,
        "fetched": datetime.now().isoformat(),
    }


def update_workshop_guides() -> int:
    """Fetch Workshop guides listed in WORKSHOP_GUIDE_IDS. Returns count of new/updated."""
    stored = _load_workshop_guides()
    known_ids = {g["guide_id"] for g in stored}
    updated = 0

    for guide_id in WORKSHOP_GUIDE_IDS:
        if guide_id in known_ids:
            continue
        guide = fetch_workshop_guide(guide_id)
        if guide:
            stored.append(guide)
            updated += 1
            logger.info("Fetched Workshop guide: %s", guide["title"])

    if updated:
        _save_workshop_guides(stored)

    logger.info("Workshop guides: %d stored, %d new", len(stored), updated)
    return updated


def get_workshop_context() -> str:
    """Format stored Workshop guides for LLM context injection."""
    guides = _load_workshop_guides()
    if not guides:
        return ""

    lines = ["\n\nSTEAM COMMUNITY GUIDES:"]
    for guide in guides:
        lines.append(f"\n--- {guide['title']} ---")
        content = guide["content"]
        # Cap at 5000 chars per guide
        if len(content) > 5000:
            content = content[:5000] + "\n[... truncated]"
        lines.append(content)

    return "\n".join(lines)
