# Manor Lords AI Advisor

AI-powered strategic advisor for [Manor Lords](https://store.steampowered.com/app/1363080/Manor_Lords/) that reads your save files and provides real-time, context-aware counsel through a medieval-themed web dashboard.

## How It Works

```
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
Dashboard (SSE)
```

1. **Parse** -- Decompresses Manor Lords `.sav` files (Oodle Kraken) and converts binary GVAS to JSON via `uesave`
2. **Map** -- Extracts resources, population, buildings, and metadata into typed Pydantic models
3. **Alert** -- Evaluates YAML-driven threshold rules (starvation, fuel shortage, low approval)
4. **Advise** -- Sends game state + guide context to Gemini with auto-detected latest flash model
5. **Evaluate** -- DeepEval scores response quality; auto-retries with correction prompts on failure
6. **Deliver** -- Streams results to the web dashboard via Server-Sent Events

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
PRIMARY_MODEL=auto              # Auto-detect latest Gemini flash model
FALLBACK_MODEL=gemini-2.5-flash
DASHBOARD_PORT=8080
MAX_EVAL_RETRIES=2              # DeepEval retry attempts
EVAL_THRESHOLD=0.6              # Quality score threshold (0-1)
CACHE_TTL_SECONDS=1800          # Gemini context cache (30 min)
WORKSHOP_GUIDE_IDS=3427105626   # Steam Workshop guide IDs (comma-separated)
SESSION_MAX_ENTRIES=10
DEBOUNCE_SECONDS=2.0
```

### Run

```bash
docker compose up -d --build
```

Open **http://localhost:8080** -- click "Analyse Save" to process your latest save.

## Features

### Save Parsing
- Oodle Kraken decompression of Manor Lords binary saves
- `uesave` CLI converts GVAS to JSON
- Extracts 50+ resource types, building counts, worker assignments, population stats

### AI Strategy Engine
- **Auto model detection** -- queries Gemini API for the latest flash model
- **Fallback chain** -- primary model -> fallback on rate limit
- **Context caching** -- Gemini explicit cache for system prompt + guides (~90% token cost reduction)
- **Extended thinking** -- dynamic thinking budget based on game complexity
- **Structured output** -- Warnings, 3 priorities, situation summary, next season prep

### DeepEval Self-Healing
Three LLM-as-judge metrics evaluate every response:

| Metric | What it checks | Threshold |
|--------|---------------|-----------|
| Format compliance | All required sections present with substance | 0.7 |
| Specificity | References actual numbers, buildings, counts | 0.6 |
| State relevance | Addresses critical alerts (food/fuel/approval) | 0.6 |

Failed evaluations trigger automatic retries with correction prompts injected into the next attempt. Max 3 total attempts per request.

### Knowledge Context
- **Static guides** -- Markdown files covering build orders, economy, winter survival, approval
- **Steam patch notes** -- Fetched from ISteamNews API (no key needed)
- **Workshop guides** -- Scraped from Steam Community by configurable guide IDs
- **Session memory** -- Previous advice injected for continuity

### Web Dashboard
- Medieval-themed dark UI matching the game's aesthetic
- Save file selector dropdown
- Real-time state bar (year, season, families, food, approval, alerts)
- Advice panels: Warnings, Priorities, Situation, Next Season
- Follow-up chat for conversational questions about your game state
- Background processing with SSE streaming (no page refresh needed)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard UI |
| GET | `/api/health` | Service health check |
| GET | `/api/state` | Current parsed game state |
| GET | `/api/advice` | Latest generated advice |
| GET | `/api/saves` | List available save files |
| GET | `/api/history` | Session advice history |
| GET | `/api/logs` | Request/response debug logs |
| GET | `/api/stream` | SSE stream for real-time updates |
| POST | `/api/process` | Trigger pipeline on a save file |
| POST | `/api/ask` | Ask a follow-up question |

## Project Structure

```
src/
  parser/           # Oodle Kraken decompression + uesave
  mapper/           # Game state extraction, Pydantic schemas, alert engine
  strategy/         # Gemini client, DeepEval evaluator, prompts, response parser
  guides/           # Steam patch notes + Workshop guide fetcher
  memory/           # Session history (JSON) + request log (SQLite)
  dashboard/        # FastAPI app, routes, SSE streaming
  watcher/          # Watchdog file monitor with debounce
  config.py         # Centralized env-backed configuration
  pipeline.py       # Orchestrator tying all components together
configs/            # YAML configs (alert rules, prompts, mapper)
guides/             # Static markdown strategy guides
static/             # Dashboard HTML/CSS/JS
```

## Auto-Watch Mode

The file watcher automatically processes saves when Manor Lords writes to disk. Save your game in-game and the dashboard updates within seconds.

## Tech Stack

- **Python 3.12** / FastAPI / Uvicorn
- **Google Gemini** (genai SDK) with context caching
- **DeepEval** for LLM response quality evaluation
- **Docker** with custom build for Oodle Kraken decompressor
- **uesave** for Unreal Engine GVAS parsing
