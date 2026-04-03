# Phase 5: Deploy & Validate

## Status: COMPLETE

The SQL Query Writing Environment is live on Hugging Face Spaces.

**Live URL:** https://huggingface.co/spaces/UtkarshSatav/sql-env
**API URL:** https://UtkarshSatav-sql-env.hf.space

## What Was Done

### 1. Docker Build & Local Test
- Built image: `docker build -t sql-env:latest -f Dockerfile .`
- Ran container: `docker run -p 7860:7860 sql-env:latest`
- Verified all endpoints locally: /health, /reset, /step, /state

### 2. HF Spaces Deployment
- Created Space via `huggingface_hub` Python API
- Uploaded all project files
- Fixed critical issues:
  - `app_port: 8000` → `app_port: 7860` in README frontmatter (HF was routing to wrong port)
  - Removed `base_path: /web` (our app serves from root)
  - Added root `/` endpoint returning HTML (HF needs this to detect app is ready)

### 3. Validation
- `openenv validate` → **[OK] Ready for multi-mode deployment**
- Live endpoint tests all passing:
  - `GET /health` → `{"status":"healthy"}`
  - `POST /reset` → Returns first question with schema
  - `POST /step` → Executes query, returns reward=1.0 for correct SQL
  - `GET /state` → Returns episode_id and step_count

## Pre-Submission Checklist

| Requirement | Status |
|---|---|
| HF Space deploys | PASS — Running at UtkarshSatav/sql-env |
| OpenEnv spec compliance | PASS — openenv validate passes |
| Dockerfile builds | PASS — Docker build + run works locally and on HF |
| Baseline reproduces | PASS — inference.py produces scores across all 3 tasks |
| 3+ tasks with graders | PASS — basic_select, join_aggregate, advanced_analytics |
| Typed models (step/reset/state) | PASS — SQLAction, SQLObservation, State |
| Meaningful reward function | PASS — 4-component partial credit |
| README with docs | PASS — Full documentation with action/observation spaces |
