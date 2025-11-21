"""Task service for CRUD operations."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service for managing tasks."""

    def __init__(self, db: AsyncSession):
        """Initialize task service.

        Args:
            db: Database session
        """
        self.db = db

    async def create(self, task_data: TaskCreate) -> Task:
        """Create a new task.

        Args:
            task_data: Task creation data

        Returns:
            Created task
        """
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            session_id=task_data.session_id,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_by_id(self, task_id: UUID) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: Task UUID

        Returns:
            Task if found, None otherwise
        """
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        status: TaskStatus | None = None,
        session_id: UUID | None = None,
        sort_by: Literal[
            "updated_at", "created_at", "due_date", "priority", "status"
        ] = "updated_at",
        order: Literal["asc", "desc"] = "desc",
    ) -> tuple[list[Task], int]:
        """Get paginated list of tasks with filtering and sorting.

        Args:
            page: Page number (1-indexed)
            status: Optional status filter
            session_id: Optional session ID filter
            sort_by: Sort field (default: updated_at)
            order: Sort order (default: desc)

        Returns:
            Tuple of (tasks list, total count)
        """
        # Fixed limit: 10 tasks per page
        limit = 10
        # Calculate offset: (page - 1) * limit
        offset = (page - 1) * limit

        # Build base query
        query = select(Task)
        count_query = select(func.count()).select_from(Task)

        # Apply filters
        if status is not None:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)
        if session_id is not None:
            query = query.where(Task.session_id == session_id)
            count_query = count_query.where(Task.session_id == session_id)

        # Apply sorting
        query = self._apply_sorting(query, sort_by, order)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute queries
        tasks_result = await self.db.execute(query)
        tasks = list(tasks_result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return tasks, total

    def _apply_sorting(
        self,
        query: Select[Any],
        sort_by: Literal["updated_at", "created_at", "due_date", "priority", "status"],
        order: Literal["asc", "desc"],
    ) -> Select[Any]:
        """Apply sorting to query with proper NULL handling.

        Args:
            query: SQLAlchemy query
            sort_by: Sort field
            order: Sort order

        Returns:
            Query with sorting applied
        """
        if sort_by == "priority":
            # Priority sorting: custom order with NULL at the end
            if order == "asc":
                # low > medium > high > NULL
                return query.order_by(
                    case(
                        (Task.priority == TaskPriority.LOW, 1),
                        (Task.priority == TaskPriority.MEDIUM, 2),
                        (Task.priority == TaskPriority.HIGH, 3),
                        (Task.priority.is_(None), 4),
                    )
                )
            else:  # desc
                # high > medium > low > NULL
                return query.order_by(
                    case(
                        (Task.priority == TaskPriority.HIGH, 1),
                        (Task.priority == TaskPriority.MEDIUM, 2),
                        (Task.priority == TaskPriority.LOW, 3),
                        (Task.priority.is_(None), 4),
                    )
                )
        elif sort_by == "status":
            # Status sorting: custom order
            if order == "asc":
                # pending > in_progress > completed
                return query.order_by(
                    case(
                        (Task.status == TaskStatus.PENDING, 1),
                        (Task.status == TaskStatus.IN_PROGRESS, 2),
                        (Task.status == TaskStatus.COMPLETED, 3),
                    )
                )
            else:  # desc
                # completed > in_progress > pending
                return query.order_by(
                    case(
                        (Task.status == TaskStatus.COMPLETED, 1),
                        (Task.status == TaskStatus.IN_PROGRESS, 2),
                        (Task.status == TaskStatus.PENDING, 3),
                    )
                )
        else:
            # Standard column sorting with NULL at the end
            sort_column = getattr(Task, sort_by)
            if order == "asc":
                return query.order_by(sort_column.asc().nullslast())
            else:  # desc
                return query.order_by(sort_column.desc().nullslast())

    async def update(self, task_id: UUID, task_data: TaskUpdate) -> Task | None:
        """Update a task.

        Automatically manages completed_at:
        - Sets to current time when status changes to completed
        - Sets to None when status changes from completed to other

        Args:
            task_id: Task UUID
            task_data: Task update data

        Returns:
            Updated task if found, None otherwise
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return None

        # Store old status for comparison
        old_status = task.status

        # Update fields if provided
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.status is not None:
            task.status = task_data.status
        if task_data.priority is not None:
            task.priority = task_data.priority
        if task_data.due_date is not None:
            task.due_date = task_data.due_date

        # Handle completed_at auto-management
        if task_data.status is not None:
            new_status = task_data.status

            # completed로 변경: completed_at 자동 설정
            if new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                task.completed_at = datetime.now(UTC)

            # completed에서 다른 상태로: completed_at 초기화
            elif old_status == TaskStatus.COMPLETED and new_status != TaskStatus.COMPLETED:
                task.completed_at = None

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete(self, task_id: UUID) -> bool:
        """Delete a task.

        Args:
            task_id: Task UUID

        Returns:
            True if deleted, False if not found
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return False

        await self.db.delete(task)
        await self.db.commit()
        return True
