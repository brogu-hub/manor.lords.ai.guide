MANOR LORDS

AI Strategic Guide System

Real-Time AI Advisor Powered by Local LLM + Save File Intelligence

You make the moves. AI tells you what to do next.

| Version1.0 | Phase 1Save File Parser | FutureUE4 HTTP Plugin |
| ---------- | ----------------------- | --------------------- |

Executive Summary

This document describes an AI-powered strategic guide system for Manor Lords built across two distinct phases, each designed for a different gameplay mode. Unlike automation systems that control the game on your behalf, this advisor reads your game state, understands your situation, and tells you what to do next — leaving all decisions and movements in your hands.

| DESIGN PHILOSOPHY | You are the Lord. The AI is your Steward. The Steward reads the ledger, analyses the situation, and recommends the next action. You issue the command. This creates a genuinely collaborative experience — AI intelligence augmenting human decision-making rather than replacing it. |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Two Phases, Two Gameplay Modes

| Phase   | Gameplay Mode              | Game Settings                        | Focus                                                                       | Technology                                                     |
| ------- | -------------------------- | ------------------------------------ | --------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Phase 1 | Peaceful economy mode      | No raids / bandit attacks disabled   | City building, economy, population growth, season planning                  | Save file parsing — periodic advice on manual save            |
| Phase 2 | Hard / Extreme combat mode | Bandit attacks + enemy raids enabled | Real-time military alerts, raid response, tactical decisions under pressure | UE4 HTTP plugin — live game state stream, event-driven alerts |

Phase 1 is the foundation. Peaceful mode removes the time pressure of raids and lets you focus on building a prosperous settlement with expert guidance on every economic and city planning decision. Phase 2 adds the military layer — when bandits can attack at any moment, periodic advice from a save file is not enough. You need real-time warnings the instant a raid is detected.

What the System Delivers

| Capability             | Mode         | Description                                                                        | Phase |
| ---------------------- | ------------ | ---------------------------------------------------------------------------------- | ----- |
| Save state parsing     | Peaceful     | Read full game state from .sav: resources, population, season, buildings, approval | 1     |
| Economy analysis       | Peaceful     | LLM advises on build order, trade, worker assignment, food chains                  | 1     |
| City planning advice   | Peaceful     | Prioritised next actions: what to build, where, in what order                      | 1     |
| Seasonal warnings      | Peaceful     | Winter prep, food stockpile targets, firewood before frost                         | 1     |
| Session memory         | Peaceful     | Graphiti learns your playstyle across sessions, personalises advice                | 1     |
| Live game state stream | Hard/Extreme | UE4 HTTP plugin pushes live state every few seconds — no save needed              | 2     |
| Raid detection alert   | Hard/Extreme | Instant alert the moment a bandit raid or enemy attack is detected                 | 2     |
| Combat advisor         | Hard/Extreme | Real-time military recommendations: rally levies, position retinue, terrain choice | 2     |
| Crisis response        | Hard/Extreme | Simultaneous raid + starvation + approval crisis — AI prioritises in real time    | 2     |

Technical Foundation: How Save Files Work

Save File Location and Format

Manor Lords uses Unreal Engine 4's standard save system. Save files are written to a fixed location on Windows:

C:\Users\[Username]\AppData\Local\ManorLords\Saved\SaveGames\

The folder contains autosaves, manual saves, screenshots, and coat of arms files. The game saves in numbered .sav files alongside .png thumbnail previews.

GVAS Binary Format

Unreal Engine saves use the GVAS (Game Variable Archive Save) binary format. This is a well-documented standard format used across hundreds of UE4 games — not proprietary to Manor Lords. It has already been reverse-engineered and has multiple open-source parsers available.

| Layer            | Description                                                                            | Tool                         |
| ---------------- | -------------------------------------------------------------------------------------- | ---------------------------- |
| Binary container | GVAS magic header + optional zlib compression wrapper                                  | Python SavConverter          |
| Property tree    | Hierarchical typed properties: IntProperty, StrProperty, ArrayProperty, StructProperty | Python SavConverter          |
| Game data        | Manor Lords-specific property names and structures within the tree                     | Custom mapper (Phase 1 work) |
| JSON output      | Clean structured JSON ready for LLM consumption                                        | SavConverter + mapper        |

