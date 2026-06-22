"""Generic repository base implementing the repository pattern."""
from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Async CRUD helpers shared by all repositories.

    Repositories ``flush`` but never ``commit`` — transaction boundaries are
    owned by the unit of work (the request/session or the worker loop).
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def add_all(self, entities: list[ModelT]) -> list[ModelT]:
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        stmt = (
            select(self.model)
            .order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return int(await self.session.scalar(stmt) or 0)

    async def delete(self, entity_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )
