"""Target Repository for RAG Application Configurations."""

import json
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.target import Target
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.target import TargetCreate, TargetUpdate


class TargetRepository(BaseRepository[Target]):
    """Data access layer for Target RAG configurations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Target, session)

    async def get_by_name(self, name: str) -> Optional[Target]:
        """Looks up a target by its name."""
        result = await self.session.execute(
            select(Target).where(Target.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active_targets(self, skip: int = 0, limit: int = 100) -> List[Target]:
        """Returns all active targets."""
        result = await self.session.execute(
            select(Target).where(Target.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create_target(self, target_in: TargetCreate) -> Target:
        """Persists a new Target configuration."""
        db_target = Target(
            name=target_in.name,
            description=target_in.description,
            target_url=str(target_in.target_url),
            api_key=target_in.api_key,
            custom_headers_json=json.dumps(target_in.custom_headers or {}),
            request_mapping_json=json.dumps(target_in.request_mapping or {}),
            response_mapping_json=json.dumps(target_in.response_mapping or {})
        )
        return await self.create(db_target)

    async def update_target(self, target_id: str, target_in: TargetUpdate) -> Optional[Target]:
        """Updates target attributes."""
        db_target = await self.get(target_id)
        if not db_target:
            return None

        update_data = target_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ["custom_headers", "request_mapping", "response_mapping"] and value is not None:
                setattr(db_target, f"{field}_json", json.dumps(value))
            elif field == "target_url" and value is not None:
                db_target.target_url = str(value)
            elif value is not None:
                setattr(db_target, field, value)

        await self.session.flush()
        return db_target
