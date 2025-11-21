"""Task model for database."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(Base):
    """Task model for managing todo items."""

    __tablename__ = "tasks"

    # Required fields
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(nullable=False, default=TaskStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Optional fields (nullable)
    session_id: Mapped[UUID | None] = mapped_column(nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True, default=None)
    priority: Mapped[TaskPriority | None] = mapped_column(nullable=True, default=None)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self) -> str:
        """String representation of Task."""
        return f"<Task(id={self.id}, title={self.title!r}, status={self.status.value})>"