Python SavConverter Library

The SavConverter pip package converts UE4 .sav files to JSON and back with no additional dependencies. This is the core of Phase 1:

pip install SavConverter

from SavConverter import read_sav, sav_to_json

# Read the latest Manor Lords save

props = read_sav('SaveGames/autosave_0.sav')

game_json = sav_to_json(props, string=False)

# game_json now contains the full structured game state

# Next: pass through the Manor Lords mapper to extract

# meaningful game state fields

| KEY FINDING | The .sav format for UE4 games is standardised and well-understood. Multiple open-source tools exist (SavConverter in Python, gvas-rs in Rust, uesave-rs). The Manor Lords-specific work is mapping property names to meaningful game state — a one-time reverse engineering effort, not ongoing infrastructure. |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Save File Update Frequency

| Save type    | Trigger                     | Frequency                         | Suitable for advisor?            |
| ------------ | --------------------------- | --------------------------------- | -------------------------------- |
| Autosave     | Game triggers automatically | Every ~5–10 minutes of game time | Yes — good for strategic advice |
| Manual save  | Player presses Save         | On demand                         | Yes — most accurate snapshot    |
| Quicksave    | Player presses F5           | On demand                         | Yes — fastest trigger           |
| File watcher | System monitors file change | Instant on any save               | Yes — passive, zero effort      |

The file watcher approach is recommended: a Python watchdog monitors the SaveGames folder and triggers the parser + LLM pipeline automatically whenever any save file changes. No manual trigger required — save the game, get advice instantly.

Phase 1: Peaceful Economy Mode

Phase 1 is designed for peaceful or low-threat gameplay — raids and bandit attacks disabled in game settings. Without the urgency of combat, the periodic save-file approach is ideal: save when you want advice, read the recommendations, make your moves. There is no need for real-time monitoring when nothing can attack you mid-build.

| PHASE 1 GAME SETTINGS | Set Manor Lords to No Raids mode or disable bandit camps at map start. This removes all military time pressure and lets you focus entirely on economic development, population growth, and city planning — exactly what Phase 1 is optimised to advise on. |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| NO MOUSE CONTROL | This system is purely advisory in both phases. It reads the game state, analyses it, and produces text recommendations. All gameplay actions are performed by you. The AI never touches the game directly. |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Component Overview

| Component       | Technology                             | Role                                                                           | VRAM    |
| --------------- | -------------------------------------- | ------------------------------------------------------------------------------ | ------- |
| Save watcher    | Python watchdog                        | Monitors SaveGames folder, triggers pipeline on file change                    | 0       |
| GVAS parser     | Python SavConverter                    | Converts .sav binary to raw JSON property tree                                 | 0       |
| State mapper    | Python (custom)                        | Extracts meaningful game state from raw JSON: resources, buildings, population | 0       |
| Strategy engine | Gemini 3.1 Flash-Lite + fallback chain | Analyses game state, generates prioritised recommendations                     | 0 GB    |
| Session memory  | Graphiti + FalkorDB                    | Tracks past decisions, outcomes, player preferences across sessions            | ~512 MB |
| Guide library   | PageIndex                              | Indexed build guides, strategy tips, meta knowledge for LLM context            | ~256 MB |
| Dashboard UI    | FastAPI + HTML                         | Displays recommendations, warnings, session history in browser overlay         | 0       |

Data Flow

| 1 | Player saves game (auto, manual, or quicksave)File change detected instantly by watchdog. Triggers pipeline. Player continues playing — advice arrives in seconds. |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| 2 | GVAS parser reads .sav binarySavConverter converts .sav to raw JSON property tree. Handles decompression and binary parsing automatically. |
| - | ------------------------------------------------------------------------------------------------------------------------------------------ |

| 3 | State mapper extracts game stateCustom mapper reads raw JSON and produces clean structured state: season, year, all resources, population, approval, buildings, ongoing threats. |
| - | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| 4 | Graphiti retrieves session memoryPast decisions, repeated mistakes, player preferences retrieved from knowledge graph to personalise advice. |
| - | -------------------------------------------------------------------------------------------------------------------------------------------- |

