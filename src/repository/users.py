from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import redis_client
from src.database.models import User
from src.schemas.users import UserCreate


class UserRepository:
    """
    Repository class for managing user accounts in the database.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the user repository with a database session.

        :param db: The asynchronous database session.
        """
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by their ID.

        :param user_id: The ID of the user.
        :return: The User object if found, otherwise None.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        :param username: The username of the user.
        :return: The User object if found, otherwise None.
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address.

        :param email: The email address of the user.
        :return: The User object if found, otherwise None.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate) -> User:
        """
        Create a new user account in the database.

        :param body: The schema representing the new user's details.
        :return: The newly created User object.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirm_email(self, email: str) -> None:
        """
        Confirm a user's email address.

        :param email: The email address to confirm.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.confirmed = True
            await self.db.commit()
            try:
                await redis_client.delete(f"user:{user.username}")
            except Exception:
                pass

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update the avatar URL of a specific user.

        :param email: The email address of the user.
        :param url: The new avatar URL.
        :return: The updated User object.
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise
        user.avatar_url = url
        await self.db.commit()
        await self.db.refresh(user)
        try:
            await redis_client.delete(f"user:{user.username}")
        except Exception:
            pass
        return user

    async def update_password(self, email: str, hashed_password: str) -> None:
        """
        Update the user's password in the database and invalidate their cache.

        :param email: The email address of the user.
        :param hashed_password: The already hashed new password.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.hashed_password = hashed_password
            await self.db.commit()
            try:
                await redis_client.delete(f"user:{user.username}")
            except Exception:
                pass
