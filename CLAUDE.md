# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the server (then open http://127.0.0.1:8000)
uvicorn app:app --host 127.0.0.1 --port 8000

# Unit tests (no server needed) — 23 tests
python run_tests.py                # wraps pytest with -v --tb=short
python -m pytest tests/

# Single test
python -m pytest tests/test_scoring.py::TestScoreCost::test_score_in_valid_range

# Smoke test (auto-starts server) — 35 tests
python smoke_test.py
```

Dependencies: `pip install -r requirements.txt` plus `pytest` for tests. Python 3.10+ (uses `list[...]` / tuple generics). This is a Windows dev environment with no git repository.

## Architecture

A FastAPI travel-recommendation service. Request flow: `app.py` → `TravelRecommender.recommend()` → cache → JSON response.

**Synchronous-then-background enrichment is the central pattern.** `_get()` in `app.py` computes scores synchronously, caches the result, returns immediately, then spawns **four daemon threads** (`_enrich_ai`, `_enrich_weather`, `_track_results`, `_warn_weather`) that fetch slow external data and **re-`set` the same cache key in place**. Consequences to keep in mind:
- The **first** API response for a query lacks `ai_blurb`, real `weather_detail`, and weather `warnings`. They appear on the **next** (cache-hit) request once enrichment finishes.
- Cache TTL is 300s; enrichment writes also use 300s. Enrichment runs are best-effort and swallow errors to `logger`.

**Scoring engine** (`travel_recommender.py`) is the core. `recommend()` scores every destination on 5 dimensions (cost / route / review / weather / preference), each 1–5, combined with weights from `_adjust_weights()`, then `_diversify()` applies MMR (penalizes repeated `dest_type`) to pick the top 5.
- Currently **126 destinations** (58 original + 68 POI-aggregated domestic cities from `data/enriched_ai.json`). New destinations have IDs 62-129.
- `_adjust_weights()` mutates a base weight dict based on budget, season, traveler type, trip length, preferences, and region, then **renormalizes to sum 1.0**. When adding a weight rule, you don't need to keep the sum balanced — normalization handles it.
- **Cost fields are season-indexed tuples** `(off, mid, peak)`. `_season_index(month)` → 0/1/2 selects the slot. Months map: off `[1,2,3,11,12]`, mid `[4,5,9,10]`, peak `[6,7,8]`.
- `score_weather` / `_get_weather_detail` use a fast latitude+month estimate by default; real Open-Meteo data only overrides it via background enrichment.

**Destination data & a deliberate lazy import.** The `Destination` dataclass is defined in `travel_recommender.py`. `destinations_data.py` imports `Destination` from it, and `load_destinations()` lazily imports `load_all` from `destinations_data` *inside the function* to break the circular import — keep that import local. To add a destination, append to `load_all()` in `destinations_data.py` and add its Chinese name to `CN_NAMES` in `zh_names.py`. Ratings in seed data are overridden at load time from `reviews.db` via `review_seed.get_aggregated_rating()` when available.

**Graceful degradation everywhere.** Optional services (`transport`, `weather_service`, review DB) are wrapped in `try/import` with `_HAS_*` flags and fall back to hardcoded estimates. External APIs (Open-Meteo, AMAP geocode, exchange-rate) all have offline/estimate fallbacks. Preserve this — never assume an external call succeeds.

**Caching layer** (`cache_manager.py`): a single `CacheManager` class instantiated as `result_cache` (+ weather/geocode caches) with per-entry TTL and LRU eviction; `run_periodic_cleanup()` sweeps every 5 min. Some services also keep their own file caches in `.ai_cache/`, `.weather_cache/`, `.transport_cache/`.

**Persistence**: `reviews.db` (SQLite) holds `destinations`, `reviews`, `review_details`, `feedback*`, and `flight_prices` / `flight_price_history` / `flight_alerts`. `flight_tracker.py` records prices and drives low-price alerts; `/api/flight/trend` synthesizes a 30-day series when real history has <3 points.

**Frontend**: static SPA in `static/` (`index.html` + `js/app.js` + `js/map.js`), mounted at `/js`, zero external CDNs (must work behind the GFW), AMap for maps. There is **no build step** — edit the files directly.

## Repository conventions

- **`scripts/` data pipeline scripts** (`crawl_*.py`, `enrich_descriptions.py`, `merge_poi_data.py`) are reusable data collection/enrichment tools.
- **One-off debug scripts** (`fix_*.py`, `check_*.py`, `find_*.py`, `remove_*.py`, etc.) have been archived to `scripts/archive/`. They're kept for reference but should NOT be re-run or treated as application code.
- **`scripts/archive/`** holds 40 historical one-off scripts that were run once during development. If you need to understand how a particular fix was done, check there.
- API keys are currently hardcoded (`ai_writer.py` DeepSeek key, `app.py` AMAP key/secret). If you touch these files, move them to environment variables rather than copying the literals.