| 5 | PageIndex retrieves relevant guide contentBased on current game state (winter approaching, low food, raid warning), retrieves relevant strategy sections from indexed guide library. |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| 6 | Gemini 3.1 Flash-Lite generates strategic recommendationsAPI call with dynamic thinking level. Full context: game state + session memory + guide knowledge → returns prioritised action list, warnings, explanations in under 2 seconds. |
| - | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| 7 | Dashboard displays adviceBrowser overlay shows: top 3 priorities, active warnings, current situation summary, optional deeper analysis on request. |
| - | -------------------------------------------------------------------------------------------------------------------------------------------------- |

The State Mapper: From GVAS to Game Intelligence

The state mapper is the Phase 1 development work — the one-time effort to understand which GVAS property names correspond to which game values in Manor Lords. Once built, it requires no further maintenance unless the game updates its save format.

Target Game State Schema

The mapper produces a clean JSON object that the LLM can reason over directly:

// manor_lords_state.json — output of the mapper

{

  "meta": { "year": 3, "season": "Winter", "day": 14, "game_speed": "paused" },

  "settlement": {

    "name": "Thornfield",

    "approval": 67,

    "population": { "families": 18, "workers": 42, "homeless": 0 },

    "regional_wealth": 85,

    "lord_personal_wealth": 240

  },

  "resources": {

    "food": { "total": 340, "bread": 120, "berries": 80, "meat": 60, "vegetables": 80 },

    "fuel": { "firewood": 45, "charcoal": 0 },

    "construction": { "timber": 28, "planks": 15, "stone": 4, "clay": 0 },

    "clothing": { "leather": 8, "linen": 0 },

    "production": { "iron": 2, "ale": 0, "malt": 0 }

  },

  "buildings": [

    { "type": "LoggingCamp", "workers_assigned": 2, "max_workers": 3 },

    { "type": "Granary", "workers_assigned": 1 },

    { "type": "Church", "radius_coverage": 0.85 }

  ],

  "military": {

    "retinue": { "count": 5, "equipment": "spears" },

    "levies_mobilised": false,

    "bandit_camps_nearby": 2,    // Phase 1: advisory only — no live raid alert

    "active_raid": false          // Phase 2: this triggers instant combat response

  },

  "development_points": 2,

  "alerts": ["LOW_STONE", "NO_CLOTHING_SOURCE"]

}

Mapper Development Strategy

Building the mapper is a discovery process. The approach:

Load the game, take note of a specific value — e.g. food = 340

Save the game, parse the .sav with SavConverter, search the JSON tree for 340

Change the value in game, save again, confirm the property name updates

Map property path to semantic name in the mapper config

Repeat for each game state variable — typically 2–4 hours for full coverage

The mapper config is a YAML file mapping GVAS property paths to semantic field names — no code changes needed when adding new mappings:

# manor_lords_mapper.yaml

mappings:

  food_total: 'SaveGameData.Settlement.Storage.FoodItems.TotalCount'

  approval:   'SaveGameData.Settlement.ApprovalRating.CurrentValue'

  year:       'SaveGameData.GameTime.CurrentYear'

  season:     'SaveGameData.GameTime.CurrentSeason'

  population: 'SaveGameData.Settlement.Population.FamilyCount'

| COMMUNITY OPPORTUNITY | Once the mapper is built and published, the entire Manor Lords community benefits. This is the kind of open-source contribution that could grow into a full modding ecosystem. The mapper config file alone — property paths for every game value — would be immediately useful to modders and researchers. |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

The LLM Strategy Advisor

Primary Model: Gemini 3.1 Flash-Lite

The Manor Lords advisor uses Gemini 3.1 Flash-Lite as its primary model — Google's newest and most cost-efficient production model as of March 2026. It runs entirely via Google's API, consuming zero local GPU VRAM. Manor Lords keeps its full 16GB for Epic quality graphics. The AI has no resource competition with the game at all.

| WHY 3.1 FLASH-LITE AS PRIMARY | Gemini 3.1 Flash-Lite is 2.5x faster than 2.5 Flash, cheaper, and achieves 86.9% on GPQA Diamond benchmarks — excellent strategic reasoning for the price. The Manor Lords advisor is a structured analysis task, not a creative writing task. Flash-Lite is built exactly for this: high-frequency, structured, intelligent extraction. The quality gap versus larger models is negligible for the specific job of reading a game state JSON and producing prioritised recommendations. |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

The Full Model Family: Primary + Fallback Chain

