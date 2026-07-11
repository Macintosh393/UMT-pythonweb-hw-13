from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.contacts import ContactModel


class ContactRepository:
    """
    Repository class for managing contacts in the database.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the repository with a database session.

        :param db: The asynchronous database session.
        """
        self.db = db

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        """
        Retrieve a list of contacts for a specific user.

        :param skip: Number of contacts to skip.
        :param limit: Maximum number of contacts to return.
        :param user: The owner of the contacts.
        :return: A list of Contact objects.
        """
        stmt = select(Contact).filter_by(user=user).offset(skip).limit(limit)
        contacts = await self.db.execute(stmt)

        return list(contacts.scalars().all())

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Retrieve a specific contact by its ID and owner.

        :param contact_id: The ID of the contact.
        :param user: The owner of the contact.
        :return: The Contact object if found, otherwise None.
        """
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)

        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        """
        Create a new contact for a user.

        :param body: The schema representing the new contact's details.
        :param user: The owner of the new contact.
        :return: The newly created Contact object.
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        """
        Update an existing contact's details.

        :param contact_id: The ID of the contact to update.
        :param body: The updated schema data.
        :param user: The owner of the contact.
        :return: The updated Contact object if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Remove/Delete a contact from the database.

        :param contact_id: The ID of the contact to remove.
        :param user: The owner of the contact.
        :return: The removed Contact object if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()

        return contact
