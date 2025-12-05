"""Pydantic schemas for Task API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: str | None = Field(
        None, max_length=1000, description="Task description (optional)"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Task status (defaults to pending)"
    )
    priority: TaskPriority | None = Field(None, description="Task priority (optional)")
    due_date: datetime | None = Field(None, description="Task due date (optional)")
    session_id: UUID | None = Field(None, description="AI session ID (optional)")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task.

    All fields are optional to support partial updates.
    """

    title: str | None = Field(None, min_length=1, max_length=255, description="Task title")
    description: str | None = Field(None, max_length=1000, description="Task description")
    status: TaskStatus | None = Field(None, description="Task status")
    priority: TaskPriority | None = Field(None, description="Task priority")
    due_date: datetime | None = Field(None, description="Task due date")


class TaskResponse(BaseModel):
    """Schema for task response."""

    id: UUID
    session_id: UUID | None
    batch_id: UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority | None
    due_date: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""

    items: list[TaskResponse]
    total: int = Field(..., description="Total number of tasks")
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
