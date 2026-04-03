# Phase 4: Inference Script & Docker

## What We Built

Phase 4 delivers the two remaining mandatory submission components:
1. **`inference.py`** — baseline inference script using OpenAI client
2. **`Dockerfile`** — container for deploying to HF Spaces

## Components

### 1. Inference Script (`inference.py`)

The MANDATORY baseline script that runs an LLM agent against all 3 tasks.

**Configuration (via environment variables):**

| Variable | Default | Description |
|---|---|---|
| `HF_TOKEN` / `API_KEY` | (required) | API key for the LLM provider |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model to use |

**How it works:**
1. Creates an OpenAI client pointing at HF Inference API
2. For each task (basic_select, join_aggregate, advanced_analytics):
   - Creates a local `SQLEnvironment` instance
   - Calls `reset()` to get the first question + schema
   - Loops up to 8 steps per task:
     - Sends schema + question + previous feedback to the LLM
     - LLM returns a SQL query
     - Environment grades the query and returns reward
     - On retry, includes previous result and feedback in the prompt
   - Emits [START]/[STEP]/[END] to stdout

**STDOUT format (exactly as specified by hackathon):**
```
[START] task=basic_select env=sql_env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC reward=1.00 done=false error=null
[STEP] step=2 action=SELECT name, price FROM products WHERE category = 'Electronics'... reward=0.80 done=false error=null
...
[END] success=true steps=8 score=0.750 rewards=1.00,0.80,...
```

**LLM prompting strategy:**
- System prompt: expert SQL writer, SQLite-compatible, SELECT-only
- First attempt: schema + question
- Retries: adds previous result, error, and grader feedback
- Temperature: 0.3 (low for deterministic SQL)
- Max tokens: 512 (enough for complex queries)

**Score calculation:**
- Per-task score = sum(rewards) / total_questions (normalized to [0, 1])
- Success threshold: 0.1

### 2. Dockerfile

Simple single-stage build for HF Spaces deployment:

```dockerfile
FROM python:3.11-slim
# Install deps, copy code, expose port 7860, run uvicorn
```

**Key decisions:**
- **Port 7860**: HF Spaces default (not 8000)
- **python:3.11-slim**: Lightweight, has SQLite built-in
- **Single stage**: Simpler than the scaffold's multi-stage openenv-base approach
- **Health check**: Polls /health every 30s

### 3. Updated `openenv.yaml`

Updated port to 7860 for HF Spaces compatibility.

## Requirements From You

1. **HF_TOKEN** — Set as environment variable (confirmed working)
2. **Docker** — **NOT INSTALLED YET**. Needed for:
   - Testing `docker build` + `docker run` locally
   - `openenv build` command
   - Install from: https://docs.docker.com/desktop/install/mac-install/

## Running the Inference Script

```bash
# Set your token (if not already in shell)
export HF_TOKEN="hf_your_token_here"

# Run against all 3 tasks
cd /Users/utkarsh/Scaller\ Hackethon/sql_env
python3.11 inference.py
```

## Testing Docker (after Docker Desktop is installed)

```bash
# Build
docker build -t sql-env:latest -f Dockerfile .

# Run
docker run -p 7860:7860 sql-env:latest

# Test in another terminal
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{}'
curl http://localhost:7860/health
```

## Test Results

### Inference Format Tests (8/8 passing)

| Test | Status |
|---|---|
| [START] format | PASS |
| [STEP] format | PASS |
| [STEP] with error | PASS |
| [END] format (success) | PASS |
| [END] format (failure) | PASS |
| Local episode run | PASS |
| All 3 tasks locally | PASS |
| Multiline action sanitized | PASS |

### LLM Inference Run

Run `python3.11 inference.py` in your terminal with `$HF_TOKEN` set to see
baseline scores. Expected ranges:

| Task | Expected Score |
|---|---|
| basic_select | 0.60 - 0.90 |
| join_aggregate | 0.35 - 0.65 |
| advanced_analytics | 0.10 - 0.40 |

## Files Created/Modified

| File | Action | Purpose |
|---|---|---|
| `inference.py` | Created | Mandatory baseline inference script |
| `Dockerfile` | Created | HF Spaces deployment container (root level) |
| `openenv.yaml` | Updated | Port 7860 for HF Spaces |
| `server/requirements.txt` | Updated | Added openai dependency |
| `tests/test_inference.py` | Created | 8 tests for inference format |
| `PHASE3.md` | Created | Documents Phase 3 (completed in Phase 2) |
| `PHASE4.md` | Created | This file |

## What's Next (Phase 5)

1. Install Docker Desktop
2. Test `docker build` + `docker run` locally
3. Deploy to HF Spaces via `openenv push`
4. Run validation script
5. Submit