The advisor uses a four-level fallback chain. When the primary model hits its rate limit, the system automatically tries the next model in the chain. Each level is a predecessor in the Gemini family — older, slightly heavier, but same API interface and zero code change required.

| Level      | Model                 | Speed                  | Cost / 1M tokens     | Free RPD                   | Role                           |
| ---------- | --------------------- | ---------------------- | -------------------- | -------------------------- | ------------------------------ |
| Primary    | gemini-3-1-flash-lite | 380 tok/s              | $0.25 in / $1.50 out | Preview — check AI Studio | Default for all requests       |
| Fallback 1 | gemini-3-flash        | 3x faster than 2.5 Pro | $0.50 in / $3.00 out | Preview limit              | When 3.1 Lite hits rate limit  |
| Fallback 2 | gemini-2-5-flash      | Fast                   | $0.30 in / $2.50 out | 250 RPD                    | Stable free tier fallback      |
| Fallback 3 | gemini-2-5-flash-lite | Fastest 2.5 variant    | $0.10 in / $0.40 out | 1000 RPD                   | Last resort — very high quota |

| FREE TIER STRATEGY | Gemini 3.1 Flash-Lite and Gemini 3 Flash are currently in preview — their exact free RPD limits are not yet published and are subject to change. The stable fallback chain is Gemini 2.5 Flash (250 RPD) and Gemini 2.5 Flash-Lite (1000 RPD). In practice, a gaming session generates 30–60 requests. You will almost never reach even the 250 RPD limit, let alone need the 1000 RPD fallback. |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Paid Tier When Ready

When you add billing to your Google Cloud project, Tier 1 activates instantly. The economics for personal gaming use are essentially free:

| Usage pattern               | Requests/month | Est. tokens/request | Monthly cost (3.1 Flash-Lite) |
| --------------------------- | -------------- | ------------------- | ----------------------------- |
| Casual (3 sessions/week)    | ~360 requests  | ~4000 tokens avg    | ~$0.22 / month                |
| Regular (daily sessions)    | ~900 requests  | ~4000 tokens avg    | ~$0.54 / month                |
| Heavy (long daily sessions) | ~1800 requests | ~6000 tokens avg    | ~$1.62 / month                |

Even at heavy usage, Gemini 3.1 Flash-Lite costs under $2 per month for a personal gaming advisor. Tier 1 gives 300 RPM — rate limits become a complete non-issue. The fallback chain becomes unnecessary but stays in the code as resilience.

The Thinking Level Parameter

Gemini 3 family models introduce thinking_level — a parameter controlling how deeply the model reasons before responding. The advisor uses this dynamically based on detected game situation complexity:

| Game situation                                                | Phase             | Thinking level | Why                                                                     |
| ------------------------------------------------------------- | ----------------- | -------------- | ----------------------------------------------------------------------- |
| Routine check — stable settlement, no warnings               | 1 — Peaceful     | MINIMAL        | Fast response, minimum tokens. No complexity to reason over.            |
| Season change approaching, seasonal prep needed               | 1 — Peaceful     | LOW            | Light forward planning. Seasonal advice has a small reasoning benefit.  |
| Multiple resource warnings simultaneously                     | 1 — Peaceful     | MEDIUM         | Competing priorities need structured ranking to avoid wrong first move. |
| New region, Year 3+ strategic pivot, development point choice | 1 — Peaceful     | HIGH           | Long-term consequences justify deep reasoning and extra tokens.         |
| Bandit camp detected nearby                                   | 2 — Hard/Extreme | HIGH           | Military + economic planning needed simultaneously. Full reasoning.     |
| Active raid in progress                                       | 2 — Hard/Extreme | HIGH           | Crisis mode — competing threats, real-time tactical advice required.   |

Configuration

| Parameter           | Value                                  | Notes                                                             |
| ------------------- | -------------------------------------- | ----------------------------------------------------------------- |
| Primary model       | gemini-3-1-flash-lite                  | Model ID in API calls                                             |
| Fallback chain      | 3-flash → 2.5-flash → 2.5-flash-lite | Auto-retry on 429 rate limit error                                |
| Thinking level      | MINIMAL by default                     | Upgraded dynamically based on warnings count + situation          |
| Temperature         | 1.0                                    | Gemini 3 default — do not lower, causes looping on complex tasks |
| Context window      | 1M tokens                              | Entire guide library + game state + session history fits easily   |
| Max output tokens   | 1024                                   | Structured advisor output is compact — no need for more          |
| System prompt style | Expert advisor, not assistant          | Authoritative structured output, not conversational               |

