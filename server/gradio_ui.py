"""
Custom Gradio UI for the SQL Query Writing Environment.

Provides an interactive playground where users can:
- Select task difficulty
- See the database schema
- Write and submit SQL queries
- View graded results with reward breakdowns
- Track progress through questions
"""

import gradio as gr
import os
import json
from pathlib import Path

# We use the environment directly (not HTTP) for the Gradio UI
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.sql_env_environment import SQLEnvironment, _load_task
from server.database import Database
from server.graders import grade_query
from models import SQLAction


def create_gradio_app() -> gr.Blocks:
    """Create a custom Gradio Blocks app for the SQL environment."""

    # Shared state
    env_state = {"env": None, "task_name": "basic_select"}

    def reset_env(task_name):
        """Reset environment with selected task."""
        os.environ["SQL_ENV_TASK"] = task_name
        env = SQLEnvironment()
        obs = env.reset()
        env_state["env"] = env
        env_state["task_name"] = task_name

        task = _load_task(task_name)
        difficulty = task.get("difficulty", "unknown")

        status = f"**Task:** {task_name} ({difficulty})  |  **Question 1/{obs.total_questions}**  |  **Attempts left:** {obs.steps_remaining}"

        return (
            obs.question,
            obs.schema_description,
            "",  # clear query input
            "",  # clear result
            "",  # clear feedback
            "0.0",  # reward
            status,
            _build_progress_html(0, obs.total_questions, []),
        )

    def submit_query(query, question_text):
        """Submit a SQL query and get graded results."""
        env = env_state.get("env")
        if env is None:
            return (
                question_text,
                "Please click 'Start Task' first!",
                "Environment not initialized",
                "0.0",
                "**Error:** Not initialized",
                "",
            )

        obs = env.step(SQLAction(query=query))

        feedback = obs.metadata.get("feedback", "")
        reward_display = round(obs.reward)  # show 0 or 1

        # Color the reward
        if reward_display == 1:
            reward_html = f'<span style="color:#22c55e;font-size:2em;font-weight:bold">{reward_display}</span>'
        else:
            reward_html = f'<span style="color:#ef4444;font-size:2em;font-weight:bold">{reward_display}</span>'

        if obs.done:
            rewards = obs.metadata.get("rewards", [])
            total = obs.metadata.get("total_reward", sum(rewards))
            status = f"**Episode Complete!**  |  **Total Reward:** {round(total)}  |  **Steps:** {len(rewards)}"
            next_question = "All questions answered! Click 'Start Task' to try again."
            progress = _build_progress_html(len(rewards), obs.total_questions, rewards)
        else:
            status = f"**Task:** {env_state['task_name']}  |  **Question {obs.question_index}/{obs.total_questions}**  |  **Attempts left:** {obs.steps_remaining}"
            next_question = obs.question
            # Collect rewards from episode so far
            rewards = env._rewards
            progress = _build_progress_html(obs.question_index - 1, obs.total_questions, rewards)

        result_display = obs.query_result if obs.query_result else "(no output)"
        if obs.error:
            result_display = f"ERROR: {obs.error}\n\n{result_display}"

        return (
            next_question,
            result_display,
            feedback,
            reward_html,
            status,
            progress,
        )

    def run_ground_truth(task_name):
        """Run all ground truth queries for demo purposes."""
        os.environ["SQL_ENV_TASK"] = task_name
        env = SQLEnvironment()
        obs = env.reset()
        task = _load_task(task_name)

        results = []
        for q in task["questions"]:
            obs = env.step(SQLAction(query=q["ground_truth_sql"]))
            results.append(f"**Q{len(results)+1}:** {q['question'][:80]}...\n- SQL: `{q['ground_truth_sql'][:100]}...`\n- Reward: **{round(obs.reward)}**\n")

        total = sum(env._rewards)
        results.append(f"\n---\n**Total: {round(total)} / {len(task['questions'])}**")
        return "\n".join(results)

    def preview_schema():
        """Show the database schema."""
        db = Database()
        db.initialize()
        schema = db.get_schema_description()
        db.close()
        return schema

    def _build_progress_html(current_q, total_q, rewards):
        """Build a visual progress bar."""
        bars = []
        for i in range(total_q):
            if i < len(rewards):
                r = rewards[i] if i < len(rewards) else 0
                if r >= 0.9:
                    color = "#22c55e"
                elif r >= 0.5:
                    color = "#eab308"
                else:
                    color = "#ef4444"
                bars.append(f'<div style="display:inline-block;width:18%;height:30px;background:{color};margin:1%;border-radius:4px;text-align:center;line-height:30px;color:white;font-weight:bold">Q{i+1}: {round(r)}</div>')
            elif i == len(rewards):
                bars.append(f'<div style="display:inline-block;width:18%;height:30px;background:#3b82f6;margin:1%;border-radius:4px;text-align:center;line-height:30px;color:white;font-weight:bold">Q{i+1} ▶</div>')
            else:
                bars.append(f'<div style="display:inline-block;width:18%;height:30px;background:#374151;margin:1%;border-radius:4px;text-align:center;line-height:30px;color:#9ca3af">Q{i+1}</div>')
        return "<div style='margin:10px 0'>" + "".join(bars) + "</div>"

    # Build the Gradio interface
    with gr.Blocks(title="SQLEnv — SQL Query Writing Environment") as app:

        gr.Markdown("""
        # 🗃️ SQLEnv — SQL Query Writing Environment
        Write SQL queries to answer natural language questions about an e-commerce database.
        Get graded with partial-credit scoring — syntax, columns, rows, and exact match.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                task_selector = gr.Dropdown(
                    choices=["basic_select", "join_aggregate", "advanced_analytics"],
                    value="basic_select",
                    label="Select Task Difficulty",
                )
                start_btn = gr.Button("🚀 Start Task", variant="primary", size="lg")
                status_md = gr.Markdown("Click **Start Task** to begin")
                progress_html = gr.HTML("")
                reward_html = gr.HTML('<span style="color:#666;font-size:2em">—</span>')
                gr.Markdown("---")
                feedback_box = gr.Textbox(label="Grader Feedback", lines=3, interactive=False)

            with gr.Column(scale=2):
                question_box = gr.Textbox(
                    label="Question",
                    lines=2,
                    interactive=False,
                    placeholder="Start a task to see the question...",
                )
                query_input = gr.Textbox(
                    label="Your SQL Query",
                    lines=5,
                    placeholder="SELECT name, age FROM customers WHERE age > 30 ORDER BY age DESC",
                    elem_classes=["query-input"],
                )
                submit_btn = gr.Button("▶ Execute & Grade", variant="primary", size="lg")
                result_box = gr.Textbox(
                    label="Query Result",
                    lines=10,
                    interactive=False,
                    elem_classes=["result-output"],
                )

        with gr.Accordion("📋 Database Schema", open=False):
            schema_box = gr.Textbox(
                label="Schema",
                lines=20,
                interactive=False,
                elem_classes=["result-output"],
            )

        with gr.Accordion("🏆 Run Ground Truth Demo", open=False):
            gr.Markdown("See how perfect SQL queries score on each task:")
            with gr.Row():
                demo_task = gr.Dropdown(
                    choices=["basic_select", "join_aggregate", "advanced_analytics"],
                    value="basic_select",
                    label="Task",
                )
                demo_btn = gr.Button("Run Demo")
            demo_output = gr.Markdown("")

        # Event handlers
        start_btn.click(
            fn=reset_env,
            inputs=[task_selector],
            outputs=[question_box, schema_box, query_input, result_box, feedback_box, reward_html, status_md, progress_html],
        )

        submit_btn.click(
            fn=submit_query,
            inputs=[query_input, question_box],
            outputs=[question_box, result_box, feedback_box, reward_html, status_md, progress_html],
        )

        # Also submit on Enter (Shift+Enter for newline)
        query_input.submit(
            fn=submit_query,
            inputs=[query_input, question_box],
            outputs=[question_box, result_box, feedback_box, reward_html, status_md, progress_html],
        )

        demo_btn.click(
            fn=run_ground_truth,
            inputs=[demo_task],
            outputs=[demo_output],
        )

    return app
