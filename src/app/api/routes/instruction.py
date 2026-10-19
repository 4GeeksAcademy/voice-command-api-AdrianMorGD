import json

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from src.app.core.config import get_settings
from src.app.schemas.voice import (
    InstructionPayload,
    InstructionRequest,
    TaskCreate,
    TaskReplace,
    TaskUpdate,
)

router = APIRouter(tags=["instruction"])


@router.post("/instruction", response_model=InstructionPayload)
def route_instruction(
    payload: InstructionRequest,
) -> InstructionPayload:
    settings = get_settings()
    if not (settings.luna_api_key and settings.luna_base_url and settings.luna_model):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Luna LLM is not configured. Set LITE_LLM_API_KEY, "
                "LITE_LLM_BASE_URL, and LITE_LLM_MODEL."
            ),
        )

    base_url = settings.luna_base_url.rstrip("/")
    completion_url = (
        base_url
        if base_url.endswith("/chat/completions")
        else f"{base_url}/chat/completions"
    )

    try:
        response = httpx.post(
            completion_url,
            headers={
                "Authorization": f"Bearer {settings.luna_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.luna_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You route natural-language requests for a task-list API. "
                            "Return only one JSON object with exactly these keys: "
                            "endpoint, method, params. No Markdown or explanations. "
                            "Allowed actions: list tasks: GET /tasks with empty params; "
                            "create task: POST /tasks with {title, optional done}; "
                            "replace task: PUT /tasks/{task_id} with task_id, title, done; "
                            "update task: PATCH /tasks/{task_id} with task_id and only "
                            "the changed title and/or done; delete task: DELETE "
                            "/tasks/{task_id} with task_id. task_id must be a positive "
                            "integer. Never invent an ID or task details not provided."
                        ),
                    },
                    {"role": "user", "content": payload.transcription},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The Luna LLM service failed to return a valid chat completion.",
        ) from exc

    try:
        if not content:
            raise ValueError("The LLM returned an empty response.")

        instruction = InstructionPayload.model_validate(json.loads(content))
        instruction.method = instruction.method.upper()
        _validate_instruction(instruction)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The Luna LLM returned invalid routing JSON for the task API.",
        ) from exc

    return instruction


def _validate_instruction(instruction: InstructionPayload) -> None:
    """Reject model output that does not map to a supported task operation."""
    endpoint = instruction.endpoint.rstrip("/")
    method = instruction.method
    params = instruction.params

    if endpoint == "/tasks" and method == "GET":
        if params:
            raise ValueError("GET /tasks does not accept parameters.")
        return

    if endpoint == "/tasks" and method == "POST":
        TaskCreate.model_validate(params)
        return

    if endpoint == "/tasks/{task_id}" and method in {"PUT", "PATCH", "DELETE"}:
        task_id = params.get("task_id")
        if isinstance(task_id, bool) or not isinstance(task_id, int) or task_id < 1:
            raise ValueError("A positive task_id is required.")

        task_fields = {key: value for key, value in params.items() if key != "task_id"}
        if method == "PUT":
            TaskReplace.model_validate(task_fields)
        elif method == "PATCH":
            TaskUpdate.model_validate(task_fields)
        elif task_fields:
            raise ValueError("DELETE does not accept task fields.")
        return

    raise ValueError("Unsupported task endpoint or HTTP method.")