Fallback Implementation

The fallback chain is a simple Python wrapper around the Gemini API client. It tries each model in order on a 429 rate limit error, logs which model was used, and returns the response transparently:

FALLBACK_CHAIN = [

    'gemini-3-1-flash-lite',   # primary — fastest, cheapest

    'gemini-3-flash',           # fallback 1 — Pro-grade reasoning

    'gemini-2.5-flash',         # fallback 2 — stable 250 RPD free

    'gemini-2.5-flash-8b',      # fallback 3 — 1000 RPD free

]

def get_thinking_level(state: dict) -> str:

    warnings = len(state.get('alerts', []))

    year = state['meta']['year']

    if warnings == 0 and year < 3: return 'MINIMAL'

    if warnings <= 1:              return 'LOW'

    if warnings <= 3:              return 'MEDIUM'

    return 'HIGH'

async def call_with_fallback(prompt: str, state: dict) -> str:

    level = get_thinking_level(state)

    for model in FALLBACK_CHAIN:

    try:

    response = await gemini.generate(

    model=model, prompt=prompt,

    thinking_level=level, temperature=1.0

    )

    log(f'Used {model} at thinking level {level}')

    return response

    except RateLimitError:

    continue  # try next model

    raise Exception('All models rate limited')

System Prompt Design

The advisor prompt is designed for strategic clarity — not conversation. Every response follows a strict structure so the dashboard can parse and display it cleanly:

# profiles/manor_lords_advisor.yaml

system_prompt: |

  You are an expert Manor Lords steward. You analyse the lord's

  current settlement state and provide clear, prioritised advice.

  Always respond in this exact structure:

  WARNINGS: [list critical issues requiring immediate attention]

  PRIORITY_1: [single most important action right now]

  PRIORITY_2: [second most important action]

  PRIORITY_3: [third most important action]

  SITUATION: [2-3 sentence assessment of current state]

  NEXT_SEASON: [what to prepare for before next season]

  Be specific. Name exact buildings, quantities, and assignments.

  Reference the player's actual resource numbers in your advice.

  Never be vague. 'Build more food storage' is wrong.

  'Build a second Granary — food at 340 will not last winter' is right.

Sample Advisor Output

Given the example game state JSON shown earlier (Year 3, Winter Day 14, approval 67, food 340):

| WARNINGS    | LOW_STONE: Only 4 stone remaining. Cannot build Manor House. Mine or trade immediately.

| NO_CLOTHING: 0 linen and 8 leather only. Approval will drop when clothing need triggers. |                                                                                                                                                                                                                                              |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PRIORITY 1                                                                               | Assign 1 worker to Stonecutter immediately. You need 25 stone for the Manor House. With 4 currently, assign now — stone takes time.                                                                                                         |
| PRIORITY 2                                                                               | Build a Tannery next to your Storehouse. You have 8 leather unprocessed. Convert to clothing before your 18 families trigger the clothing need in Spring.                                                                                    |
| PRIORITY 3                                                                               | Assign third worker to Logging Camp. Firewood at 45 is borderline for 18 families through winter. Target 80 before Day 30.                                                                                                                   |
| SITUATION                                                                                | Settlement is stable but under-resourced for growth. Approval at 67 is sufficient for slow settler arrival but blocking Level 2 Burgages. Winter food (340) is adequate for current population. Main bottleneck is clothing and stone.       |
| NEXT SEASON                                                                              | Spring Year 3: Plan your first farming field. Check fertility overlay for Emmer wheat. Assign 2 families to farming as soon as ground thaws. Ale production should be next priority after Manor House — approval boost critical for growth. |

Session Memory: The Advisor Learns Your Style

A basic advisor gives the same advice to every player. A good steward learns your preferences, your mistakes, and your playstyle over time. Graphiti provides this session memory — the same knowledge graph used in the Minecraft Gerald system, adapted for Manor Lords strategic data.

What Gets Stored in Graphiti

| Memory type         | Example                                               | How used                                                                           |
| ------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Decisions taken     | Player built Trading Post before Church (session 2)   | Advisor notes economic-first tendency, adjusts recommendations                     |
| Warnings ignored    | Starvation warning ignored 3 times across sessions    | Advisor escalates urgency, adds historical context: 'You have ignored this before' |
| Successful patterns | Always builds Sawpit immediately — efficient         | Advisor reinforces this, stops recommending it as priority                         |
| Preferences         | Player never uses sheep farming                       | Advisor stops suggesting it, recommends alternative clothing sources               |
| Region patterns     | Player consistently builds near rivers                | Advisor notes good water access, adjusts well placement advice                     |
| Difficulty moments  | Player always struggles with winter Year 1            | Advisor adds extra winter prep warnings in Year 1 specifically                     |
| Development choices | Player always takes Pond Management perk if available | Advisor mentions fish pond quality at region selection time                        |

Personalisation Examples

The difference between a generic advisor and a personalised one:

| Situation          | Generic advice                                           | Personalised (with Graphiti)                                                                                               |
| ------------------ | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Low food Winter Y1 | You have low food. Consider building a food gatherer.    | CRITICAL: Food at 180. You starved in this exact situation in sessions 2 and 4. Build Berry Gatherer NOW — not next turn. |
| Clothing needed    | Build a sheep farm or flax farm for clothing production. | You never use sheep farms — add goat pens to 3 Burgages instead. Faster and fits your building style.                     |

Guide Library: PageIndex as Strategic Knowledge Base

PageIndex indexes curated game guides so the LLM can retrieve relevant strategy sections based on the current game situation. This means the advisor doesn't just know the game from training data — it can reason over structured, up-to-date expert knowledge specific to the current situation.

PageIndex Document Library

| Document                  | Contents                                                                                              | Triggered by                                               |
| ------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Build order guide         | Optimal first 10–15 buildings for different starts, sequencing rationale                             | Early game, Year 1–2                                      |
| Winter survival guide     | Food, firewood, clothing requirements per family, stockpile targets                                   | Autumn or Winter season detected                           |
| Economy and trade guide   | When to build Trading Post, what to export, import priorities                                         | Low regional wealth or trade post missing                  |
| Military guide — Phase 2 | Retinue build order, levy timing, bandit camp attack tactics, terrain advantage, Manor House priority | Phase 2 only — bandit camps detected, raid warning active |
| Approval guide            | Church coverage, marketplace stalls, food variety bonuses, ale effect                                 | Approval below 60%                                         |
| Farming guide             | Fertility overlay use, crop rotation, windmill and bakery chain                                       | Farming buildings present or needed                        |
| Burgages upgrade guide    | Level 1 → 2 → 3 requirements, clothing, food variety, church access checklist                       | Burgages at Level 1 for too long                           |
| Development perks guide   | When to pick each perk, fish pond priority, plough vs sheep decision                                  | Development points available                               |
| Region expansion guide    | Influence requirements, which resource regions to prioritise, specialisation                          | Year 3+ or influence building                              |
| Patch notes               | Latest game version changes to mechanics, balance updates                                             | Always included as context                                 |

| WHY NOT JUST USE LLM TRAINING DATA | The game is in Early Access — it updates frequently. Patch notes from 2025 may change food spoilage, trade mechanics, or building costs. PageIndex lets the advisor stay current by simply adding new documents, without fine-tuning the model. It also lets you add your own custom strategy notes specific to your playstyle. |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

The Advisory Dashboard

The dashboard is a browser-based overlay that runs alongside the game. It displays the LLM's advice in a clean, scannable format — designed to be read in seconds while playing, not paragraphs to study.

Dashboard Layout

Five panels, all visible at once, all updating on every save:

| Panel             | Contents                                                                                                                                          | Update trigger                          |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| Warnings          | Phase 1: starvation risk, winter underprepared, approval below 50%, low stone/clothing. Phase 2 adds: RAID ACTIVE, ENEMY APPROACHING, RETINUE LOW | Every parse / instant on Phase 2 events |
| Top 3 Priorities  | Three specific actions with explanations. Numbered, scannable, actionable.                                                                        | Every parse                             |
| Situation Summary | 2–3 sentence current state assessment. Season, approval, main bottleneck.                                                                        | Every parse                             |
| Next Season Prep  | What to do before the season changes. Specific targets: build X, stockpile Y units of Z.                                                          | Every parse                             |
| Session History   | Last 5 saves — what changed, what was recommended, what you actually built. Tracks your decisions.                                               | Cumulative                              |

