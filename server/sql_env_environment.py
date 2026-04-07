"""
SQL Query Writing Environment.

An AI agent receives a database schema and natural language question,
then writes SQL queries to answer the question. The environment grades
each query with partial-credit scoring and provides feedback.
"""

import json
import os
from pathlib import Path
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import SQLAction, SQLObservation
except ImportError:
    from models import SQLAction, SQLObservation

from .database import Database
from .graders import grade_query, _clamp_reward

TASKS_DIR = Path(__file__).resolve().parent.parent / "data" / "tasks"

# Default task can be overridden via environment variable
DEFAULT_TASK = os.getenv("SQL_ENV_TASK", "basic_select")
MAX_TOTAL_STEPS = int(os.getenv("SQL_ENV_MAX_STEPS", "15"))
STEP_PENALTY = float(os.getenv("SQL_ENV_STEP_PENALTY", "0.02"))


def _load_task(task_name: str) -> dict:
    """Load a task definition from JSON file."""
    task_path = TASKS_DIR / f"{task_name}.json"
    if not task_path.exists():
        available = [f.stem for f in TASKS_DIR.glob("*.json")]
        raise ValueError(
            f"Task '{task_name}' not found. Available: {available}"
        )
    with open(task_path) as f:
        return json.load(f)


class SQLEnvironment(Environment):
    """
    SQL Query Writing Environment.

    The agent interacts with an e-commerce SQLite database by submitting
    SQL queries to answer natural language questions. Each query is graded
    with a multi-component reward function providing partial credit.

    Episode flow:
      1. reset() → loads task, initializes DB, returns first question
      2. step(SQLAction) → executes query, grades it, returns observation
      3. Episode ends when all questions answered or max steps reached
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._db = Database()
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task: dict = {}
        self._questions: list = []
        self._current_q_index: int = 0
        self._q_steps_used: int = 0
        self._max_steps_per_q: int = 3
        self._total_steps: int = 0
        self._rewards: list = []
        self._schema_cache: str = ""
        self._done: bool = False
        self._last_feedback: str = ""

    def reset(self) -> SQLObservation:
        """
        Reset the environment: initialize DB, load task, return first question.
        """
        self._db.initialize()
        self._state = State(episode_id=str(uuid4()), step_count=0)

        task_name = os.getenv("SQL_ENV_TASK", DEFAULT_TASK)
        self._task = _load_task(task_name)
        self._questions = self._task["questions"]
        self._max_steps_per_q = self._task.get("max_steps_per_question", 3)
        self._current_q_index = 0
        self._q_steps_used = 0
        self._total_steps = 0
        self._rewards = []
        self._done = False
        self._last_feedback = ""
        self._schema_cache = self._db.get_schema_description()

        return self._make_observation(
            reward=_clamp_reward(0.0),
            query_result="",
            error="",
        )

    def step(self, action: SQLAction) -> SQLObservation:  # type: ignore[override]
        """
        Execute the agent's SQL query, grade it, and return observation.
        """
        # Auto-reset if step called before reset (HTTP stateless mode)
        if not self._questions:
            self.reset()

        if self._done or self._current_q_index >= len(self._questions):
            self._done = True
            return self._make_observation(
                reward=_clamp_reward(0.0),
                query_result="Episode is over. Call reset() to start a new episode.",
                error="",
            )

        self._state.step_count += 1
        self._total_steps += 1
        self._q_steps_used += 1

        # Get current question
        question = self._questions[self._current_q_index]

        # Grade the query
        grade_result = grade_query(
            db=self._db,
            agent_sql=action.query,
            expected_columns=question["expected_columns"],
            expected_rows=question["expected_rows"],
            order_matters=question.get("order_matters", True),
        )

        raw_reward = grade_result["reward"]

        # Apply step penalty (not on first attempt)
        penalty = STEP_PENALTY * (self._q_steps_used - 1)
        reward = _clamp_reward(raw_reward - penalty)
        reward = round(reward, 4)

        self._rewards.append(reward)
        self._last_feedback = grade_result["feedback"]

        # Format query result for observation
        query_result_str = grade_result["query_result"].to_display_string()
        error_str = grade_result["query_result"].error or ""

        # Check if we should move to next question
        perfect = grade_result["exact_score"] == 1.0
        out_of_attempts = self._q_steps_used >= self._max_steps_per_q
        move_on = perfect or out_of_attempts

        if move_on:
            self._current_q_index += 1
            self._q_steps_used = 0

        # Check if episode is done
        if self._current_q_index >= len(self._questions):
            self._done = True
        if self._total_steps >= MAX_TOTAL_STEPS:
            self._done = True

        return self._make_observation(
            reward=reward,
            query_result=query_result_str,
            error=error_str,
        )

    @property
    def state(self) -> State:
        return self._state

    def _make_observation(
        self,
        reward: float,
        query_result: str,
        error: str,
    ) -> SQLObservation:
        """Build an SQLObservation for the current state."""
        if self._done or not self._questions or self._current_q_index >= len(self._questions):
            # Episode finished or not started
            return SQLObservation(
                task_name=self._task.get("task_name", ""),
                question="Episode complete. All questions answered.",
                schema_description="",
                query_result=query_result,
                error=error,
                steps_remaining=0,
                question_index=len(self._questions),
                total_questions=len(self._questions),
                done=True,
                reward=reward,
                metadata={
                    "feedback": self._last_feedback,
                    "total_reward": round(sum(self._rewards), 4),
                    "rewards": [round(r, 4) for r in self._rewards],
                },
            )

        question = self._questions[self._current_q_index]
        steps_remaining = self._max_steps_per_q - self._q_steps_used

        return SQLObservation(
            task_name=self._task.get("task_name", ""),
            question=question["question"],
            schema_description=self._schema_cache,
            query_result=query_result,
            error=error,
            steps_remaining=steps_remaining,
            question_index=self._current_q_index + 1,
            total_questions=len(self._questions),
            done=False,
            reward=reward,
            metadata={
                "feedback": self._last_feedback,
                "question_id": question["id"],
                "difficulty": self._task.get("difficulty", ""),
            },
        )
