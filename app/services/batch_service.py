"""Batch service for CRUD operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.batch import TaskBatch
from app.models.task import Task
from app.schemas.batch import BatchCreate


class BatchService:
    """Service for managing task batches."""

    def __init__(self, db: AsyncSession):
        """Initialize batch service.

        Args:
            db: Database session
        """
        self.db = db

    async def create(self, batch_data: BatchCreate) -> TaskBatch:
        """Create a new batch with tasks.

        Args:
            batch_data: Batch creation data with tasks

        Returns:
            Created batch with tasks
        """
        # Create batch
        batch = TaskBatch(
            session_id=batch_data.session_id,
            reason=batch_data.reason,
        )
        self.db.add(batch)
        await self.db.flush()  # Get batch.id without committing

        # Create tasks
        for task_data in batch_data.tasks:
            task = Task(
                title=task_data.title,
                description=task_data.description,
                status=task_data.status,
                priority=task_data.priority,
                due_date=task_data.due_date,
                session_id=batch_data.session_id,  # Inherit from batch
                batch_id=batch.id,
            )
            self.db.add(task)

        await self.db.commit()
        await self.db.refresh(batch)

        # Load tasks relationship
        result = await self.db.execute(
            select(TaskBatch).where(TaskBatch.id == batch.id).options(selectinload(TaskBatch.tasks))
        )
        return result.scalar_one()

    async def get_by_id(self, batch_id: UUID) -> TaskBatch | None:
        """Get a batch by ID with tasks.

        Args:
            batch_id: Batch UUID

        Returns:
            Batch with tasks if found, None otherwise
        """
        result = await self.db.execute(
            select(TaskBatch).where(TaskBatch.id == batch_id).options(selectinload(TaskBatch.tasks))
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        session_id: UUID | None = None,
    ) -> tuple[list[TaskBatch], int]:
        """Get paginated list of batches.

        Args:
            page: Page number (1-indexed)
            session_id: Optional session ID filter

        Returns:
            Tuple of (batches list, total count)
        """
        limit = 10
        offset = (page - 1) * limit

        # Build queries
        query = select(TaskBatch).options(selectinload(TaskBatch.tasks))
        count_query = select(func.count()).select_from(TaskBatch)

        # Apply filters
        if session_id is not None:
            query = query.where(TaskBatch.session_id == session_id)
            count_query = count_query.where(TaskBatch.session_id == session_id)

        # Sort by created_at desc (newest first)
        query = query.order_by(TaskBatch.created_at.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute queries
        batches_result = await self.db.execute(query)
        batches = list(batches_result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return batches, total

    async def get_latest(self, session_id: UUID | None = None) -> TaskBatch | None:
        """Get the most recent batch.

        Args:
            session_id: Optional session ID filter

        Returns:
            Latest batch if found, None otherwise
        """
        query = (
            select(TaskBatch)
            .options(selectinload(TaskBatch.tasks))
            .order_by(TaskBatch.created_at.desc())
            .limit(1)
        )

        if session_id is not None:
            query = query.where(TaskBatch.session_id == session_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
