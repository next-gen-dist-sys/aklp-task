"""Pydantic schemas for Batch API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.schemas.task import TaskCreate, TaskResponse


class BatchCreate(BaseModel):
    """Schema for creating a new batch with tasks."""

    session_id: UUID | None = Field(None, description="AI session ID (optional)")
    tasks: list[TaskCreate] = Field(..., min_length=1, description="List of tasks to create")


class BatchResponse(BaseModel):
    """Schema for batch response."""

    id: UUID
    session_id: UUID | None
    created_at: datetime
    tasks: list[TaskResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# 이건 필요없을 것 같긴 한데 일단
class BatchListResponse(BaseModel):
    """Schema for paginated batch list response."""

    items: list[BatchResponse]
    total: int = Field(..., description="Total number of batches")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")

    @computed_field  # type: ignore
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.limit - 1) // self.limit

    @computed_field  # type: ignore
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @computed_field  # type: ignore
    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
