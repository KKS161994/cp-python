# cp-python

Python practice — competitive-programming-style problems and data-structure implementations.

FastAPI learning lives in a separate folder: `~/Desktop/fastapi-learning/`.

## Layout

```
programs/
  pattern/           printing patterns (squares, triangles)
  *.py               problems and data structures
  rotten_oranges     BFS problem
```

## Running

```bash
python3 programs/<file>.py
```

No external dependencies — standard library only.

---

## Daily work log

Reconstructed from git history and file mtimes; fill in future days as you go.

### 2026-05-05 (Mon) — Day 1
- `hello_world.py` — first commit, sanity check
- `warm_temperatures.py` — daily temperatures / next-warmer-day (monotonic stack)
- `pattern/solid_square.py`, `pattern/right_triangle.py` — warm-up pattern printing

### 2026-05-06 (Tue) — Day 2
- `rotten_oranges` — multi-source BFS on a grid
- `open_map.py` — map / dict practice
- `max_within_k_window.py`, `max_within_k_window_v2.py` — sliding-window maximum (two approaches)
- Revisited `warm_temperatures.py`

### 2026-05-12 (Mon) — FastAPI deep-dive
- Moved to FastAPI track (now in `~/Desktop/fastapi-learning/fastapi/`)
- DI / `Annotated` patterns: `validate_di.py`, `query_annotated_example.py`, `security_annotated_example.py`
- Auth: `authorisation_header.py`, `security_bearer.py`, `security_bearer_v1.py`
- JWT: `jwt_token_example.py`, `jwt_sqlalchemy_example.py`, `jwt_sqlalchemy_async_example.py`
- Back to CP: `streaming_backpressure.py` — backpressure / producer-consumer

### 2026-05-13 (Tue) — Consolidation
- Committed the week's work (`Add Python practice programs and FastAPI learning examples`)
- Scaffolded the standalone FastAPI app under `fastapi/app/` (its own repo)

### 2026-05-14 (Wed) — Data structures day
- `find_median.py` — running median (two-heap pattern)
- `AllOne.py` — LeetCode 432, O(1) increment/decrement/getMin/getMax
- `lru_cache.py`, `lru_cache_v1.py` — LRU cache, two iterations
- `lfu_cache_v2.py`, `lfu_v3.py` — LFU cache, two iterations
- `random.py` — randomized set / sampling practice
- `hash_set.py`, `hash_set_v1.py` — hash set from scratch, two iterations
- Reorganised repo: moved FastAPI + venv out to `~/Desktop/fastapi-learning/`; added this README
- Loose FastAPI examples moved into the fastapi-app repo under `app/examples/`

### YYYY-MM-DD (Day) — <title>
- <bullet>
