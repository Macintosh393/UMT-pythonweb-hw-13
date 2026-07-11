from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.users import UserRepository
from src.schemas.users import UserCreate


class UserService:
    """
    Service class wrapping the UserRepository to handle user-related business logic.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the user service with a database session.

        :param db: The asynchronous database session.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Create a new user.

        :param body: The schema representing user creation details.
        :return: The created User object.
        """
        return await self.repository.create_user(body)

    async def get_user_by_id(self, user_id: int):
        """
        Retrieve a user by their ID.

        :param user_id: The ID of the user.
        :return: The User object if found, otherwise None.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """
        Retrieve a user by their username.

        :param username: The username of the user.
        :return: The User object if found, otherwise None.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        """
        Retrieve a user by their email.

        :param email: The email address of the user.
        :return: The User object if found, otherwise None.
        """
        return await self.repository.get_user_by_email(email)

    async def confirm_email(self, email: str):
        """
        Confirm user's email verification status.

        :param email: The email address to confirm.
        """
        return await self.repository.confirm_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """
        Update a user's avatar image URL.

        :param email: The email address of the user.
        :param url: The new avatar URL.
        :return: The updated User object.
        """
        return await self.repository.update_avatar_url(email, url)

    async def update_password(self, email: str, hashed_password: str):
        """
        Update a user's password.

        :param email: The email address of the user.
        :param hashed_password: The already hashed new password.
        """
        return await self.repository.update_password(email, hashed_password)
