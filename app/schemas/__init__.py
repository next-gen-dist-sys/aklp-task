"""Pydantic schemas package."""

from app.schemas.batch import BatchCreate, BatchListResponse, BatchResponse
from app.schemas.responses import (
    BaseResponse,
    ErrorResponse,
    HealthResponse,
    SuccessResponse,
)
from app.schemas.task import (
    TaskBulkDelete,
    TaskBulkDeleteResponse,
    TaskBulkUpdate,
    TaskBulkUpdateItem,
    TaskBulkUpdateResponse,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)

__all__ = [
    # Task schemas
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    "TaskBulkUpdate",
    "TaskBulkUpdateItem",
    "TaskBulkUpdateResponse",
    "TaskBulkDelete",
    "TaskBulkDeleteResponse",
    # Batch schemas
    "BatchCreate",
    "BatchResponse",
    "BatchListResponse",
    # Response schemas
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthResponse",
]
