from fastapi import APIRouter, HTTPException, Request, status
import logging

from fastapi import APIRouter, HTTPException, Request, status
from groq import AsyncGroq
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from src.app.api.routes.instruction import route_instruction
from src.app.api.routes.tasks import (
    create_task,
    delete_task,
    get_tasks,
    replace_task,
    update_task,
)
from src.app.core.config import get_settings
from src.app.schemas.voice import (
    InstructionPayload,
    InstructionRequest,
    TaskCreate,
    TaskReplace,
    TaskUpdate,
    TranscribeFlowResponse,
)
from src.app.utils.language import normalize_transcription_language

router = APIRouter(tags=["transcribe"])
logger = logging.getLogger(__name__)


@router.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/transcribe", response_model=TranscribeFlowResponse)
async def transcribe_and_run_flow(request: Request) -> TranscribeFlowResponse:
    content_type = request.headers.get("content-type", "").lower()

    if content_type.startswith("application/json"):
        try:
            body = await request.json()
            instruction_request = InstructionRequest.model_validate(body)
        except (ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="JSON body must contain a non-empty 'transcription' string.",
            ) from exc
        transcription = instruction_request.transcription.strip()
    elif content_type.startswith("multipart/form-data"):
        try:
            form = await request.form()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not read the uploaded form data.",
            ) from exc

        audio = form.get("file")
        if not isinstance(audio, UploadFile):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Multipart form must contain an audio file in the 'file' field.",
            )

        language = normalize_transcription_language(form.get("language"))
        transcription = await _transcribe_audio(audio, language)
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Send an audio file as multipart/form-data or JSON with 'transcription'.",
        )

    routed_instruction = await run_in_threadpool(
        route_instruction,
        InstructionRequest(transcription=transcription),
    )
    result = _execute_task_instruction(routed_instruction)

    return TranscribeFlowResponse(
        transcription=transcription,
        instruction=routed_instruction,
        result=result,
    )


async def _transcribe_audio(audio: UploadFile, language: str | None) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audio transcription is not configured: GROQ_API_KEY is missing.",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded audio file is empty.",
        )

    try:
        client = AsyncGroq(
            api_key=settings.groq_api_key,
            timeout=settings.request_timeout_seconds,
        )
        transcription = await client.audio.transcriptions.create(
            file=(audio.filename or "recording.webm", audio_bytes),
            model=settings.groq_transcription_model,
            language=language,
        )
    except Exception as exc:
        logger.exception("Groq audio transcription request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The speech-to-text service failed to transcribe the audio.",
        ) from exc
    finally:
        await audio.close()

    text = transcription.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No speech was recognized in the uploaded audio.",
        )
    return text


def _execute_task_instruction(instruction: InstructionPayload) -> object:
    params = instruction.params
    method = instruction.method.upper()
    endpoint = instruction.endpoint.rstrip("/")

    if endpoint == "/tasks" and method == "GET":
        return get_tasks()
    if endpoint == "/tasks" and method == "POST":
        return create_task(TaskCreate.model_validate(params))

    task_id = params["task_id"]
    task_fields = {key: value for key, value in params.items() if key != "task_id"}
    if endpoint == "/tasks/{task_id}" and method == "PUT":
        return replace_task(task_id, TaskReplace.model_validate(task_fields))
    if endpoint == "/tasks/{task_id}" and method == "PATCH":
        return update_task(task_id, TaskUpdate.model_validate(task_fields))
    if endpoint == "/tasks/{task_id}" and method == "DELETE":
        return delete_task(task_id)

    # route_instruction validates this before it can reach execution.
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="The instruction selected an unsupported task operation.",
    )
