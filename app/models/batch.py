"""TaskBatch model for database."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.task import Task


class TaskBatch(Base):
    """TaskBatch model for grouping tasks created together."""

    __tablename__ = "task_batches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID | None] = mapped_column(nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    # Relationship to tasks
    tasks: Mapped[list[Task]] = relationship("Task", back_populates="batch")

    def __repr__(self) -> str:
        """String representation of TaskBatch."""
        return f"<TaskBatch(id={self.id}, session_id={self.session_id})>"