Dashboard Technology Stack

| Component         | Technology               | Notes                                                     |
| ----------------- | ------------------------ | --------------------------------------------------------- |
| Backend API       | FastAPI (Python)         | Serves game state and LLM advice via REST endpoints       |
| Frontend          | Plain HTML + JavaScript  | Single page, no framework, loads instantly                |
| Real-time updates | Server-sent events (SSE) | Dashboard updates automatically when new advice generated |
| File watcher      | Python watchdog          | Monitors SaveGames folder, triggers pipeline on change    |
| Hosting           | localhost:8080           | Open in browser, position beside game window              |

Usage Flow

| 1 | Start the advisor servicedocker compose up — starts FalkorDB, Graphiti, FastAPI, PageIndex. Set GEMINI_API_KEY in .env. Primary model is Gemini 3.1 Flash-Lite with automatic fallback. Open localhost:8080 in browser. |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| 2 | Launch Manor Lords and load your savePlay normally. The advisor is passive until you save. |
| - | ------------------------------------------------------------------------------------------ |

| 3 | Save the game (auto, manual, or F5 quicksave)Watchdog detects the file change instantly. Parse + LLM advice generated in 3–8 seconds. |
| - | -------------------------------------------------------------------------------------------------------------------------------------- |

| 4 | Glance at dashboardRead the top priority and warnings. Make the move yourself. Save again when ready for next advice. |
| - | --------------------------------------------------------------------------------------------------------------------- |

| 5 | Ask follow-up questions (optional)Dashboard includes a text input for follow-up questions. Phase 1: 'Should I build a Trading Post or Church first?' Phase 2: 'Raid coming from the east — should I rally levies or rely on retinue?' — LLM answers with full current game state context. |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Phase 2: Hard / Extreme Combat Mode

Phase 2 is built for a fundamentally different gameplay challenge. When you enable hard or extreme difficulty with bandit attacks and enemy raids active, the periodic save-file approach of Phase 1 completely breaks down. A raid does not wait for you to save the game. You need the AI watching the game state continuously and alerting you the instant a threat appears.

| PHASE 2 GAME SETTINGS | Enable bandit camps and raider difficulty in Manor Lords settings. Hard mode adds periodic bandit raids that require military response. Extreme mode adds aggressive enemy lords who will actively contest your territory. Both require real-time awareness that Phase 1 cannot provide. |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| WHY PHASE 1 FAILS IN COMBAT MODE | Raids happen in real time. If a Creeper — sorry, a bandit raid — starts while you are building a Granary, you have seconds to respond, not minutes. The save file only updates when you save. By the time you save, read advice, and act, your settlement may already be burning. Phase 2 solves this with a live game state stream and instant event-driven alerts. |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Phase 2 Architecture: Real-Time Combat Intelligence

| Component        | Technology                      | How it works                                                                                                |
| ---------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Blueprint plugin | UE4 Blueprint + C++ module      | Runs inside the game process, reads game state from UE4 objects directly                                    |
| HTTP server      | libmicrohttpd via UE4 plugin    | Exposes localhost:9090/state endpoint returning live JSON                                                   |
| State exporter   | Blueprint nodes reading UActors | Directly queries Settlement actor, Resource manager, Population system                                      |
| Event emitter    | UE4 delegate bindings           | Fires instant HTTP events on: raid start, enemy detected, retinue casualties, approval collapse, starvation |
| Phase 1 adapter  | Python bridge                   | Phase 1 dashboard connects to localhost:9090 instead of parsing .sav files                                  |

Phase 2 Development Path

| Step | Work                                                                                                 | Difficulty                                | Time       |
| ---- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------- | ---------- |
| 1    | Install UE4.27 matching Manor Lords version                                                          | Low                                       | 30 min     |
| 2    | Create empty plugin project, verify it loads in game                                                 | Medium                                    | 2–4 hours |
| 3    | Find key Blueprint actors (Settlement, ResourceManager, PopulationSystem)                            | High — requires game reverse engineering | 1–2 weeks |
| 4    | Read values from actors, output to log to verify                                                     | Medium                                    | 2–3 days  |
| 5    | Add HTTP server to plugin, expose /state endpoint                                                    | Medium                                    | 1–2 days  |
| 6    | Add combat event hooks: raid_start, enemy_detected, retinue_low, levy_needed, settlement_burning     | Medium                                    | 2–3 days  |
| 7    | Add combat panel to dashboard: raid alerts, military recommendations, retinue status, levy countdown | Low                                       | 4–6 hours |

