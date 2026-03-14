"""Parse structured LLM output into AdviceResponse."""

import re
from pydantic import BaseModel


class AdviceResponse(BaseModel):
    """Structured advice from the LLM."""
    warnings: list[str] = []
    priority_1: str = ""
    priority_2: str = ""
    priority_3: str = ""
    situation: str = ""
    next_season: str = ""
    raw_text: str = ""


def parse_advice(text: str) -> AdviceResponse:
    """Parse the LLM's structured text into an AdviceResponse.

    Expects the format:
        WARNINGS: ...
        PRIORITY_1: ...
        PRIORITY_2: ...
        PRIORITY_3: ...
        SITUATION: ...
        NEXT_SEASON: ...
    """
    sections = {
        "WARNINGS": "",
        "PRIORITY_1": "",
        "PRIORITY_2": "",
        "PRIORITY_3": "",
        "SITUATION": "",
        "NEXT_SEASON": "",
    }

    # Split by section headers
    pattern = r"(WARNINGS|PRIORITY_1|PRIORITY_2|PRIORITY_3|SITUATION|NEXT_SEASON)\s*:\s*"
    parts = re.split(pattern, text)

    # parts alternates: [preamble, key, value, key, value, ...]
    for i in range(1, len(parts) - 1, 2):
        key = parts[i].strip()
        value = parts[i + 1].strip()
        if key in sections:
            sections[key] = value

    # Parse warnings as a list (split on newlines or bullet points)
    warnings_text = sections["WARNINGS"]
    if warnings_text.lower().startswith("none"):
        warnings = []
    else:
        warnings = [
            line.strip().lstrip("•-* ")
            for line in re.split(r"[\n;]", warnings_text)
            if line.strip() and not line.strip().startswith("None")
        ]

    return AdviceResponse(
        warnings=warnings,
        priority_1=sections["PRIORITY_1"],
        priority_2=sections["PRIORITY_2"],
        priority_3=sections["PRIORITY_3"],
        situation=sections["SITUATION"],
        next_season=sections["NEXT_SEASON"],
        raw_text=text,
    )
