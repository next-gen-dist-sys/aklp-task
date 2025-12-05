"""Batch API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DBSession
from app.schemas.batch import BatchCreate, BatchListResponse, BatchResponse
from app.schemas.task import TaskResponse
from app.services.batch_service import BatchService

router = APIRouter()

BATCHES_PER_PAGE = 10


@router.post(
    "",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new batch with tasks",
)
async def create_batch(
    batch_data: BatchCreate,
    db: DBSession,
) -> BatchResponse:
    """Create a new batch with multiple tasks.

    Args:
        batch_data: Batch creation data with tasks
        db: Database session

    Returns:
        Created batch with tasks
    """
    service = BatchService(db)
    batch = await service.create(batch_data)

    return BatchResponse(
        id=batch.id,
        session_id=batch.session_id,
        reason=batch.reason,
        created_at=batch.created_at,
        tasks=[TaskResponse.model_validate(task) for task in batch.tasks],
    )


@router.get(
    "",
    response_model=BatchListResponse,
    summary="Get list of batches",
)
async def list_batches(
    db: DBSession,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    session_id: UUID | None = Query(default=None, description="Filter by session ID"),
) -> BatchListResponse:
    """Get paginated list of batches.

    Args:
        db: Database session
        page: Page number (1-indexed)
        session_id: Optional session ID filter

    Returns:
        Paginated batch list
    """
    service = BatchService(db)
    batches, total = await service.get_list(page=page, session_id=session_id)

    return BatchListResponse(
        items=[
            BatchResponse(
                id=batch.id,
                session_id=batch.session_id,
                reason=batch.reason,
                created_at=batch.created_at,
                tasks=[TaskResponse.model_validate(task) for task in batch.tasks],
            )
            for batch in batches
        ],
        total=total,
        page=page,
        limit=BATCHES_PER_PAGE,
    )


@router.get(
    "/latest",
    response_model=BatchResponse | None,
    summary="Get the latest batch",
)
async def get_latest_batch(
    db: DBSession,
    session_id: UUID | None = Query(default=None, description="Filter by session ID"),
) -> BatchResponse | None:
    """Get the most recent batch.

    Args:
        db: Database session
        session_id: Optional session ID filter

    Returns:
        Latest batch if found, None otherwise
    """
    service = BatchService(db)
    batch = await service.get_latest(session_id=session_id)

    if batch is None:
        return None

    return BatchResponse(
        id=batch.id,
        session_id=batch.session_id,
        reason=batch.reason,
        created_at=batch.created_at,
        tasks=[TaskResponse.model_validate(task) for task in batch.tasks],
    )


@router.get(
    "/{batch_id}",
    response_model=BatchResponse,
    summary="Get a batch by ID",
)
async def get_batch(
    batch_id: UUID,
    db: DBSession,
) -> BatchResponse:
    """Get a batch by ID with tasks.

    Args:
        batch_id: Batch UUID
        db: Database session

    Returns:
        Batch with tasks

    Raises:
        HTTPException: 404 if batch not found
    """
    service = BatchService(db)
    batch = await service.get_by_id(batch_id)

    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    return BatchResponse(
        id=batch.id,
        session_id=batch.session_id,
        reason=batch.reason,
        created_at=batch.created_at,
        tasks=[TaskResponse.model_validate(task) for task in batch.tasks],
    )
