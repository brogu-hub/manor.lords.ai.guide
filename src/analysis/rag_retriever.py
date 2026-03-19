"""Cascading RAG retriever — finds similar past game states."""

import json
import logging
import math

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

_DB_PATH = DATA_DIR / "dashboard.db"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_similar_states(
    current_embedding: list[float] | None,
    current_year: int,
    current_families: int,
    top_k: int = 5,
) -> list[dict]:
    """Find similar past states using cascading filter + embedding similarity.

    Step 1: Filter by game stage (year ±1, families ±50%)
    Step 2: Rank by cosine similarity of embeddings
    Step 3: Return top_k with their trajectory labels + reasoning
    """
    import sqlite3

    try:
        db = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    except Exception as e:
        logger.warning("Could not open dashboard DB for RAG: %s", e)
        return []

    # Step 1: Filter by game stage
    min_year = max(1, current_year - 1)
    max_year = current_year + 1
    min_families = max(1, int(current_families * 0.5))
    max_families = int(current_families * 1.5) + 1

    try:
        rows = db.execute("""
            SELECT id, timestamp, save_name, state_json,
                   trajectory_label, trajectory_score, trajectory_reasoning,
                   trajectory_strengths, trajectory_risks, embedding
            FROM history
            WHERE trajectory_label IS NOT NULL
              AND state_json IS NOT NULL
        """).fetchall()
    except Exception as e:
        logger.warning("RAG query failed: %s", e)
        return []
    finally:
        db.close()

    candidates = []
    for row in rows:
        state = json.loads(row[3]) if row[3] else {}
        meta = state.get("meta", {})
        pop = state.get("settlement", {}).get("population", {})
        year = meta.get("year", 0)
        families = pop.get("families", 0)

        # Stage filter
        if not (min_year <= year <= max_year):
            continue
        if not (min_families <= families <= max_families):
            continue

        embedding = json.loads(row[9]) if row[9] else None

        candidates.append({
            "id": row[0],
            "timestamp": row[1],
            "save_name": row[2],
            "label": row[4],
            "score": row[5],
            "reasoning": row[6],
            "strengths": json.loads(row[7]) if row[7] else [],
            "risks": json.loads(row[8]) if row[8] else [],
            "embedding": embedding,
            "year": year,
            "season": meta.get("season", ""),
            "families": families,
        })

    # Step 2: Rank by cosine similarity
    if current_embedding and any(c.get("embedding") for c in candidates):
        for c in candidates:
            if c.get("embedding"):
                c["similarity"] = round(_cosine_similarity(current_embedding, c["embedding"]), 3)
            else:
                c["similarity"] = 0.0
        candidates.sort(key=lambda c: c["similarity"], reverse=True)
    else:
        # No embeddings — sort by score descending
        for c in candidates:
            c["similarity"] = 0.0
        candidates.sort(key=lambda c: c.get("score", 0), reverse=True)

    # Step 3: Return top_k (strip embedding from response)
    results = []
    for c in candidates[:top_k]:
        c.pop("embedding", None)
        results.append(c)

    logger.info("RAG: %d candidates filtered, returning top %d", len(candidates), len(results))
    return results
