"""
FastAPI application for the SQL Query Writing Environment.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action (SQL query)
    - GET /state: Get current environment state
    - GET /health: Health check
    - GET /web: Interactive Gradio playground
    - WS /ws: WebSocket endpoint for persistent sessions
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


# Mount the custom Gradio UI
import gradio as gr
from server.gradio_ui import create_gradio_app

gradio_app = create_gradio_app()
app = gr.mount_gradio_app(app, gradio_app, path="/")


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
