"""
SQLite database management for SQLEnv.

Handles database initialization, query execution, and schema introspection.
All operations use an in-memory SQLite database that is re-created on each
environment reset, ensuring deterministic, isolated episodes.
"""

import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCHEMA_PATH = DATA_DIR / "schema.sql"
SEED_PATH = DATA_DIR / "seed.sql"


@dataclass
class QueryResult:
    """Result of executing a SQL query."""

    columns: List[str] = field(default_factory=list)
    rows: List[Tuple] = field(default_factory=list)
    error: Optional[str] = None
    row_count: int = 0

    @property
    def success(self) -> bool:
        return self.error is None

    def to_display_string(self, max_rows: int = 20) -> str:
        """Format result as a readable table string."""
        if self.error:
            return f"ERROR: {self.error}"
        if not self.columns:
            return "(no results)"

        # Calculate column widths
        col_widths = [len(str(c)) for c in self.columns]
        display_rows = self.rows[:max_rows]
        for row in display_rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        # Build table
        header = " | ".join(
            str(c).ljust(col_widths[i]) for i, c in enumerate(self.columns)
        )
        separator = "-+-".join("-" * w for w in col_widths)
        lines = [header, separator]

        for row in display_rows:
            line = " | ".join(
                str(val).ljust(col_widths[i]) for i, val in enumerate(row)
            )
            lines.append(line)

        if len(self.rows) > max_rows:
            lines.append(f"... ({len(self.rows) - max_rows} more rows)")

        lines.append(f"\n({self.row_count} row{'s' if self.row_count != 1 else ''})")
        return "\n".join(lines)


class Database:
    """
    Manages an in-memory SQLite database for one episode.

    Each call to `initialize()` creates a fresh database with the schema
    and seed data, ensuring deterministic state across episodes.
    """

    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None

    def initialize(self) -> None:
        """Create a fresh in-memory database with schema and seed data."""
        self.close()
        self._conn = sqlite3.connect(":memory:")
        self._conn.execute("PRAGMA foreign_keys = ON")

        schema_sql = SCHEMA_PATH.read_text()
        self._conn.executescript(schema_sql)

        seed_sql = SEED_PATH.read_text()
        self._conn.executescript(seed_sql)

        self._conn.commit()

    def execute_query(self, sql: str, timeout_seconds: float = 5.0) -> QueryResult:
        """
        Execute a SQL query and return the result.

        Only SELECT statements are allowed. Modification statements
        (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE) are rejected.

        Args:
            sql: The SQL query string to execute.
            timeout_seconds: Max execution time (unused for SQLite in-memory).

        Returns:
            QueryResult with columns, rows, and potential error.
        """
        if self._conn is None:
            return QueryResult(error="Database not initialized. Call reset() first.")

        # Strip and normalize
        stripped = sql.strip().rstrip(";").strip()
        if not stripped:
            return QueryResult(error="Empty query.")

        # Block modification statements
        first_word = stripped.split()[0].upper()
        blocked = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE"}
        if first_word in blocked:
            return QueryResult(
                error=f"Only SELECT queries are allowed. Got: {first_word}"
            )

        try:
            cursor = self._conn.execute(stripped)
            if cursor.description is None:
                return QueryResult(error="Query did not return results.")

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
            )
        except sqlite3.Error as e:
            return QueryResult(error=str(e))

    def get_schema_description(self) -> str:
        """
        Return a human-readable description of the database schema
        including table structures and sample data.
        """
        schema_text = []
        schema_text.append("=== DATABASE SCHEMA ===\n")

        tables = [
            ("customers", "Customer information"),
            ("products", "Product catalog"),
            ("orders", "Customer orders"),
            ("order_items", "Items within each order"),
            ("reviews", "Product reviews by customers"),
        ]

        if self._conn is None:
            return "Database not initialized."

        for table_name, description in tables:
            schema_text.append(f"TABLE: {table_name} -- {description}")

            # Get column info
            cursor = self._conn.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                # col: (cid, name, type, notnull, default_value, pk)
                col_name = col[1]
                col_type = col[2]
                is_pk = " PRIMARY KEY" if col[5] else ""
                is_nn = " NOT NULL" if col[3] else ""
                schema_text.append(f"  {col_name} {col_type}{is_pk}{is_nn}")

            # Get foreign keys
            cursor = self._conn.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            for fk in fks:
                schema_text.append(f"  FOREIGN KEY ({fk[3]}) REFERENCES {fk[2]}({fk[4]})")

            # Show sample data (first 3 rows)
            result = self.execute_query(f"SELECT * FROM {table_name} LIMIT 3")
            if result.success and result.rows:
                schema_text.append(f"  Sample data ({result.row_count} rows shown):")
                for row in result.rows:
                    schema_text.append(f"    {row}")

            # Show total count
            count_result = self.execute_query(
                f"SELECT COUNT(*) FROM {table_name}"
            )
            if count_result.success and count_result.rows:
                total = count_result.rows[0][0]
                schema_text.append(f"  Total rows: {total}")

            schema_text.append("")

        # Add relationship summary
        schema_text.append("=== RELATIONSHIPS ===")
        schema_text.append("orders.customer_id -> customers.id")
        schema_text.append("order_items.order_id -> orders.id")
        schema_text.append("order_items.product_id -> products.id")
        schema_text.append("reviews.product_id -> products.id")
        schema_text.append("reviews.customer_id -> customers.id")
        schema_text.append("")
        schema_text.append("=== NOTES ===")
        schema_text.append("- All dates are in ISO format (YYYY-MM-DD)")
        schema_text.append("- Prices are in INR (Indian Rupees)")
        schema_text.append("- Order status: pending, shipped, delivered, cancelled")
        schema_text.append("- Product categories: Electronics, Clothing, Books, Home")
        schema_text.append("- Ratings are integers from 1 to 5")

        return "\n".join(schema_text)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
