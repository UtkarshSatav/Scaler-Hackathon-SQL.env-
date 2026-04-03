"""
Inference Script for SQL Query Writing Environment
===================================================
MANDATORY — this file must be named `inference.py` and placed in the project root.

Uses OpenAI Client for all LLM calls. Reads credentials from environment variables:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

STDOUT FORMAT:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>
"""

import os
import sys
import textwrap
from typing import List, Optional

from openai import OpenAI

# ---------------------------------------------------------------------------
# Environment — runs locally (no Docker needed for inference)
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SQL_ENV_TASK", "basic_select")

from server.sql_env_environment import SQLEnvironment
from models import SQLAction

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HF_TOKEN = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# Also accept API_KEY as fallback for non-HF providers (e.g., Groq)
API_KEY = HF_TOKEN or os.getenv("API_KEY")

BENCHMARK = "sql_env"
TASKS = ["basic_select", "join_aggregate", "advanced_analytics"]
MAX_STEPS = 8
TEMPERATURE = 0.3
MAX_TOKENS = 512
SUCCESS_SCORE_THRESHOLD = 0.1


# ---------------------------------------------------------------------------
# Logging helpers (MANDATORY stdout format)
# ---------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    # Sanitize action: remove newlines, truncate for readability
    action_clean = action.replace("\n", " ").replace("\r", "").strip()
    if len(action_clean) > 200:
        action_clean = action_clean[:200] + "..."
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# System prompt for the LLM
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert SQL query writer. You are given a database schema and a
    natural language question. Write a single SQL SELECT query that answers
    the question exactly.

    Rules:
    - Write ONLY the SQL query, nothing else. No explanations, no markdown.
    - Use only SELECT statements (no INSERT, UPDATE, DELETE, etc.)
    - Match the requested column names and sorting exactly.
    - Use standard SQL compatible with SQLite.
    - If the question asks for rounding, use ROUND().
    - If the question asks for sorting, include ORDER BY.
    - Pay attention to whether results should be sorted ascending or descending.
""").strip()


def build_user_prompt(
    question: str,
    schema: str,
    last_result: str,
    last_error: str,
    feedback: str,
    attempt: int,
) -> str:
    """Build the prompt for the LLM."""
    parts = [
        f"DATABASE SCHEMA:\n{schema}\n",
        f"QUESTION: {question}\n",
    ]

    if attempt > 1:
        parts.append(f"PREVIOUS ATTEMPT RESULT:\n{last_result}\n")
        if last_error:
            parts.append(f"ERROR: {last_error}\n")
        if feedback:
            parts.append(f"FEEDBACK: {feedback}\n")
        parts.append(
            f"This is attempt {attempt}. Fix the query based on the feedback above.\n"
        )

    parts.append("Write the SQL query:")
    return "\n".join(parts)


def get_sql_from_model(
    client: OpenAI,
    question: str,
    schema: str,
    last_result: str,
    last_error: str,
    feedback: str,
    attempt: int,
) -> str:
    """Call the LLM to generate a SQL query."""
    user_prompt = build_user_prompt(
        question, schema, last_result, last_error, feedback, attempt
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()

        # Clean up: remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```sql and ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        return text if text else "SELECT 1"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "SELECT 1"


def run_task(client: OpenAI, task_name: str) -> None:
    """Run a single task and emit [START]/[STEP]/[END] logs."""
    os.environ["SQL_ENV_TASK"] = task_name

    env = SQLEnvironment()
    obs = env.reset()

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    attempt_on_q = 0

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        last_result = ""
        last_error = ""
        feedback = ""
        attempt_on_q = 1

        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break

            # Get SQL from model
            sql_query = get_sql_from_model(
                client=client,
                question=obs.question,
                schema=obs.schema_description,
                last_result=last_result,
                last_error=last_error,
                feedback=feedback,
                attempt=attempt_on_q,
            )

            # Step the environment
            obs = env.step(SQLAction(query=sql_query))

            reward = obs.reward
            done = obs.done
            error = obs.error if obs.error else None

            rewards.append(reward)
            steps_taken = step

            log_step(
                step=step,
                action=sql_query,
                reward=reward,
                done=done,
                error=error,
            )

            # Track state for retry prompting
            last_result = obs.query_result
            last_error = obs.error
            feedback = obs.metadata.get("feedback", "")

            # Track attempt number for current question
            if reward >= 0.98:  # near-perfect, moved to next question
                attempt_on_q = 1
            else:
                attempt_on_q += 1

            if done:
                break

        # Calculate normalized score
        max_possible = obs.total_questions  # 5 questions, max 1.0 each
        if max_possible > 0:
            score = sum(rewards) / max_possible
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_name} error: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


def main() -> None:
    """Run inference on all 3 tasks."""
    if not API_KEY:
        print("[ERROR] HF_TOKEN or API_KEY environment variable is required.", flush=True)
        sys.exit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    for task_name in TASKS:
        run_task(client, task_name)
        print("", flush=True)  # blank line between tasks


if __name__ == "__main__":
    main()
