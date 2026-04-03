---
title: SQLEnv - SQL Query Writing Environment
emoji: 🗃️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
tags:
  - openenv
---

# SQLEnv — SQL Query Writing Environment for AI Agents

An OpenEnv-compatible reinforcement learning environment where AI agents learn to write correct SQL queries from natural language questions. Built on a realistic e-commerce database with deterministic, partial-credit grading across 3 difficulty levels.

## Why This Environment Matters

**Text-to-SQL is a real-world task** performed by millions of data analysts, engineers, and business users daily. Natural language interfaces to databases are a $2B+ market (Tableau Ask Data, ThoughtSpot, etc.), yet there is no standardized RL benchmark for training and evaluating text-to-SQL agents in the OpenEnv ecosystem.

SQLEnv fills this gap by providing:
- A **realistic domain** (e-commerce) that any evaluator can understand
- **Deterministic grading** — same query always produces the same score
- **Rich reward signal** — not just pass/fail, but 4-component partial credit
- **Meaningful difficulty progression** — from simple WHERE clauses to window functions
- **Immediate practical value** — can be used to train/evaluate text-to-SQL copilots

**Who benefits:** AI/ML researchers training agents, data teams evaluating LLM SQL capability, educators teaching SQL with automated grading, and enterprises building natural language BI tools.

## Interactive Demo

