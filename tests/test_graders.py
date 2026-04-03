"""Tests for the grading system."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.database import Database
from server.graders import grade_query


def _db():
    db = Database()
    db.initialize()
    return db


def test_perfect_match():
    """Ground truth SQL scores exactly 1.0."""
    db = _db()
    r = grade_query(
        db,
        "SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC",
        ["name", "age"],
        [["Suresh Menon", 50], ["Kavita Joshi", 45], ["Swati Tiwari", 44],
         ["Rahul Kumar", 42], ["Pooja Mishra", 41], ["Divya Saxena", 39],
         ["Arjun Nair", 38], ["Rohan Das", 36], ["Priya Patel", 35],
         ["Amit Pandey", 34], ["Deepak Verma", 33], ["Nikhil Bhat", 32],
         ["Vikram Singh", 31]],
        order_matters=True,
    )
    assert r["reward"] == 1.0
    assert r["exact_score"] == 1.0
    db.close()


def test_syntax_error():
    """Invalid SQL scores 0.0."""
    db = _db()
    r = grade_query(db, "SELEC * FORM customers", ["name"], [["x"]], True)
    assert r["reward"] == 0.0
    assert r["syntax_score"] == 0.0
    db.close()


def test_empty_query():
    """Empty query scores 0.0."""
    db = _db()
    r = grade_query(db, "", ["name"], [["x"]], True)
    assert r["reward"] == 0.0
    db.close()


def test_blocked_modification():
    """Modification attempts score 0.0."""
    db = _db()
    r = grade_query(db, "DELETE FROM customers", ["name"], [["x"]], True)
    assert r["reward"] == 0.0
    db.close()


def test_wrong_columns():
    """Query with wrong columns gets only syntax credit (0.1)."""
    db = _db()
    r = grade_query(
        db, "SELECT email, city FROM customers LIMIT 1",
        ["name", "age"], [["x", 1]], True,
    )
    assert r["syntax_score"] == 1.0
    assert r["column_score"] == 0.0
    assert r["reward"] == 0.1
    db.close()


def test_partial_rows():
    """Query returning subset of expected rows gets partial row credit."""
    db = _db()
    r = grade_query(
        db, "SELECT name, age FROM customers WHERE age > 40 ORDER BY age DESC",
        ["name", "age"],
        [["Suresh Menon", 50], ["Kavita Joshi", 45], ["Swati Tiwari", 44],
         ["Rahul Kumar", 42], ["Pooja Mishra", 41], ["Divya Saxena", 39],
         ["Arjun Nair", 38], ["Rohan Das", 36], ["Priya Patel", 35],
         ["Amit Pandey", 34], ["Deepak Verma", 33], ["Nikhil Bhat", 32],
         ["Vikram Singh", 31]],
        order_matters=True,
    )
    assert r["syntax_score"] == 1.0
    assert r["column_score"] == 1.0
    assert 0.0 < r["row_score"] < 1.0  # partial
    assert r["exact_score"] == 0.0
    assert 0.1 < r["reward"] < 1.0
    db.close()


def test_extra_rows():
    """Query returning extra rows gets partial exact credit (0.5)."""
    db = _db()
    r = grade_query(
        db, "SELECT name, price FROM products ORDER BY price DESC",
        ["name", "price"],
        [["Bluetooth Speaker", 3999.0]],
        order_matters=False,
    )
    assert r["row_score"] == 1.0
    assert r["exact_score"] == 0.5  # all expected found but extra rows
    db.close()


def test_reordered_columns():
    """Query with swapped column order still scores 1.0."""
    db = _db()
    r = grade_query(
        db, "SELECT age, name FROM customers WHERE age = 50",
        ["name", "age"],
        [["Suresh Menon", 50]],
        order_matters=False,
    )
    assert r["reward"] == 1.0
    db.close()


def test_null_handling():
    """NULL values compared correctly."""
    db = _db()
    r = grade_query(
        db,
        "SELECT strftime('%Y-%m', order_date) as month, COUNT(*) as order_count, "
        "COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', order_date)) as growth "
        "FROM orders GROUP BY month ORDER BY month",
        ["month", "order_count", "growth"],
        [["2024-01", 6, None], ["2024-02", 6, 0], ["2024-03", 7, 1],
         ["2024-04", 4, -3], ["2024-05", 4, 0], ["2024-06", 3, -1]],
        order_matters=True,
    )
    assert r["reward"] == 1.0
    db.close()


def test_float_tolerance():
    """Float comparisons use tolerance of 0.01."""
    db = _db()
    # AVG might produce slightly different float representation
    r = grade_query(
        db,
        "SELECT ROUND(AVG(rating), 2) as avg_r FROM reviews",
        ["avg_r"],
        [[4.24]],
        order_matters=False,
    )
    assert r["reward"] == 1.0
    db.close()


def test_unordered_match():
    """Unordered comparison finds rows regardless of position."""
    db = _db()
    r = grade_query(
        db,
        "SELECT DISTINCT category FROM products ORDER BY category",
        ["category"],
        [["Home"], ["Electronics"], ["Books"], ["Clothing"]],  # different order
        order_matters=False,
    )
    assert r["row_score"] == 1.0
    assert r["exact_score"] == 1.0
    db.close()


def test_reward_bounded():
    """Reward is always in [0.0, 1.0]."""
    db = _db()
    for sql in [
        "SELECT 1",
        "INVALID SQL",
        "",
        "SELECT * FROM customers",
        "DELETE FROM customers",
    ]:
        r = grade_query(db, sql, ["name"], [["x"]], True)
        assert 0.0 <= r["reward"] <= 1.0, f"Reward out of bounds: {r['reward']} for: {sql}"
    db.close()


def test_feedback_present():
    """Feedback string is always non-empty."""
    db = _db()
    r = grade_query(db, "SELECT 1", ["name"], [["x"]], True)
    assert r["feedback"], "Feedback should not be empty"
    r = grade_query(db, "INVALID", ["name"], [["x"]], True)
    assert r["feedback"], "Feedback should not be empty for errors"
    db.close()


if __name__ == "__main__":
    tests = [
        test_perfect_match,
        test_syntax_error,
        test_empty_query,
        test_blocked_modification,
        test_wrong_columns,
        test_partial_rows,
        test_extra_rows,
        test_reordered_columns,
        test_null_handling,
        test_float_tolerance,
        test_unordered_match,
        test_reward_bounded,
        test_feedback_present,
    ]

    passed = 0
    failed = 0
    results = []

    for test in tests:
        name = test.__name__
        try:
            test()
            passed += 1
            results.append(f"PASS  {name}")
        except Exception as e:
            failed += 1
            results.append(f"FAIL  {name}: {e}")

    for r in results:
        print(r)
    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")

    import sys
    sys.exit(1 if failed else 0)
