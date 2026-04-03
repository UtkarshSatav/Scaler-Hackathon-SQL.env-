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


from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint — required by HF Spaces to detect the app is running."""
    return """
    <html><head><title>SQLEnv - SQL Query Writing Environment</title></head>
    <body style="font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px">
    <h1>SQLEnv</h1>
    <p>SQL Query Writing Environment for AI Agents</p>
    <h3>API Endpoints</h3>
    <ul>
        <li><b>POST /reset</b> — Reset environment, get first question</li>
        <li><b>POST /step</b> — Submit SQL query, get graded result</li>
        <li><b>GET /state</b> — Current episode state</li>
        <li><b>GET /health</b> — Health check</li>
        <li><b>GET /docs</b> — Interactive API docs</li>
    </ul>
    <p>3 tasks: basic_select (easy), join_aggregate (medium), advanced_analytics (hard)</p>
    </body></html>
    """


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
