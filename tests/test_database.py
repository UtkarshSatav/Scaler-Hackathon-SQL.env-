"""Tests for the database module."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.database import Database


def test_initialize():
    """Database initializes with all tables and correct row counts."""
    db = Database()
    db.initialize()

    expected_counts = {
        "customers": 20,
        "products": 15,
        "orders": 30,
        "order_items": 46,
        "reviews": 25,
    }

    for table, expected in expected_counts.items():
        result = db.execute_query(f"SELECT COUNT(*) FROM {table}")
        assert result.success, f"Failed to query {table}: {result.error}"
        assert result.rows[0][0] == expected, (
            f"{table}: expected {expected} rows, got {result.rows[0][0]}"
        )

    db.close()


def test_select_queries():
    """Basic SELECT queries execute and return correct results."""
    db = Database()
    db.initialize()

    # Simple WHERE
    r = db.execute_query("SELECT name FROM customers WHERE age = 50")
    assert r.success
    assert r.row_count == 1
    assert r.rows[0][0] == "Suresh Menon"

    # ORDER BY + LIMIT
    r = db.execute_query("SELECT name, price FROM products ORDER BY price DESC LIMIT 1")
    assert r.success
    assert r.rows[0] == ("Bluetooth Speaker", 3999.0)

    # COUNT
    r = db.execute_query("SELECT COUNT(*) FROM orders WHERE status = 'shipped'")
    assert r.success
    assert r.rows[0][0] == 5

    db.close()


def test_join_queries():
    """JOIN and aggregate queries work correctly."""
    db = Database()
    db.initialize()

    # JOIN
    r = db.execute_query(
        "SELECT c.name, o.total_amount FROM customers c "
        "JOIN orders o ON c.id = o.customer_id WHERE o.id = 1"
    )
    assert r.success
    assert r.rows[0][0] == "Aarav Sharma"

    # GROUP BY + HAVING
    r = db.execute_query(
        "SELECT p.category, COUNT(*) as cnt FROM products p GROUP BY p.category ORDER BY cnt DESC"
    )
    assert r.success
    assert r.row_count == 4  # 4 categories

    # Customers with no orders
    r = db.execute_query(
        "SELECT name FROM customers WHERE id NOT IN "
        "(SELECT DISTINCT customer_id FROM orders) ORDER BY name"
    )
    assert r.success
    assert r.row_count == 2
    assert r.rows[0][0] == "Nisha Agarwal"
    assert r.rows[1][0] == "Sneha Gupta"

    db.close()


def test_window_functions():
    """Window functions (RANK, LAG) work in SQLite."""
    db = Database()
    db.initialize()

    # RANK
    r = db.execute_query(
        "SELECT name, price, RANK() OVER (ORDER BY price DESC) as rnk "
        "FROM products LIMIT 3"
    )
    assert r.success
    assert r.rows[0][2] == 1  # rank 1

    # LAG
    r = db.execute_query(
        "SELECT strftime('%Y-%m', order_date) as month, COUNT(*) as cnt, "
        "COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', order_date)) as growth "
        "FROM orders GROUP BY month ORDER BY month LIMIT 2"
    )
    assert r.success
    assert r.rows[0][2] is None  # first month has NULL growth
    assert r.rows[1][2] == 0  # Jan→Feb: 6→6 = 0

    db.close()


def test_block_modifications():
    """Modification statements are blocked."""
    db = Database()
    db.initialize()

    for stmt in [
        "DELETE FROM customers WHERE id = 1",
        "UPDATE customers SET name = 'hacked' WHERE id = 1",
        "INSERT INTO customers VALUES (99, 'x', 'x', 1, 'x', '2024-01-01')",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN hack TEXT",
        "CREATE TABLE hack (id INT)",
    ]:
        r = db.execute_query(stmt)
        assert not r.success, f"Should have blocked: {stmt}"
        assert "Only SELECT" in r.error

    db.close()


def test_error_handling():
    """Bad queries return errors, not crashes."""
    db = Database()
    db.initialize()

    # Syntax error
    r = db.execute_query("SELEC * FORM customers")
    assert not r.success
    assert "syntax" in r.error.lower()

    # Non-existent table
    r = db.execute_query("SELECT * FROM nonexistent_table")
    assert not r.success

    # Empty query
    r = db.execute_query("")
    assert not r.success

    # Query before init
    db2 = Database()
    r = db2.execute_query("SELECT 1")
    assert not r.success
    assert "not initialized" in r.error.lower()

    db.close()


def test_schema_description():
    """Schema description contains all tables and relationships."""
    db = Database()
    db.initialize()

    schema = db.get_schema_description()

    for table in ["customers", "products", "orders", "order_items", "reviews"]:
        assert table in schema, f"Missing table: {table}"

    assert "RELATIONSHIPS" in schema
    assert "orders.customer_id -> customers.id" in schema

    db.close()


def test_deterministic():
    """Two fresh databases produce identical results."""
    db1 = Database()
    db1.initialize()
    r1 = db1.execute_query("SELECT * FROM customers ORDER BY id")

    db2 = Database()
    db2.initialize()
    r2 = db2.execute_query("SELECT * FROM customers ORDER BY id")

    assert r1.rows == r2.rows
    assert r1.columns == r2.columns

    db1.close()
    db2.close()


if __name__ == "__main__":
    tests = [
        test_initialize,
        test_select_queries,
        test_join_queries,
        test_window_functions,
        test_block_modifications,
        test_error_handling,
        test_schema_description,
        test_deterministic,
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
    sys.exit(1 if failed else 0)
