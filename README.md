# Manor Lords AI Advisor

AI-powered strategic advisor for [Manor Lords](https://store.steampowered.com/app/1363080/Manor_Lords/) that reads your save files and provides real-time, context-aware counsel through a medieval-themed web dashboard.

## How It Works

```text
Save File (.sav)
    |  Oodle Kraken decompression + uesave parsing
    v
Game State (JSON)
    |  Pydantic mapping + YAML-based alert rules
    v
Alerts + State
    |  Gemini API + guide context + session history
    v
Strategic Advice
    |  DeepEval quality check (format, specificity, relevance)
    v
Dashboard (SSE) → React Router + shadcn/ui
```

1. **Parse** -- Decompresses Manor Lords `.sav` files (Oodle Kraken) and converts binary GVAS to JSON via `uesave`
2. **Map** -- Extracts resources, population, buildings, and metadata into typed Pydantic models
3. **Alert** -- Evaluates YAML-driven threshold rules (starvation, fuel shortage, low approval)
4. **Advise** -- Sends game state + guide context to Gemini with auto-detected latest flash model
5. **Evaluate** -- DeepEval scores response quality; auto-retries with correction prompts on failure
6. **Deliver** -- Streams results to the web dashboard via Server-Sent Events

## Architecture

```text
Browser → React Router (port 7860) → Python API (port 7861)
                                        ├── File watcher (auto-detect .sav changes)
                                        └── Game detector (Steam registry, zero CPU)
```

- **Frontend**: React Router (Remix successor) + shadcn/ui + Tailwind CSS
- **Backend**: Python FastAPI (REST + SSE)
- **Deploy**: Docker Compose (2 containers), Coolify-ready

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

Open **http://localhost:7860** -- the dashboard updates in real-time when you save your game.

### Game Detection (Windows, Optional)

Auto-opens the dashboard in your browser when Manor Lords launches via Steam. Zero CPU -- uses kernel-level registry notifications.

```powershell
.\setup-game-detector.ps1
```

Runs once, starts on every login. To remove: delete `ManorLordsDetector` from `shell:startup`.

### Local Development

```bash
# Terminal 1: Python API
uvicorn src.dashboard.app:app --host 0.0.0.0 --port 7861 --reload

# Terminal 2: React Router frontend
cd web && npm run dev
```

## Features

### Save Parsing
- Oodle Kraken decompression of Manor Lords binary saves
- `uesave` CLI converts GVAS to JSON
- Extracts 50+ resource types, building counts, worker assignments, population stats

### AI Strategy Engine
- **Auto model detection** -- queries Gemini API for the latest flash model
- **Fallback chain** -- primary model -> fallback on rate limit
- **Context caching** -- Gemini explicit cache for system prompt + guides
- **Extended thinking** -- dynamic thinking budget based on game complexity
- **Structured output** -- Warnings, 3 priorities, situation summary, next season prep

### DeepEval Self-Healing

| Metric | What it checks | Threshold |
|--------|---------------|-----------|
| Format compliance | All required sections present with substance | 0.7 |
| Specificity | References actual numbers, buildings, counts | 0.6 |
| State relevance | Addresses critical alerts (food/fuel/approval) | 0.6 |

Failed evaluations trigger automatic retries with correction prompts. Max 3 total attempts.

### Game Detection (Windows)
- Zero-CPU registry watcher using `RegNotifyChangeKeyValue`
- Watches `HKCU\Software\Valve\Steam\Apps\1363080\Running`
- Auto-opens browser when Manor Lords launches via Steam
- No polling, no psutil — pure kernel-level notification

### Web Dashboard
- React Router + shadcn/ui with medieval dark theme
- Save file selector + drag-and-drop upload
- Real-time state bar (year, season, families, food, approval, alerts)
- Advice panels: Warnings, Priorities, Situation, Next Season
- Follow-up chat for conversational questions
- Pop-out compact window for use alongside the game
- SSE streaming — save changes trigger instant AI advice

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |
| GET | `/api/state` | Current parsed game state |
| GET | `/api/advice` | Latest generated advice |
| GET | `/api/saves` | List available save files |
| GET | `/api/history` | Session advice history |
| GET | `/api/logs` | Request/response debug logs |
| GET | `/api/stream` | SSE stream for real-time updates |
| POST | `/api/process` | Trigger pipeline on a save file |
| POST | `/api/upload` | Upload a .sav file directly |
| POST | `/api/ask` | Ask a follow-up question |

## Project Structure

```text
web/                  # React Router frontend (shadcn/ui + Tailwind)
  app/
    routes/           # Page routes + API proxy routes
    components/       # Dashboard panels, chat, state bar
    hooks/            # useSSE hook for real-time updates
src/
  parser/             # Oodle Kraken decompression + uesave
  mapper/             # Game state extraction, Pydantic schemas, alert engine
  strategy/           # Gemini client, DeepEval evaluator, prompts
  guides/             # Steam patch notes + Workshop guide fetcher
  memory/             # Session history (JSON) + request log (SQLite)
  dashboard/          # FastAPI app, routes, SSE streaming
  watcher/            # File watcher + game detector
  config.py           # Centralized env-backed configuration
  pipeline.py         # Orchestrator tying all components together
configs/              # YAML configs (alert rules, prompts)
guides/               # Static markdown strategy guides
```

## Coolify Deployment

1. Create a Docker Compose service pointing to this repo
2. Set `GEMINI_API_KEY` and `SAVE_FOLDER` in Coolify's env vars
3. Set `ENABLE_GAME_DETECTION=true` for local machines
4. Coolify builds + runs both containers, restarts on crash
5. Dashboard always available at `http://localhost:7860`

## Tech Stack

- **React Router** (Remix successor) + shadcn/ui + Tailwind CSS
- **Python 3.12** / FastAPI / Uvicorn
- **Google Gemini** (genai SDK) with context caching
- **DeepEval** for LLM response quality evaluation
- **Docker** with custom build for Oodle Kraken decompressor
- **uesave** for Unreal Engine GVAS parsing
