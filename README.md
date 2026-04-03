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

An OpenEnv-compatible reinforcement learning environment where an AI agent learns to write correct SQL queries from natural language questions against a realistic e-commerce database.

## Overview

The agent receives a database schema and a natural language question, submits SQL queries, and gets graded with rich partial-credit scoring.

**3 difficulty levels, 5 questions each:**

| Task | Difficulty | SQL Features |
|---|---|---|
| `basic_select` | Easy | WHERE, ORDER BY, LIMIT, COUNT |
| `join_aggregate` | Medium | JOIN, GROUP BY, HAVING, AVG, SUM |
| `advanced_analytics` | Hard | Subqueries, RANK(), LAG(), PARTITION BY |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reset` | POST | Reset environment, get first question |
| `/step` | POST | Submit SQL query, get graded result |
| `/state` | GET | Current episode state |
| `/docs` | GET | Interactive API documentation |

## Action Space

```json
{"action": {"query": "SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC"}}
```

## Observation Space

```json
{
  "observation": {
    "task_name": "basic_select",
    "question": "Find all customers older than 30...",
    "schema_description": "=== DATABASE SCHEMA === ...",
    "query_result": "name | age ...",
    "error": "",
    "steps_remaining": 2,
    "question_index": 1,
    "total_questions": 5
  },
  "reward": 1.0,
  "done": false
}
```

## Reward Function

Multi-component partial credit scoring (0.0 to 1.0):

| Component | Weight | What It Measures |
|---|---|---|
| Syntax | 0.1 | Query executes without error |
| Columns | 0.2 | Expected columns present |
| Rows | 0.3 | Expected rows match |
| Exact | 0.4 | Full result set matches ground truth |

## Database

Realistic e-commerce database with 5 tables:
- **customers** (20 rows) - name, email, age, city, signup_date
- **products** (15 rows) - name, category, price, stock
- **orders** (30 rows) - customer_id, order_date, status, total_amount
- **order_items** (46 rows) - order_id, product_id, quantity, unit_price
- **reviews** (25 rows) - product_id, customer_id, rating, review_text

## Baseline Scores

Tested with Llama 3.3 70B (via Groq):

| Task | Score |
|---|---|
| basic_select | 1.000 |
| join_aggregate | 1.000 |
| advanced_analytics | 0.969 |

## Setup

```bash
pip install openenv-core
cd sql_env
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| SQL_ENV_TASK | basic_select | Task to load |
| SQL_ENV_MAX_STEPS | 15 | Max steps per episode |
