"""
Data models for the SQL Query Writing Environment.

Defines the Action (agent submits SQL query) and Observation
(agent sees schema, question, query results, reward) types.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class SQLAction(Action):
    """Action for the SQL environment - a SQL query to execute."""

    query: str = Field(..., description="SQL SELECT query to execute against the database")


class SQLObservation(Observation):
    """Observation from the SQL environment."""

    task_name: str = Field(default="", description="Current task identifier (e.g., basic_select)")
    question: str = Field(default="", description="Natural language question to answer with SQL")
    schema_description: str = Field(default="", description="Human-readable database schema")
    query_result: str = Field(default="", description="Result of the last executed query (or error)")
    error: str = Field(default="", description="SQL error message if query failed, empty otherwise")
    steps_remaining: int = Field(default=0, description="Number of attempts remaining for current question")
    question_index: int = Field(default=0, description="Current question number (1-indexed)")
    total_questions: int = Field(default=0, description="Total questions in this task")
