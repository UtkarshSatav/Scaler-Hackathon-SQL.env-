# Phase 2: Core Environment, Tasks & Grading

## What We Built

Phase 2 implements the complete environment logic — the heart of the project. After this phase, the SQLEnv is fully functional: an agent can connect, receive questions, submit SQL queries, and get graded with partial-credit scoring.

## Components Built

### 1. Task Definitions (`data/tasks/*.json`)

Three JSON files, each containing 5 questions with ground truth:

| Task File | Difficulty | Questions | Max Steps/Q | SQL Features |
|---|---|---|---|---|
| `basic_select.json` | Easy | 5 | 3 | WHERE, ORDER BY, LIMIT, COUNT |
| `join_aggregate.json` | Medium | 5 | 4 | JOIN, GROUP BY, HAVING, AVG, SUM |
| `advanced_analytics.json` | Hard | 5 | 5 | Subqueries, CTEs, RANK(), LAG(), PARTITION BY |

Each question includes:
- `id` — Unique identifier (e.g., `easy_1`, `med_3`, `hard_5`)
- `question` — Natural language question the agent must answer
- `ground_truth_sql` — Reference SQL query (verified against our database)
- `expected_columns` — Column names the result should have
- `expected_rows` — Exact expected result rows
- `order_matters` — Whether row order affects scoring

### 2. Multi-Component Grader (`server/graders.py`)

The `grade_query()` function scores each agent submission with 4 components:

```
Total Reward = 0.1 * syntax + 0.2 * columns + 0.3 * rows + 0.4 * exact
```

| Component | Weight | What It Checks |
|---|---|---|
| `syntax_score` | 0.1 | Query parses and executes without SQL error |
| `column_score` | 0.2 | Fraction of expected columns present in result |
| `row_score` | 0.3 | Fraction of expected rows matching (position-aware if ordered) |
| `exact_score` | 0.4 | Full result set matches ground truth exactly |

**Key features:**
- Handles NULL values correctly (Python None ↔ SQL NULL)
- Handles column reordering (agent can return columns in different order)
- Numeric tolerance (±0.01) for floating point comparisons
- Partial credit for extra rows returned (exact_score = 0.5)
- Step penalty: -0.02 per retry attempt (encourages efficiency)
- Detailed feedback string explaining what went right/wrong

### 3. Core Environment (`server/sql_env_environment.py`)

The `SQLEnvironment` class implements the full OpenEnv interface:

**`reset()`**
1. Creates fresh in-memory SQLite database with schema + seed data
2. Loads the configured task (via `SQL_ENV_TASK` env var, default: `basic_select`)
3. Caches the schema description
4. Returns first question as `SQLObservation`

**`step(action: SQLAction)`**
1. Validates episode state (auto-resets if never initialized)
2. Executes the agent's SQL query via `Database.execute_query()`
3. Grades the result via `grade_query()` against ground truth
4. Applies step penalty for retries
5. Advances to next question on perfect score or max attempts exhausted
6. Returns `SQLObservation` with reward, result, feedback, and progress info

**`state` property**
- Returns OpenEnv `State` with `episode_id` and `step_count`

**Episode flow:**
```
reset() → Q1 → step() → step() → ... → Q2 → step() → ... → Q5 → done=True
```

Each question allows N attempts (3 for easy, 4 for medium, 5 for hard). Agent moves to next question on:
- Perfect score (exact_score = 1.0), OR
- Max attempts exhausted

Episode ends when all 5 questions are answered or `MAX_TOTAL_STEPS` (15) reached.

### 4. Updated Server (`server/app.py`)

Wired up `create_app(SQLEnvironment, SQLAction, SQLObservation)` with:
- All HTTP endpoints: POST /reset, POST /step, GET /state, GET /health
- WebSocket support at /ws for stateful sessions
- `max_concurrent_envs=3` for parallel WebSocket clients

### 5. Updated Client (`client.py`)

`SQLEnvClient` class for the inference script to use:
- `_step_payload()` — serializes `SQLAction(query=...)` to JSON
- `_parse_result()` — deserializes response into `StepResult[SQLObservation]`
- `_parse_state()` — deserializes state response

### 6. Seed Data Updates (`data/seed.sql`)

Added 6 extra order items (IDs 41-46) to ensure:
- 5 customers buy from 3+ product categories (needed for HARD task 4)
- Rahul Kumar buys from all 4 categories
- Better category diversity for analytics queries

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SQL_ENV_TASK` | `basic_select` | Which task to load (basic_select, join_aggregate, advanced_analytics) |
| `SQL_ENV_MAX_STEPS` | `15` | Maximum total steps per episode |
| `SQL_ENV_STEP_PENALTY` | `0.02` | Penalty per retry attempt |

## Verification Results

### Ground Truth Validation
All 15 questions across 3 tasks score perfect 1.0 when given the ground truth SQL:
```
basic_select:        5/5 perfect, total reward = 5.00
join_aggregate:      5/5 perfect, total reward = 5.00
advanced_analytics:  5/5 perfect, total reward = 5.00
```

### Grader Edge Cases
| Test Case | Result |
|---|---|
| Perfect match | reward = 1.00 |
| Syntax error | reward = 0.00 |
| Partial rows (age>40 vs age>30) | reward = 0.42 |
| Wrong columns entirely | reward = 0.10 |
| Empty query | reward = 0.00 |
| DELETE attempt (blocked) | reward = 0.00 |
| Extra rows returned | reward = 0.80 |
| Reordered columns | reward = 1.00 |
| NULL value handling | reward = 1.00 |

### HTTP Server
- GET /health → 200 `{"status": "healthy"}`
- POST /reset → 200, returns first question with schema
- POST /step → 200, returns graded observation with reward
- GET /state → 200, returns episode_id + step_count

## Files Modified/Created

| File | Action | Purpose |
|---|---|---|
| `data/tasks/basic_select.json` | Created | 5 easy questions + ground truth |
| `data/tasks/join_aggregate.json` | Created | 5 medium questions + ground truth |
| `data/tasks/advanced_analytics.json` | Created | 5 hard questions + ground truth |
| `server/graders.py` | Created | Multi-component reward function |
| `server/sql_env_environment.py` | Rewritten | Full SQLEnvironment implementation |
| `server/app.py` | Updated | Wired new environment + models |
| `client.py` | Updated | SQLEnvClient with new models |
| `data/seed.sql` | Updated | Added 6 order items for category diversity |

## What's Next (Phase 3)

Phase 3 will focus on:
1. Writing `inference.py` — the mandatory baseline script using OpenAI client
2. Following the exact [START]/[STEP]/[END] stdout format
3. Running against all 3 tasks to produce baseline scores
4. Testing reproducibility