| COMMUNITY POTENTIAL | A working Manor Lords state API would be the foundation for a full modding ecosystem — not just AI advisors but data analytics, streaming overlays, Discord bots, accessibility tools, and more. Publishing it open-source would attract contributors who could accelerate development significantly. |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

Implementation Roadmap

Phase 1: Peaceful Economy Advisor

| Task                       | Description                                                                                          | Time       |
| -------------------------- | ---------------------------------------------------------------------------------------------------- | ---------- |
| Environment setup          | Docker Compose with FalkorDB, Graphiti, FastAPI. Add GEMINI_API_KEY and build fallback chain config. | 1 hour     |
| SavConverter integration   | Install, test parsing on a real Manor Lords .sav file                                                | 1 hour     |
| State mapper v1            | Map key properties: resources, population, season, approval, buildings                               | 4–6 hours |
| File watcher               | Python watchdog monitors SaveGames, triggers pipeline on change                                      | 1 hour     |
| Advisor prompt engineering | Tune system prompt for structured output, test on multiple game states                               | 2–4 hours |
| Dashboard v1               | FastAPI + HTML overlay showing warnings and top 3 priorities                                         | 3–4 hours |
| Graphiti session memory    | Connect session tracking, personalisation after 3–5 play sessions                                   | 2–3 hours |
| PageIndex guide library    | Index the Manor Lords guide document + build order + strategy tips                                   | 1–2 hours |

Phase 2: Hard/Extreme Combat Mode — UE4 Live Plugin

| Task                      | Description                                                                              | Time       |
| ------------------------- | ---------------------------------------------------------------------------------------- | ---------- |
| UE4.27 setup              | Install engine, create plugin project, verify loads in game                              | Half day   |
| Actor reverse engineering | Locate Settlement, Resource, Population blueprint actors                                 | 1–2 weeks |
| State reader              | Blueprint nodes reading live values, verified against .sav ground truth                  | 3–5 days  |
| HTTP server               | Embed microHTTP server, expose /state and /events endpoints                              | 2–3 days  |
| Event system              | Bind to combat events: raid start, enemy approach, retinue casualties, settlement damage | 2–3 days  |
| Dashboard upgrade         | Switch from .sav polling to HTTP streaming, add real-time alerts                         | 1 day      |

Final Summary

The Manor Lords AI Strategic Guide System transforms how you play the game — not by playing it for you, but by making you a significantly better player through expert real-time analysis of your specific situation.

| Layer            | Tool                                   | Role                                                         | Phase |
| ---------------- | -------------------------------------- | ------------------------------------------------------------ | ----- |
| Game state input | GVAS parser + State mapper             | Reads save file → structured JSON of all game values        | 1     |
| Strategy engine  | Gemini 3.1 Flash-Lite + fallback chain | Analyses state → prioritised recommendations + warnings     | 1     |
| Session memory   | Graphiti + FalkorDB                    | Learns your playstyle, mistakes, preferences across sessions | 1     |
| Knowledge base   | PageIndex                              | Indexed guides, tips, patch notes for LLM context retrieval  | 1     |
| Advisory UI      | FastAPI + HTML overlay                 | Displays advice cleanly alongside the game                   | 1     |
| Live state       | UE4 Blueprint HTTP plugin              | Eliminates need to save — live game state stream            | 2     |

| BOTTOM LINE | Phase 1 requires zero game modification, uses existing open-source tools, and delivers genuine strategic value in a weekend of engineering. Phase 2 is a longer project that adds real-time capability. Start with Phase 1 — the save-file approach is already powerful enough to dramatically improve your Manor Lords play. |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

Manor Lords AI Strategic Guide System — Architecture Report v1.0

You are the Lord  •  AI is your Steward  •  Every decision is yours

* 
* [•••]()
* 
* Go to[ ] Page
