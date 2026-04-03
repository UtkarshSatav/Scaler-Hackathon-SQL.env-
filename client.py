"""SQL Query Writing Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import SQLAction, SQLObservation


class SQLEnvClient(
    EnvClient[SQLAction, SQLObservation, State]
):
    """
    Client for the SQL Query Writing Environment.

    Example:
        >>> with SQLEnvClient(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.question)
        ...     result = client.step(SQLAction(query="SELECT * FROM customers"))
        ...     print(result.observation.query_result)
    """

    def _step_payload(self, action: SQLAction) -> Dict:
        return {"query": action.query}

    def _parse_result(self, payload: Dict) -> StepResult[SQLObservation]:
        obs_data = payload.get("observation", {})
        observation = SQLObservation(
            task_name=obs_data.get("task_name", ""),
            question=obs_data.get("question", ""),
            schema_description=obs_data.get("schema_description", ""),
            query_result=obs_data.get("query_result", ""),
            error=obs_data.get("error", ""),
            steps_remaining=obs_data.get("steps_remaining", 0),
            question_index=obs_data.get("question_index", 0),
            total_questions=obs_data.get("total_questions", 0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
