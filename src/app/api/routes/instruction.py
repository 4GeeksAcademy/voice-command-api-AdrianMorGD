import json

from fastapi import APIRouter, HTTPException, status
from groq import Groq
from pydantic import ValidationError

from src.app.core.config import get_settings
from src.app.schemas.voice import InstructionPayload, InstructionRequest, TaskCreate

router = APIRouter(tags=["instruction"])


@router.post("/instruction", response_model=InstructionPayload)
def route_instruction(
    payload: InstructionRequest,
) -> InstructionPayload:
    settings = get_settings()
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
                    "Convert the user's task instruction into a routing object. "
                    "Return only a JSON object with exactly these keys: endpoint, "
                    "method, params. Do not return Markdown or explanations. "
                    "For creating a task, use endpoint '/tasks', method 'POST', "
                    "and params containing a non-empty title and optional done boolean."
                ),
            },
            {"role": "user", "content": payload.transcription},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        if not content:
            raise ValueError("The LLM returned an empty response.")

        instruction = InstructionPayload.model_validate(json.loads(content))
        if instruction.endpoint == "/tasks" and instruction.method.upper() == "POST":
            TaskCreate.model_validate(instruction.params)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The LLM returned an invalid instruction. Expected valid JSON for task creation.",
        ) from exc

    return instruction
