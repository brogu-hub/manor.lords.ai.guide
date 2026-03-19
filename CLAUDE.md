# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Manor Lords AI Advisor — parses game save files (Oodle Kraken compressed GVAS), extracts game state, sends to Gemini for strategic advice as "Gerald" (a witty modern engineer transmigrated to medieval times), evaluates quality with DeepEval, and streams results to a real-time dashboard.

## Commands

```bash
# Full stack (Docker)
docker compose up -d --build

# Local dev — two terminals
uvicorn src.dashboard.app:app --host 0.0.0.0 --port 7861 --reload   # Python API
cd web && npm run dev                                                 # Next.js on :7860

# Frontend
cd web && npm run build      # production build
cd web && npm run lint        # ESLint

# Test API
curl http://localhost:7861/api/health
curl http://localhost:7861/api/trends
curl -X POST http://localhost:7861/api/process
```

## Architecture

```
Browser (:7860) → Next.js App Router → API proxy → FastAPI (:7861)
                                                      ├── File Watcher (save changes)
                                                      └── Pipeline:
                                                           parse (.sav) → map (GameState)
                                                           → alerts (YAML rules) → Gemini (streaming)
                                                           → DeepEval (self-healing) → SSE broadcast
                                                           → trajectory label + embed (async)
                                                           → SQLite persist
```

**Save parsing**: Oodle Kraken decompression via ctypes (`libooz.so` built in Docker) + `uesave` CLI → JSON → Pydantic `GameState`. Only works in Docker (Linux binaries). For local dev, run the Python API in Docker.

**Proxy pattern**: Next.js `app/api/[...path]/route.ts` forwards all `/api/*` to Python backend. `API_BASE_URL` env var controls target (Docker: `http://python-api:7861`, local: `http://localhost:7861`).

**SSE streaming**: Pipeline broadcasts events (`state`, `advice`, `streaming_start`, `advice_chunk`, `thinking_chunk`, `streaming_end`, `eval_result`, `error`) via `broadcast_event()`. Frontend `useSSE` hook connects to `/api/stream`.

**Persistence**: SQLite `dashboard.db` stores game state/advice cache, history snapshots (100 entries), trajectory labels, and 3072-dim embeddings. Survives Docker restarts via `api-data` volume.

## Key Files

| File | Purpose |
|------|---------|
| `src/pipeline.py` | Main orchestrator — 10-step flow from save parse to delivery |
| `src/dashboard/routes.py` | All REST + SSE endpoints, SQLite persistence, `/api/trends` |
| `src/dashboard/app.py` | FastAPI entry point, startup lifecycle |
| `src/strategy/gemini_client.py` | Gemini API with auto model detection, context caching, streaming, DeepEval retry |
| `src/mapper/state_mapper.py` | Raw save JSON → GameState with 50+ resource types, compass directions |
| `src/mapper/schemas.py` | Pydantic models: GameState, RealmMap, ResourceNode, BuildingInfo |
| `src/analysis/` | Trend prediction (NumPy), trajectory labeling (Gemini), state embedding, RAG retrieval |
| `configs/advisor_prompt.yaml` | Gerald's persona + response format (WARNINGS, PRIORITY_1-3, SITUATION, NEXT_SEASON) |
| `configs/alert_rules.yaml` | Threshold-based alerts (food < 50 = critical, approval < 30 = critical, etc.) |
| `web/app/page.tsx` | Dashboard layout — wires all panels together |
| `web/hooks/useSSE.ts` | SSE connection + REST fetch on mount, returns all reactive state |
| `web/hooks/useTrends.ts` | Fetches `/api/trends` for charts, forecasts, game path, RAG |
| `web/components/TrendsPanel.tsx` | Collapsible container for all 6 chart/indicator components |
| `web/components/RealmMapPanel.tsx` | SVG compass-rose map of resource nodes |

## Conventions

- **Gerald persona**: All AI output is in-character. System prompt in `configs/advisor_prompt.yaml`. Follow-up chat prompt in `gemini_client.py` `_FOLLOWUP_SYSTEM`. Trajectory labeler also uses Gerald's voice.
- **Medieval theme**: oklch color variables in `web/app/globals.css`. Gold (`--color-gold`), parchment (`--color-parchment`), dark wood backgrounds. Fonts: Cinzel (headings), Crimson Text (body).
- **Component pattern**: Card + CardHeader + CardContent wrapper, `'use client'` directive, null-safe props.
- **Chart theme**: `web/lib/chart-theme.ts` — use these colors for any recharts components.
- **Spatial data**: Resource nodes use compass directions ("north-east", "south-west") and distance labels ("nearby", "a short ride", "far afield") relative to settlement center. No raw coordinates in the schema.
- **Docker is required for save parsing**: `libooz.so` and `uesave` are Linux binaries built in the Dockerfile. Run `docker compose up -d python-api` for local frontend dev.

## Next.js 16 Notes

This uses Next.js 16 with breaking changes from older versions. `params` is now a Promise. Check `node_modules/next/dist/docs/` for current API documentation before writing route handlers or server components.
