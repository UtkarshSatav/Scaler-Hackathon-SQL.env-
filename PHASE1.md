# Phase 1: Setup & Database

## What We're Doing

Phase 1 lays the foundation for the entire SQLEnv project. We set up the OpenEnv scaffold, design a realistic e-commerce database, populate it with deterministic seed data, and build the database management layer that the environment will use.

## Why This Matters

Everything in later phases depends on this:
- The **database schema** defines what SQL queries are possible (and thus what tasks we can create)
- The **seed data** must be deterministic — same data every time so grading is reproducible
- The **database module** is the engine that executes agent queries and compares results

## What Gets Built

### 1. Database Schema (`data/schema.sql`)
A realistic e-commerce database with 5 tables:
- **customers** — id, name, email, age, city, signup_date
- **products** — id, name, category, price, stock
- **orders** — id, customer_id, order_date, status, total_amount
- **order_items** — id, order_id, product_id, quantity, unit_price
- **reviews** — id, product_id, customer_id, rating, review_text, review_date

Relationships:
- orders.customer_id → customers.id
- order_items.order_id → orders.id
- order_items.product_id → products.id
- reviews.customer_id → customers.id
- reviews.product_id → products.id

### 2. Seed Data (`data/seed.sql`)
- 20 customers (diverse names, cities, ages)
- 15 products across 4 categories (Electronics, Clothing, Books, Home)
- 30 orders with varied statuses (pending, shipped, delivered, cancelled)
- 60 order items linking orders to products
- 25 reviews with ratings 1-5

The data is carefully crafted so that:
- Easy queries return clear, unambiguous results
- Medium queries (JOINs, aggregation) produce interesting groupings
- Hard queries (window functions, subqueries) have meaningful patterns

### 3. Database Module (`server/database.py`)
- `init_db()` — Create tables and load seed data into SQLite
- `execute_query(sql)` — Safely execute a query and return results
- `get_schema_description()` — Return human-readable schema for the agent
- `get_db_path()` — Return path to the SQLite database file
- Connection management with proper cleanup

### 4. Updated Models (`models.py`)
Replace the echo-based scaffold models with SQL environment models:
- `SQLAction` — contains `query: str`
- `SQLObservation` — contains question, schema, query_result, error, steps_remaining, etc.

## Requirements From You

1. **Python 3.11** — Already installed (confirmed at `/opt/homebrew/bin/python3.11`)
2. **openenv-core** — Already installed for Python 3.11
3. **No Docker needed yet** — That's Phase 4
4. **No HF account needed yet** — That's Phase 5

## Files Modified/Created

| File | Action | Purpose |
|---|---|---|
| `models.py` | Modified | SQL-specific Action/Observation models |
| `server/database.py` | Created | SQLite database management |
| `data/schema.sql` | Created | Table definitions |
| `data/seed.sql` | Created | Deterministic seed data |
| `openenv.yaml` | Modified | Updated metadata |
| `pyproject.toml` | Modified | No new deps needed (SQLite is built-in) |

## Verification

After Phase 1, we can verify by:
```python
from server.database import init_db, execute_query, get_schema_description

# Initialize
init_db()

# Test a query
result = execute_query("SELECT * FROM customers WHERE age > 30")
print(result)  # Should return rows

# Get schema
print(get_schema_description())  # Should print human-readable schema
```
