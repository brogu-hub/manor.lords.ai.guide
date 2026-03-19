# Manor Lords AI Advisor

AI-powered strategic advisor for [Manor Lords](https://store.steampowered.com/app/1363080/Manor_Lords/) that reads your save files and provides real-time, context-aware counsel through a medieval-themed web dashboard — powered by Gerald, a modern engineer transmigrated into a medieval world.

## How It Works

```text
Save File (.sav)
    |  Oodle Kraken decompression + uesave parsing
    v
Game State (JSON)
    |  Pydantic mapping + spatial data + YAML alert rules
    v
Alerts + State + Realm Map
    |  Gemini API + guide context + session history + RAG
    v
Strategic Advice + Trajectory Analysis
    |  DeepEval quality check + NumPy trend forecasting
    v
Dashboard (SSE) → Next.js + recharts + shadcn/ui
```

1. **Parse** — Decompresses Manor Lords `.sav` files (Oodle Kraken) and converts binary GVAS to JSON via `uesave`
2. **Map** — Extracts 50+ resource types, buildings, population, and spatial data (resource node positions with compass directions) into typed Pydantic models
3. **Alert** — Evaluates YAML-driven threshold rules (starvation, fuel shortage, low approval)
4. **Advise** — Sends game state + guide context to Gemini with auto-detected latest flash model, streaming response line-by-line
5. **Evaluate** — DeepEval scores response quality; auto-retries with correction prompts on failure
6. **Analyse** — Labels trajectory (positive/negative via Gemini), embeds state as 3072-dim vector for RAG retrieval
7. **Forecast** — NumPy linear regression predicts next-season resource levels, approval trends, and game path score
8. **Deliver** — Streams everything to the web dashboard via Server-Sent Events

## Architecture

```text
Browser → Next.js App Router (port 7860) → Python API (port 7861)
                                              ├── File watcher (auto-detect .sav changes)
                                              ├── Game detector (Steam registry, zero CPU)
                                              └── Pipeline:
                                                   parse → map → alerts → Gemini (streaming)
                                                   → DeepEval → SSE broadcast
                                                   → trajectory label + embed (async)
                                                   → SQLite persist (100 snapshots)
```

- **Frontend**: Next.js 16 App Router + shadcn/ui + Tailwind CSS 4 + recharts
- **Backend**: Python FastAPI (REST + SSE) + SQLite persistence
- **AI**: Gerald persona — witty engineer who frames modern knowledge as "ancient Roman texts"
- **Deploy**: Docker Compose (2 containers), auto-restart

## Quick Start

### Prerequisites

- Docker & Docker Compose
- [Gemini API key](https://aistudio.google.com/apikey) (free tier works)
- Manor Lords save files (Windows default path shown below)

### Setup

```bash
git clone https://github.com/brogu-hub/manor.lords.ai.guide.git
cd manor.lords.ai.guide

cp .env.example .env
# Edit .env with your API key and save folder path
```

### Configure `.env`

```env
# Required
GEMINI_API_KEY=your-api-key-here
SAVE_FOLDER=C:\Users\YourUsername\AppData\Local\ManorLords\Saved\SaveGames

# Optional (defaults shown)
PRIMARY_MODEL=auto
FALLBACK_MODEL=gemini-2.5-flash
DASHBOARD_PORT=7861
WEB_PORT=7860
ENABLE_GAME_DETECTION=true
```

### Run

```bash
docker compose up -d --build
```

Open **http://localhost:7860** — the dashboard updates in real-time when you save your game.

### Game Detection (Windows, Optional)

Auto-opens the dashboard in your browser when Manor Lords launches via Steam. Zero CPU — uses kernel-level registry notifications.

```powershell
.\setup-game-detector.ps1
```

Runs once, starts on every login. To remove: delete `ManorLordsDetector` from `shell:startup`.

### Local Development

```bash
# Terminal 1: Python API (must use Docker for save parsing — needs libooz.so + uesave)
docker compose up -d python-api

# Terminal 2: Next.js frontend
cd web && npm run dev
```

## Features

### Save Parsing & Realm Map
- Oodle Kraken decompression of Manor Lords binary saves
- `uesave` CLI converts GVAS to JSON
- Extracts 50+ resource types, building counts, worker assignments, population stats
- **Spatial awareness**: resource node positions mapped to compass directions and distances
- Gerald knows where iron deposits, berry thickets, stone quarries, and hunting grounds are relative to your settlement

### AI Strategy Engine (Gerald)
- **Character**: A modern mechanical engineer transmigrated to a medieval world — witty, funny, full of wonder, passionate about castle design
- **Auto model detection** — queries Gemini API for the latest flash model
- **Fallback chain** — primary model → fallback on rate limit
- **Context caching** — Gemini explicit cache for system prompt + guides (saves API cost)
- **Extended thinking** — dynamic thinking budget based on game complexity
- **Streaming** — response appears line-by-line in real-time, including thinking tokens
- **RAG knowledge base** — Steam Workshop guides + patch notes + medieval settlement guide

### DeepEval Self-Healing

| Metric | What it checks | Threshold |
|--------|---------------|-----------|
| Format compliance | All required sections present with substance | 0.7 |
| Specificity | References actual numbers, buildings, counts | 0.6 |
| State relevance | Addresses critical alerts (food/fuel/approval) | 0.6 |

Failed evaluations trigger automatic retries with correction prompts. Max 3 total attempts.

### Trend Charts & Predictions
- **Resource Sustainability** — food total + food-per-family trend with NumPy forecast line and danger threshold
- **Approval & Housing** — approval % trend with homeless count overlay, forecast, and reference zones
- **Economy Overview** — wealth + development points + population with togglable series
- **Winter Readiness Gauge** — food/fuel/clothing readiness bars with composite score
- **Surplus Advisor** — "Build Your Legacy" / "Stabilise First" / "Survival Mode" with condition checklist
- **Game Path Card** — LLM trajectory verdict + RAG comparison against similar past games + learning tips
- **Cartographer's Survey** — SVG compass-rose map showing all resource nodes by direction and distance

### ML-Powered Game Path Analysis
- **Trajectory labeling**: Gemini scores each game state as positive/negative with reasoning
- **State embedding**: 3072-dim vectors via Gemini embedding API
- **RAG retrieval**: Cascading filter (game stage) + cosine similarity finds similar past states
- **Past games comparison**: "3 of 4 similar past states led to success"
- **NumPy forecasting**: Linear regression predicts next-season values for all key metrics

### Game Detection (Windows)
- Zero-CPU registry watcher using `RegNotifyChangeKeyValue`
- Watches `HKCU\Software\Valve\Steam\Apps\1363080\Running`
- Auto-opens browser when Manor Lords launches via Steam

### Web Dashboard
- Next.js 16 + shadcn/ui with medieval dark theme (oklch colors)
- Save file selector + drag-and-drop upload
- Real-time state bar (year, season, families, food, approval, alerts)
- Advice panels: Warnings, Priorities, Situation, Next Season
- Streaming panel showing AI thinking + response in real-time
- Follow-up chat for conversational questions (Gerald stays in character)
- Clickable history — load full state + advice snapshots from past analyses
- Pop-out compact window for use alongside the game
- Persistent data survives Docker restarts (SQLite + Docker volume)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |
| GET | `/api/state` | Current parsed game state (includes realm map) |
| GET | `/api/advice` | Latest generated advice |
| GET | `/api/saves` | List available save files |
| GET | `/api/history` | Session advice history (up to 100 entries) |
| GET | `/api/history/{id}` | Full state + advice snapshot for a history entry |
| GET | `/api/trends` | Time-series data + forecasts + game path + RAG similar states |
| GET | `/api/logs` | Request/response debug logs |
| GET | `/api/stream` | SSE stream for real-time updates |
| POST | `/api/process` | Trigger pipeline on a save file |
| POST | `/api/upload` | Upload a .sav file directly |
| POST | `/api/ask` | Ask Gerald a follow-up question |

## Project Structure

```text
web/                  # Next.js 16 App Router frontend
  app/
    page.tsx          # Main dashboard
    popout/           # Compact pop-out window
    api/              # Proxy routes to Python backend
  components/         # Dashboard panels, charts, realm map
    charts/           # Recharts trend + indicator components
  hooks/              # useSSE (real-time), useTrends (charts)
  lib/                # Chart theme, utilities
src/
  parser/             # Oodle Kraken decompression + uesave
  mapper/             # Game state extraction, Pydantic schemas, alert engine
  strategy/           # Gemini client, DeepEval evaluator, prompts
  analysis/           # Trend prediction, trajectory labeling, embeddings, RAG
  guides/             # Steam patch notes + Workshop guide fetcher
  memory/             # Session history + request log (SQLite)
  dashboard/          # FastAPI app, routes, SSE streaming, SQLite persistence
  watcher/            # File watcher + game detector
  config.py           # Centralized env-backed configuration
  pipeline.py         # Orchestrator tying all components together
configs/              # YAML configs (alert rules, advisor prompt, mapper)
guides/               # Static markdown strategy guides (castle design, etc.)
```

## Tech Stack

- **Next.js 16** (App Router) + shadcn/ui + Tailwind CSS 4 + recharts
- **Python 3.12** / FastAPI / Uvicorn
- **Google Gemini** (genai SDK) with context caching + embedding API
- **DeepEval** for LLM response quality evaluation
- **NumPy** for trend forecasting
- **SQLite** for persistent history, embeddings, and request logs
- **Docker** with custom build for Oodle Kraken decompressor
- **uesave** for Unreal Engine GVAS parsing
