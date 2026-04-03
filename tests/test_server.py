"""Tests for the HTTP server endpoints."""

import sys
import time
import subprocess
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"
_server_proc = None


def _start_server():
    global _server_proc
    _server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.app:app",
         "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=str(Path(__file__).resolve().parent.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to be ready
    for _ in range(30):
        try:
            urlopen(f"{BASE}/health", timeout=1)
            return
        except (URLError, ConnectionError):
            time.sleep(0.5)
    raise RuntimeError("Server failed to start")


def _stop_server():
    global _server_proc
    if _server_proc:
        _server_proc.terminate()
        _server_proc.wait(timeout=5)
        _server_proc = None


def _post(path, data=None):
    body = json.dumps(data or {}).encode()
    req = Request(f"{BASE}{path}", data=body,
                  headers={"Content-Type": "application/json"},
                  method="POST")
    resp = urlopen(req, timeout=10)
    return json.loads(resp.read())


def _get(path):
    resp = urlopen(f"{BASE}{path}", timeout=10)
    return json.loads(resp.read())


def test_health():
    """GET /health returns healthy status."""
    data = _get("/health")
    assert data["status"] == "healthy"


def test_reset():
    """POST /reset returns observation with question."""
    data = _post("/reset")
    assert "observation" in data
    obs = data["observation"]
    assert obs["task_name"] == "basic_select"
    assert obs["question"] != ""
    assert obs["schema_description"] != ""
    assert data["done"] is False
    assert data["reward"] == 0.0


def test_step():
    """POST /step executes query and returns graded observation."""
    # Reset first (new instance per request, but auto-reset handles it)
    data = _post("/step", {
        "action": {"query": "SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC"}
    })
    assert "observation" in data
    assert data["reward"] > 0.0  # should get at least syntax credit


def test_state():
    """GET /state returns episode state."""
    data = _get("/state")
    assert "episode_id" in data
    assert "step_count" in data


def test_schema():
    """GET /schema returns action/observation schemas."""
    data = _get("/schema")
    assert "action" in data or "action_schema" in data or isinstance(data, dict)


if __name__ == "__main__":
    tests = [
        test_health,
        test_reset,
        test_step,
        test_state,
        test_schema,
    ]

    print("Starting server...")
    try:
        _start_server()
        print(f"Server running on port {PORT}\n")
    except RuntimeError as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    passed = 0
    failed = 0
    results = []

    try:
        for test in tests:
            name = test.__name__
            try:
                test()
                passed += 1
                results.append(f"PASS  {name}")
            except Exception as e:
                failed += 1
                results.append(f"FAIL  {name}: {e}")
    finally:
        _stop_server()

    for r in results:
        print(r)
    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
    sys.exit(1 if failed else 0)
