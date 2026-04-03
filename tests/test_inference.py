"""Tests for inference.py — verifies format and local environment interaction."""

import os
import sys
import re
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("SQL_ENV_TASK", "basic_select")

from server.sql_env_environment import SQLEnvironment
from models import SQLAction
from inference import log_start, log_step, log_end


def test_log_start_format():
    """[START] line matches required format."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    log_start("basic_select", "sql_env", "test-model")
    sys.stdout = old_stdout
    line = buf.getvalue().strip()
    assert line.startswith("[START]")
    assert "task=basic_select" in line
    assert "env=sql_env" in line
    assert "model=test-model" in line


def test_log_step_format():
    """[STEP] line matches required format."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    log_step(1, "SELECT * FROM customers", 0.50, False, None)
    sys.stdout = old_stdout
    line = buf.getvalue().strip()
    assert line.startswith("[STEP]")
    assert "step=1" in line
    assert "reward=0.50" in line
    assert "done=false" in line
    assert "error=null" in line


def test_log_step_with_error():
    """[STEP] line includes error string when present."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    log_step(2, "BAD SQL", 0.00, False, "syntax error near BAD")
    sys.stdout = old_stdout
    line = buf.getvalue().strip()
    assert "error=syntax error near BAD" in line


def test_log_end_format():
    """[END] line matches required format."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    log_end(True, 3, 0.750, [0.50, 0.25, 1.00])
    sys.stdout = old_stdout
    line = buf.getvalue().strip()
    assert line.startswith("[END]")
    assert "success=true" in line
    assert "steps=3" in line
    assert "score=0.750" in line
    assert "rewards=0.50,0.25,1.00" in line


def test_log_end_failure():
    """[END] line shows success=false for failed runs."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    log_end(False, 1, 0.020, [0.10])
    sys.stdout = old_stdout
    line = buf.getvalue().strip()
    assert "success=false" in line


def test_local_run_basic():
    """Full local episode produces valid reward sequence."""
    os.environ["SQL_ENV_TASK"] = "basic_select"
    env = SQLEnvironment()
    obs = env.reset()

    rewards = []
    steps = 0

    # Simulate agent: use ground truth for Q1, bad query for rest
    queries = [
        "SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC",  # Q1 correct
        "SELECT 1",  # Q2 wrong
        "SELECT 1",  # Q2 wrong
        "SELECT 1",  # Q2 wrong (max attempts)
        "SELECT COUNT(*) as shipped_count FROM orders WHERE status = 'shipped'",  # Q3 correct
    ]

    for sql in queries:
        if obs.done:
            break
        obs = env.step(SQLAction(query=sql))
        rewards.append(obs.reward)
        steps += 1

    assert steps >= 3
    assert rewards[0] == 1.0, f"Ground truth Q1 should score 1.0, got {rewards[0]}"
    assert rewards[1] < 0.5, f"Bad query should score low, got {rewards[1]}"
    assert all(0.0 <= r <= 1.0 for r in rewards), f"All rewards should be [0,1]: {rewards}"


def test_inference_all_tasks_locally():
    """All 3 tasks can run through a full episode locally."""
    for task_name in ["basic_select", "join_aggregate", "advanced_analytics"]:
        os.environ["SQL_ENV_TASK"] = task_name
        env = SQLEnvironment()
        obs = env.reset()

        assert obs.task_name == task_name
        assert obs.total_questions == 5
        assert not obs.done

        # Step once with a generic query
        obs = env.step(SQLAction(query="SELECT 1"))
        assert obs.reward >= 0.0
        assert obs.reward <= 1.0


def test_multiline_action_sanitized():
    """Multiline SQL in action is sanitized for logging."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    log_step(1, "SELECT\n  name,\n  age\nFROM customers", 0.50, False, None)
    sys.stdout = old_stdout
    line = buf.getvalue().strip()
    assert "\n" not in line, "Log line must be single line"


if __name__ == "__main__":
    tests = [
        test_log_start_format,
        test_log_step_format,
        test_log_step_with_error,
        test_log_end_format,
        test_log_end_failure,
        test_local_run_basic,
        test_inference_all_tasks_locally,
        test_multiline_action_sanitized,
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
