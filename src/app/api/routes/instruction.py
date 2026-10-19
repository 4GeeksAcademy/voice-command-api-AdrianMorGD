import json
import logging

from fastapi import APIRouter, HTTPException, status
from groq import Groq
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
logger = logging.getLogger(__name__)


@router.post("/instruction", response_model=InstructionPayload)
def route_instruction(
    payload: InstructionRequest,
) -> InstructionPayload:
    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq LLM is not configured. Set GROQ_API_KEY.",
        )

    try:
        client = Groq(
            api_key=settings.groq_api_key,
            timeout=settings.request_timeout_seconds,
        )
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You route natural-language requests for a task-list API. "
                        "Return only one JSON object with exactly these keys: "
                        "endpoint, method, params. No Markdown or explanations. "
                        "The endpoint value must be only the exact path, never "
                        "include the HTTP method in endpoint. Supported outputs: "
                        "list: {\"endpoint\":\"/tasks\",\"method\":\"GET\","
                        "\"params\":{}}; create: endpoint /tasks, method POST, "
                        "params {title, optional done}; replace: endpoint "
                        "/tasks/{task_id}, method PUT, params {task_id, title, done}; "
                        "update: endpoint /tasks/{task_id}, method PATCH, params "
                        "{task_id, and only the changed title and/or done}; delete: "
                        "endpoint /tasks/{task_id}, method DELETE, params {task_id}. "
                        "task_id must be a positive integer. Never invent an ID or "
                        "task details not provided."
                    ),
                },
                {"role": "user", "content": payload.transcription},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
    except Exception as exc:
        logger.exception("Groq chat completion request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The Groq LLM service failed to return a valid chat completion.",
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
            detail="The Groq LLM returned invalid routing JSON for the task API.",
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
