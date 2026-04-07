"""
Multi-component grading system for SQL query evaluation.

Scores agent queries against ground truth with partial credit:
  - syntax_score  (0.1): Query parses and executes without error
  - column_score  (0.2): Fraction of expected columns present
  - row_score     (0.3): Fraction of expected rows matching
  - exact_score   (0.4): Full result set matches ground truth exactly

Total reward per question is in (0.0, 1.0) — strictly between 0 and 1.
"""

from typing import Any, List, Optional, Tuple

from .database import Database, QueryResult

# Epsilon to ensure scores are strictly between 0 and 1 (never exactly 0.0 or 1.0)
_EPS = 0.001


def _clamp_reward(reward: float) -> float:
    """Clamp reward to be strictly within (0, 1)."""
    return min(max(reward, _EPS), 1.0 - _EPS)


def _normalize_value(val: Any) -> Any:
    """Normalize a value for comparison (handle float/int equivalence, None)."""
    if val is None:
        return None
    if isinstance(val, float):
        if val == int(val):
            return int(val)
        return round(val, 2)
    if isinstance(val, str):
        return val.strip()
    return val


def _normalize_row(row: Tuple) -> Tuple:
    """Normalize all values in a row."""
    return tuple(_normalize_value(v) for v in row)


def _normalize_column_name(col: str) -> str:
    """Normalize column name for comparison (lowercase, strip)."""
    return col.strip().lower()


def grade_query(
    db: Database,
    agent_sql: str,
    expected_columns: List[str],
    expected_rows: List[List],
    order_matters: bool = True,
) -> dict:
    """
    Grade an agent's SQL query against expected results.

    Args:
        db: Active Database instance.
        agent_sql: The SQL query submitted by the agent.
        expected_columns: List of expected column names.
        expected_rows: List of expected row values (list of lists).
        order_matters: Whether row order affects scoring.

    Returns:
        Dictionary with:
          - reward: float in [0.0, 1.0]
          - syntax_score: float
          - column_score: float
          - row_score: float
          - exact_score: float
          - query_result: QueryResult object
          - feedback: str describing what was right/wrong
    """
    result = db.execute_query(agent_sql)

    # Component weights
    W_SYNTAX = 0.1
    W_COLUMN = 0.2
    W_ROW = 0.3
    W_EXACT = 0.4

    # --- Syntax Score ---
    if not result.success:
        return {
            "reward": _clamp_reward(0.0),
            "syntax_score": 0.0,
            "column_score": 0.0,
            "row_score": 0.0,
            "exact_score": 0.0,
            "query_result": result,
            "feedback": f"SQL error: {result.error}",
        }

    syntax_score = 1.0

    # --- Column Score ---
    expected_cols_normalized = [_normalize_column_name(c) for c in expected_columns]
    actual_cols_normalized = [_normalize_column_name(c) for c in result.columns]

    if not expected_cols_normalized:
        column_score = 1.0 if not actual_cols_normalized else 0.0
    else:
        matched_cols = sum(
            1 for c in expected_cols_normalized if c in actual_cols_normalized
        )
        column_score = matched_cols / len(expected_cols_normalized)

    # --- Row Score ---
    expected_rows_normalized = [
        _normalize_row(tuple(row)) for row in expected_rows
    ]
    actual_rows_normalized = [_normalize_row(row) for row in result.rows]

    if not expected_rows_normalized:
        row_score = 1.0 if not actual_rows_normalized else 0.0
    else:
        if order_matters:
            # For ordered results, match position-by-position
            matched_rows = 0
            for i, expected_row in enumerate(expected_rows_normalized):
                if i < len(actual_rows_normalized):
                    if _rows_match(expected_row, actual_rows_normalized[i], expected_cols_normalized, actual_cols_normalized):
                        matched_rows += 1
            row_score = matched_rows / len(expected_rows_normalized)
        else:
            # For unordered results, check set membership
            matched_rows = 0
            remaining_actual = list(actual_rows_normalized)
            for expected_row in expected_rows_normalized:
                for j, actual_row in enumerate(remaining_actual):
                    if _rows_match(expected_row, actual_row, expected_cols_normalized, actual_cols_normalized):
                        matched_rows += 1
                        remaining_actual.pop(j)
                        break
            row_score = matched_rows / len(expected_rows_normalized)

    # --- Exact Score ---
    exact_score = 0.0
    if column_score == 1.0 and row_score == 1.0:
        # Check exact match: same number of rows and all matched
        if len(actual_rows_normalized) == len(expected_rows_normalized):
            exact_score = 1.0
        else:
            # Extra rows returned — partial exact credit
            exact_score = 0.5

    # --- Total Reward ---
    reward = (
        W_SYNTAX * syntax_score
        + W_COLUMN * column_score
        + W_ROW * row_score
        + W_EXACT * exact_score
    )
    reward = round(_clamp_reward(reward), 4)

    # --- Feedback ---
    feedback_parts = []
    if syntax_score == 1.0:
        feedback_parts.append("Query executed successfully.")
    if column_score < 1.0:
        missing = [c for c in expected_cols_normalized if c not in actual_cols_normalized]
        feedback_parts.append(f"Missing columns: {missing}. Expected: {expected_cols_normalized}, Got: {actual_cols_normalized}")
    if row_score < 1.0:
        feedback_parts.append(
            f"Row match: {row_score:.0%} ({int(row_score * len(expected_rows_normalized))}/{len(expected_rows_normalized)} rows correct). "
            f"Expected {len(expected_rows_normalized)} rows, got {len(actual_rows_normalized)}."
        )
    if exact_score == 1.0:
        feedback_parts.append("Perfect match!")
    elif exact_score == 0.5:
        feedback_parts.append(f"All expected rows found but got {len(actual_rows_normalized)} rows instead of {len(expected_rows_normalized)} (extra rows).")

    return {
        "reward": reward,
        "syntax_score": syntax_score,
        "column_score": column_score,
        "row_score": row_score,
        "exact_score": exact_score,
        "query_result": result,
        "feedback": " ".join(feedback_parts),
    }


def _rows_match(
    expected_row: Tuple,
    actual_row: Tuple,
    expected_cols: List[str],
    actual_cols: List[str],
) -> bool:
    """
    Check if an actual row matches an expected row.

    Handles column reordering: maps expected columns to actual column positions.
    """
    if len(expected_cols) != len(expected_row):
        return False

    # Build a mapping from expected column index to actual column index
    col_map = {}
    for i, ec in enumerate(expected_cols):
        if ec in actual_cols:
            col_map[i] = actual_cols.index(ec)
        else:
            return False  # Missing column

    for exp_idx, act_idx in col_map.items():
        if act_idx >= len(actual_row):
            return False
        exp_val = expected_row[exp_idx]
        act_val = _normalize_value(actual_row[act_idx])
        if exp_val != act_val:
            # Try numeric comparison with tolerance
            try:
                if abs(float(exp_val) - float(act_val)) < 0.01:
                    continue
            except (TypeError, ValueError):
                pass
            return False

    return True