Visit the **[Live Space](https://huggingface.co/spaces/UtkarshSatav/sql-env)** to try the environment directly in your browser:
- Select a difficulty level (easy / medium / hard)
- Read the natural language question
- Write SQL queries and get instant graded feedback
- See color-coded rewards and visual progress tracking

## Environment Design

### Episode Flow

```
Agent                          Environment
  |                                |
  |-------- reset() ------------->|  Initialize DB, load task, return Q1
  |<------- observation ----------|  Schema + question + 0 reward
  |                                |
  |--- step(SQLAction(query)) --->|  Execute SQL, grade against ground truth
  |<------- observation ----------|  Result + reward + feedback
  |                                |
  |  (retry or next question)     |  Move on after perfect score or max attempts
  |                                |
  |<------- done=true ------------|  All 5 questions answered
```

Each episode consists of 5 questions. The agent gets multiple attempts per question (3 for easy, 4 for medium, 5 for hard). A small step penalty (-0.02 per retry) encourages efficiency.

### Action Space

The agent submits a single SQL SELECT query:

```json
{
  "action": {
    "query": "SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC"
  }
}
```

- Only SELECT statements are allowed (INSERT/UPDATE/DELETE/DROP are blocked)
- Queries execute against an in-memory SQLite database
- The agent sees the full database schema in every observation

### Observation Space

After each step, the agent receives:

```json
{
  "observation": {
    "task_name": "basic_select",
    "question": "Find the names and ages of all customers older than 30, sorted by age from highest to lowest.",
    "schema_description": "=== DATABASE SCHEMA ===\n\nTABLE: customers -- Customer information\n  id INTEGER PRIMARY KEY\n  name TEXT NOT NULL\n  ...",
    "query_result": "name         | age\n--------------+----\nSuresh Menon | 50\nKavita Joshi | 45\n...",
    "error": "",
    "steps_remaining": 2,
    "question_index": 1,
    "total_questions": 5
  },
  "reward": 1.0,
  "done": false
}
```

Key fields:
- `question` — Natural language question to answer with SQL
- `schema_description` — Full database schema with sample data and relationships
- `query_result` — Formatted table output of the executed query (or error message)
- `error` — SQL error string if query failed, empty otherwise
- `steps_remaining` — Attempts left for this question
- `metadata.feedback` — Human-readable explanation of what was right/wrong

## Tasks (3 Difficulty Levels)

### Task 1: `basic_select` (Easy)
Simple SELECT queries with WHERE, ORDER BY, LIMIT, COUNT.

**Example questions:**
- "Find the names and ages of all customers older than 30, sorted by age descending"
- "List all products in the Electronics category, sorted by price descending"
- "How many orders have the status shipped?"

**Max attempts per question:** 3

### Task 2: `join_aggregate` (Medium)
JOIN queries with GROUP BY, HAVING, and aggregate functions.

**Example questions:**
- "What is the average order total for each customer?"
- "Which products have been ordered more than 2 times in total quantity?"
- "List all customers who have never placed an order"

**Max attempts per question:** 4

### Task 3: `advanced_analytics` (Hard)
Subqueries, CTEs, window functions, and complex multi-table analytics.

**Example questions:**
- "Find all customers whose total spending exceeds the average customer spending"
- "Rank all products by revenue within each category using RANK()"
- "Calculate month-over-month growth in order count using LAG()"

**Max attempts per question:** 5

## Reward Function

The reward is **NOT binary**. It provides rich gradient signal across the full trajectory using 4 weighted components:

```
Total Reward = 0.1 × syntax + 0.2 × columns + 0.3 × rows + 0.4 × exact
```

| Component | Weight | Score Range | What It Measures |
|---|---|---|---|
| **Syntax** | 0.1 | 0 or 1 | Query parses and executes without SQL error |
| **Columns** | 0.2 | 0.0–1.0 | Fraction of expected column names present in result |
| **Rows** | 0.3 | 0.0–1.0 | Fraction of expected rows matching (position-aware for ordered queries) |
| **Exact** | 0.4 | 0, 0.5, or 1 | Full result set matches ground truth (0.5 if extra rows) |

**Score examples:**

| Scenario | Reward | Breakdown |
|---|---|---|
| Syntax error (`SELEC * FORM`) | 0.00 | All components zero |
| Valid SQL, wrong columns | 0.10 | Syntax only |
| Right columns, partial rows | 0.40 | Syntax + columns + partial rows |
| Right columns, all rows, extra rows | 0.80 | Syntax + columns + rows + partial exact |
| Perfect match | 1.00 | All components maximum |

**Additional mechanics:**
- **Step penalty:** -0.02 per retry attempt (encourages getting it right the first time)
- **Deterministic:** Same query always produces the same score
- **Handles edge cases:** NULL values, float tolerance (±0.01), column reordering

## Database

Realistic e-commerce database with 5 interconnected tables:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  customers   │    │   orders     │    │  products    │
│  (20 rows)   │───<│  (30 rows)   │    │  (15 rows)   │
│  name, email │    │  order_date  │    │  name, price │
│  age, city   │    │  status      │    │  category    │
└──────────────┘    └──────────────┘    └──────────────┘
                           │
                    ┌──────────────┐    ┌──────────────┐
                    │ order_items  │───>│   reviews    │
                    │  (46 rows)   │    │  (25 rows)   │
                    │  quantity    │    │  rating 1-5  │
                    └──────────────┘    └──────────────┘
```

**Key data characteristics:**
- 4 product categories: Electronics, Clothing, Books, Home
- 4 order statuses: pending, shipped, delivered, cancelled
- 7 cities across India
- 2 customers with no orders (for LEFT JOIN / NOT IN queries)
- 5 customers spanning 3+ product categories (for complex analytics)
- Prices in INR, dates in ISO format

All data is **deterministic** — seeded identically on every `reset()`.

## Baseline Scores

Tested with **Llama 3.3 70B** (via Groq, temperature=0.3):

| Task | Score | Steps | Notes |
|---|---|---|---|
| `basic_select` | **1.000** | 6 | Solved all 5 questions, 1 retry on Q3 |
| `join_aggregate` | **1.000** | 8 | Used all 8 steps, retried Q2 multiple times |
| `advanced_analytics` | **0.969** | 8 | Near-perfect, retries on RANK() and LAG() queries |

Also tested with **Qwen 2.5 72B** (via HuggingFace):

| Task | Score | Notes |
|---|---|---|
| `basic_select` | **1.000** | Perfect |
| `join_aggregate` | **0.967** | Near-perfect |
| `advanced_analytics` | **0.623** | Partial (API credits ran out mid-task) |

These scores demonstrate:
- Easy task is solvable by current LLMs (validates environment works)
- Hard task challenges even 70B models (meaningful benchmark)
- Scores vary across runs and models (not a constant grader)

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Interactive Gradio playground |
| `/health` | GET | Health check → `{"status": "healthy"}` |
| `/reset` | POST | Reset environment, returns initial observation |
| `/step` | POST | Submit SQL query, returns graded observation |
| `/state` | GET | Current episode state (episode_id, step_count) |
| `/schema` | GET | Action/observation JSON schemas |
| `/docs` | GET | Interactive Swagger API documentation |
| `/ws` | WS | WebSocket for persistent sessions |

## Setup & Usage

### Quick Start (Local)

```bash
git clone https://github.com/UtkarshSatav/Scaler-Hackathon-SQL.env-.git
cd Scaler-Hackathon-SQL.env-
pip install openenv-core[core] fastapi uvicorn gradio openai
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t sql-env:latest -f Dockerfile .
docker run -p 7860:7860 sql-env:latest
```

### Using the Client

```python
from client import SQLEnvClient
from models import SQLAction

with SQLEnvClient(base_url="http://localhost:7860") as env:
    result = env.reset()
    print(result.observation.question)
    
    result = env.step(SQLAction(query="SELECT * FROM customers"))
    print(f"Reward: {result.reward}")
```

### Running Inference

```bash
export API_BASE_URL="https://api.groq.com/openai/v1"
export API_KEY="your_key"
export MODEL_NAME="llama-3.3-70b-versatile"
python inference.py
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SQL_ENV_TASK` | `basic_select` | Task to load: basic_select, join_aggregate, advanced_analytics |
| `SQL_ENV_MAX_STEPS` | `15` | Maximum total steps per episode |
| `SQL_ENV_STEP_PENALTY` | `0.02` | Penalty per retry attempt |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM API endpoint (for inference.py) |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model for inference |
| `HF_TOKEN` / `API_KEY` | (required) | API key for LLM calls |

## Project Structure

```
sql_env/
├── inference.py                 # Mandatory baseline inference script
├── Dockerfile                   # HF Spaces deployment container
├── openenv.yaml                 # OpenEnv metadata
├── README.md                    # This file
├── models.py                    # SQLAction, SQLObservation (typed Pydantic models)
├── client.py                    # SQLEnvClient for WebSocket connections
├── data/
│   ├── schema.sql               # Database table definitions
│   ├── seed.sql                 # Deterministic seed data
│   └── tasks/
│       ├── basic_select.json    # 5 easy questions + ground truth
│       ├── join_aggregate.json  # 5 medium questions + ground truth
│       └── advanced_analytics.json  # 5 hard questions + ground truth
├── server/
│   ├── app.py                   # FastAPI + Gradio app
│   ├── sql_env_environment.py   # SQLEnvironment (reset/step/state)
│   ├── database.py              # SQLite management
│   ├── graders.py               # Multi-component reward function
│   ├── gradio_ui.py             # Interactive web UI
│   └── Dockerfile               # Alternative Dockerfile (openenv scaffold)
└── tests/
    ├── test_database.py         # 8 tests
    ├── test_graders.py          # 13 tests
    ├── test_environment.py      # 15 tests
    ├── test_inference.py        # 8 tests
    └── test_server.py           # 5 tests (49 total, all passing)
```

## Technical Decisions

| Decision | Rationale |
|---|---|
| SQLite (in-memory) | Zero external deps, deterministic, resets instantly |
| E-commerce domain | Universally understood, naturally scales in complexity |
| 4-component reward | Provides gradient signal, not just binary pass/fail |
| Multiple attempts per question | Allows agent to learn from errors within an episode |
| Fixed seed data | Reproducible results — same data every reset() |
| Schema in every observation | No hidden information, agent sees full context |
