"""User Repository for Authentication and Account Management."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User, UserRole
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.user import UserCreate


class UserRepository(BaseRepository[User]):
    """Data access layer for User entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Looks up a user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create_user(self, user_in: UserCreate, hashed_password: str) -> User:
        """Creates and stores a new user record."""
        db_user = User(
            email=user_in.email.lower(),
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role
        )
        return await self.create(db_user)
