from fastapi import APIRouter, HTTPException, status

from src.app.schemas.voice import Task, TaskCreate, TaskReplace, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

# In-memory storage for the lifetime of this backend process.
tasks: list[dict[str, int | str | bool]] = []
_next_task_id = 1


@router.get("", response_model=list[Task])
def get_tasks() -> list[Task]:
    return [Task(**task) for task in tasks]


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    global _next_task_id

    task = {
        "id": _next_task_id,
        "title": payload.title,
        "done": payload.done,
    }
    tasks.append(task)
    _next_task_id += 1

    return Task(**task)


@router.put("/{task_id}", response_model=Task)
def replace_task(
    task_id: int,
    payload: TaskReplace,
) -> Task:
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            replacement = {
                "id": task_id,
                "title": payload.title,
                "done": payload.done,
            }
            tasks[index] = replacement
            return Task(**replacement)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task with id {task_id} not found.",
    )


@router.patch("/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    payload: TaskUpdate,
) -> Task:
    for task in tasks:
        if task["id"] == task_id:
            updates = payload.model_dump(exclude_unset=True)
            if not updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide at least one field to update: title or done.",
                )

            task.update(updates)
            return Task(**task)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task with id {task_id} not found.",
    )


@router.delete("/{task_id}")
def delete_task(task_id: int) -> dict[str, str]:
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[index]
            return {"detail": f"Task with id {task_id} deleted."}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task with id {task_id} not found.",
    )


def raise_not_implemented(endpoint: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Template endpoint pending implementation: {endpoint}",
    )
