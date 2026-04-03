# Phase 3: Tasks & Grading (Completed in Phase 2)

## Status: COMPLETE

Phase 3 was fully implemented during Phase 2 to avoid context-switching between
related components. All deliverables are done and verified.

## Deliverables Completed

### 1. All 15 Questions Written (5 per difficulty)

| Task | Difficulty | Questions | SQL Features |
|---|---|---|---|
| `basic_select` | Easy | 5 | WHERE, ORDER BY, LIMIT, COUNT |
| `join_aggregate` | Medium | 5 | JOIN, GROUP BY, HAVING, AVG, SUM, subquery |
| `advanced_analytics` | Hard | 5 | Subqueries, RANK(), LAG(), PARTITION BY, HAVING with subquery |

Files: `data/tasks/basic_select.json`, `data/tasks/join_aggregate.json`, `data/tasks/advanced_analytics.json`

### 2. Grader Manually Tested

All 15 ground truth queries verified against the database — each scores exactly 1.0.

### 3. Edge Cases Tested

| Edge Case | Expected | Actual | Status |
|---|---|---|---|
| Perfect match | 1.00 | 1.00 | PASS |
| Syntax error | 0.00 | 0.00 | PASS |
| Empty query | 0.00 | 0.00 | PASS |
| DELETE/DROP blocked | 0.00 | 0.00 | PASS |
| Wrong columns | 0.10 | 0.10 | PASS |
| Partial rows | 0.10-0.60 | 0.42 | PASS |
| Extra rows returned | 0.80 | 0.80 | PASS |
| Reordered columns | 1.00 | 1.00 | PASS |
| NULL values | 1.00 | 1.00 | PASS |
| Float tolerance | 1.00 | 1.00 | PASS |
| Unordered set match | 1.00 | 1.00 | PASS |

### 4. Graders Deterministic & Reproducible

- `test_deterministic` in `tests/test_database.py` confirms two fresh databases produce identical results
- All grader tests run deterministically — same input always produces same score

### 5. Unit Tests Written

| Test File | Tests | Status |
|---|---|---|
| `tests/test_database.py` | 8 | All PASS |
| `tests/test_graders.py` | 13 | All PASS |
| `tests/test_environment.py` | 15 | All PASS |
| `tests/test_server.py` | 5 | All PASS |
| **Total** | **41** | **All PASS** |

Full results in `test_results/SUMMARY.txt`.
