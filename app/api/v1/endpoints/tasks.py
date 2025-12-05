"""Task API endpoints."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DBSession
from app.models.task import TaskStatus
from app.schemas.task import (
    TaskBulkDelete,
    TaskBulkDeleteResponse,
    TaskBulkUpdate,
    TaskBulkUpdateResponse,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter()

# Fixed limit: 10 tasks per page
TASKS_PER_PAGE = 10


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    task_data: TaskCreate,
    db: DBSession,
) -> TaskResponse:
    """Create a new task.

    Args:
        task_data: Task creation data
        db: Database session

    Returns:
        Created task
    """
    service = TaskService(db)
    task = await service.create(task_data)
    return TaskResponse.model_validate(task)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="Get list of tasks",
)
async def list_tasks(
    db: DBSession,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    status: TaskStatus | None = Query(default=None, description="Filter by status"),
    session_id: UUID | None = Query(default=None, description="Filter by session ID"),
    sort_by: Literal["updated_at", "created_at", "due_date", "priority", "status"] = Query(
        default="updated_at", description="Sort field"
    ),
    order: Literal["asc", "desc"] = Query(default="desc", description="Sort order"),
) -> TaskListResponse:
    """Get paginated list of tasks with filtering and sorting.

    Args:
        db: Database session
        page: Page number (1-indexed)
        status: Optional status filter
        session_id: Optional session ID filter
        sort_by: Sort field (default: updated_at)
        order: Sort order (default: desc)

    Returns:
        Paginated task list
    """
    service = TaskService(db)
    tasks, total = await service.get_list(
        page=page,
        status=status,
        session_id=session_id,
        sort_by=sort_by,
        order=order,
    )

    return TaskListResponse(
        items=[TaskResponse.model_validate(task) for task in tasks],
        total=total,
        page=page,
        limit=TASKS_PER_PAGE,
    )


# Bulk operations must come before /{task_id} routes to avoid path conflicts
@router.put(
    "/bulk",
    response_model=TaskBulkUpdateResponse,
    summary="Update multiple tasks",
)
async def bulk_update_tasks(
    bulk_data: TaskBulkUpdate,
    db: DBSession,
) -> TaskBulkUpdateResponse:
    """Update multiple tasks at once.

    Args:
        bulk_data: Bulk update data with list of tasks
        db: Database session

    Returns:
        List of updated tasks
    """
    service = TaskService(db)
    updated_tasks = await service.bulk_update(bulk_data)

    return TaskBulkUpdateResponse(
        updated=[TaskResponse.model_validate(task) for task in updated_tasks]
    )


@router.delete(
    "/bulk",
    response_model=TaskBulkDeleteResponse,
    summary="Delete multiple tasks",
)
async def bulk_delete_tasks(
    bulk_data: TaskBulkDelete,
    db: DBSession,
) -> TaskBulkDeleteResponse:
    """Delete multiple tasks at once.

    Args:
        bulk_data: Bulk delete data with list of task IDs
        db: Database session

    Returns:
        Number of deleted tasks
    """
    service = TaskService(db)
    deleted_count = await service.bulk_delete(bulk_data.ids)

    return TaskBulkDeleteResponse(deleted_count=deleted_count)


# Single task operations with path parameter
@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
)
async def get_task(
    task_id: UUID,
    db: DBSession,
) -> TaskResponse:
    """Get a task by ID.

    Args:
        task_id: Task UUID
        db: Database session

    Returns:
        Task details

    Raises:
        HTTPException: 404 if task not found
    """
    service = TaskService(db)
    task = await service.get_by_id(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    return TaskResponse.model_validate(task)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    db: DBSession,
) -> TaskResponse:
    """Update a task.

    Automatically manages completed_at:
    - Sets to current time when status changes to completed
    - Sets to None when status changes from completed to other

    Args:
        task_id: Task UUID
        task_data: Task update data
        db: Database session

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found
    """
    service = TaskService(db)
    task = await service.update(task_id, task_data)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: UUID,
    db: DBSession,
) -> None:
    """Delete a task.

    Args:
        task_id: Task UUID
        db: Database session

    Raises:
        HTTPException: 404 if task not found
    """
    service = TaskService(db)
    deleted = await service.delete(task_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
