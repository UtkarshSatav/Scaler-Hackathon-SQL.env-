"""
FastAPI application for the SQL Query Writing Environment.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action (SQL query)
    - GET /state: Get current environment state
    - GET /health: Health check
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core"
    ) from e

try:
    from ..models import SQLAction, SQLObservation
    from .sql_env_environment import SQLEnvironment
except (ImportError, ModuleNotFoundError):
    from models import SQLAction, SQLObservation
    from server.sql_env_environment import SQLEnvironment


app = create_app(
    SQLEnvironment,
    SQLAction,
    SQLObservation,
    env_name="sql_env",
    max_concurrent_envs=3,
)


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
