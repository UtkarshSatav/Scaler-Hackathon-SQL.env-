"""Tests for the SQLEnvironment (reset/step/state)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["SQL_ENV_TASK"] = "basic_select"

from server.sql_env_environment import SQLEnvironment
from models import SQLAction


def test_reset_returns_observation():
    """reset() returns a valid SQLObservation with first question."""
    env = SQLEnvironment()
    obs = env.reset()

    assert obs.task_name == "basic_select"
    assert obs.question != ""
    assert obs.schema_description != ""
    assert obs.done is False
    assert obs.reward == 0.0
    assert obs.question_index == 1
    assert obs.total_questions == 5
    assert obs.steps_remaining == 3


def test_step_correct_query():
    """Correct query scores 1.0 and advances to next question."""
    env = SQLEnvironment()
    env.reset()

    obs = env.step(SQLAction(
        query="SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC"
    ))

    assert obs.reward == 1.0
    assert obs.done is False
    assert obs.question_index == 2  # moved to Q2
    assert "Perfect match" in obs.metadata.get("feedback", "")


def test_step_wrong_query():
    """Wrong query gets partial credit and stays on same question."""
    env = SQLEnvironment()
    env.reset()

    obs = env.step(SQLAction(query="SELECT * FROM products"))

    assert 0.0 < obs.reward < 1.0
    assert obs.done is False
    assert obs.question_index == 1  # still on Q1


def test_step_syntax_error():
    """Syntax error scores 0.0."""
    env = SQLEnvironment()
    env.reset()

    obs = env.step(SQLAction(query="SELEC * FORM xyz"))

    assert obs.reward == 0.0
    assert obs.error != "" or "error" in obs.metadata.get("feedback", "").lower()


def test_step_penalty():
    """Second attempt on same question gets step penalty."""
    env = SQLEnvironment()
    env.reset()

    # First attempt (wrong)
    env.step(SQLAction(query="SELECT 1"))
    # Second attempt (correct)
    obs = env.step(SQLAction(
        query="SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC"
    ))

    assert obs.reward == 0.98  # 1.0 - 0.02 penalty


def test_max_attempts_advances():
    """After max attempts, moves to next question."""
    env = SQLEnvironment()
    env.reset()

    # Use all 3 attempts on Q1 with wrong queries
    for _ in range(3):
        obs = env.step(SQLAction(query="SELECT 1"))

    # Should now be on Q2
    assert obs.question_index == 2 or obs.done


def test_episode_ends():
    """Episode ends after all questions answered."""
    env = SQLEnvironment()
    env.reset()

    from server.sql_env_environment import _load_task
    task = _load_task("basic_select")

    for q in task["questions"]:
        obs = env.step(SQLAction(query=q["ground_truth_sql"]))

    assert obs.done is True


def test_state_property():
    """state property returns valid State object."""
    env = SQLEnvironment()
    env.reset()

    s = env.state
    assert s.episode_id is not None
    assert s.step_count == 0

    env.step(SQLAction(query="SELECT 1"))
    s = env.state
    assert s.step_count == 1


def test_step_after_done():
    """Stepping after done returns done observation with 0 reward."""
    env = SQLEnvironment()
    env.reset()

    from server.sql_env_environment import _load_task
    task = _load_task("basic_select")
    for q in task["questions"]:
        env.step(SQLAction(query=q["ground_truth_sql"]))

    # Extra step after done
    obs = env.step(SQLAction(query="SELECT 1"))
    assert obs.done is True
    assert obs.reward == 0.0


def test_all_tasks_load():
    """All 3 task files load and have 5 questions each."""
    for task_name in ["basic_select", "join_aggregate", "advanced_analytics"]:
        from server.sql_env_environment import _load_task
        task = _load_task(task_name)
        assert len(task["questions"]) == 5, f"{task_name} has {len(task['questions'])} questions"
        assert task["task_name"] == task_name


def test_all_tasks_perfect_score():
    """All 3 tasks score 5.0 total with ground truth SQL."""
    for task_name in ["basic_select", "join_aggregate", "advanced_analytics"]:
        os.environ["SQL_ENV_TASK"] = task_name
        env = SQLEnvironment()
        env.reset()

        from server.sql_env_environment import _load_task
        task = _load_task(task_name)
        total = 0.0

        for q in task["questions"]:
            obs = env.step(SQLAction(query=q["ground_truth_sql"]))
            total += obs.reward

        assert total == 5.0, f"{task_name}: expected 5.0, got {total}"
        assert obs.done is True


def test_auto_reset():
    """step() on uninitialized env auto-resets."""
    env = SQLEnvironment()
    # Don't call reset(), go straight to step
    obs = env.step(SQLAction(query="SELECT 1"))
    assert obs.task_name != ""  # auto-reset loaded a task
    assert obs.reward >= 0.0


def test_rewards_vary():
    """Different queries produce different rewards (not constant grader)."""
    env = SQLEnvironment()
    env.reset()

    rewards = set()
    queries = [
        "SELECT 1",
        "SELECT name FROM customers",
        "SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC",
        "INVALID SQL",
    ]

    for q in queries:
        env2 = SQLEnvironment()
        env2.reset()
        obs = env2.step(SQLAction(query=q))
        rewards.add(round(obs.reward, 2))

    assert len(rewards) >= 3, f"Rewards should vary, got: {rewards}"


def test_medium_task():
    """Medium task works correctly."""
    os.environ["SQL_ENV_TASK"] = "join_aggregate"
    env = SQLEnvironment()
    obs = env.reset()
    assert obs.task_name == "join_aggregate"
    assert obs.steps_remaining == 4  # medium allows 4 attempts


def test_hard_task():
    """Hard task works correctly."""
    os.environ["SQL_ENV_TASK"] = "advanced_analytics"
    env = SQLEnvironment()
    obs = env.reset()
    assert obs.task_name == "advanced_analytics"
    assert obs.steps_remaining == 5  # hard allows 5 attempts


if __name__ == "__main__":
    tests = [
        test_reset_returns_observation,
        test_step_correct_query,
        test_step_wrong_query,
        test_step_syntax_error,
        test_step_penalty,
        test_max_attempts_advances,
        test_episode_ends,
        test_state_property,
        test_step_after_done,
        test_all_tasks_load,
        test_all_tasks_perfect_score,
        test_auto_reset,
        test_rewards_vary,
        test_medium_task,
        test_hard_task,
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
