from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException, status
from pydantic import EmailStr

from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactModel
from src.database.models import User

from src.utils.birthday_check import is_birthday_in_next_N_days


def _handle_integrity_error(e: IntegrityError):
    if "unique_phone_user" in str(e.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with such phone number already exists for that user",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Data integrity error"
        )


class ContactService:
    """
    Service class wrapping the ContactRepository to handle contact-related business logic.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the contact service with a database session.

        :param db: The asynchronous database session.
        """
        self.repository = ContactRepository(db)

    async def get_contacts(
        self,
        skip: int,
        limit: int,
        user: User,
        first_name: str | None,
        last_name: str | None,
        email: EmailStr | None,
    ):
        """
        Retrieve and filter contacts for a specific user.

        :param skip: Number of contacts to skip.
        :param limit: Maximum number of contacts to return.
        :param user: The owner of the contacts.
        :param first_name: Optional first name to filter by.
        :param last_name: Optional last name to filter by.
        :param email: Optional email address to filter by.
        :return: A filtered list of Contact objects.
        """
        contacts = await self.repository.get_contacts(skip, limit, user)

        if first_name:
            contacts = [
                contact for contact in contacts if contact.first_name == first_name
            ]

        if last_name:
            contacts = [
                contact for contact in contacts if contact.last_name == last_name
            ]

        if email:
            contacts = [contact for contact in contacts if contact.email == email]

        return contacts

    async def get_contacts_birthday_next_7_days(
        self, skip: int, limit: int, user: User
    ):
        """
        Retrieve a list of contacts whose birthdays are within the next 7 days.

        :param skip: Number of contacts to skip.
        :param limit: Maximum number of contacts to return.
        :param user: The owner of the contacts.
        :return: A list of contacts celebrating birthdays within the next 7 days.
        """
        contacts = await self.repository.get_contacts(skip, limit, user)
        contacts = [
            contact
            for contact in contacts
            if is_birthday_in_next_N_days(7, contact.date_of_birth)
        ]

        return contacts

    async def get_contact(self, contact_id: int, user: User):
        """
        Retrieve a specific contact by its ID.

        :param contact_id: The ID of the contact.
        :param user: The owner of the contact.
        :return: The Contact object if found, otherwise None.
        """
        return await self.repository.get_contact_by_id(contact_id, user)

    async def create_contact(self, body: ContactModel, user: User):
        """
        Create a new contact. Handles integrity errors if the contact already exists.

        :param body: The schema representing the new contact's details.
        :param user: The owner of the new contact.
        :return: The newly created Contact object.
        """
        try:
            return await self.repository.create_contact(body, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def update_contact(self, contact_id: int, body: ContactModel, user: User):
        """
        Update an existing contact. Handles database integrity errors.

        :param contact_id: The ID of the contact to update.
        :param body: The updated schema data.
        :param user: The owner of the contact.
        :return: The updated Contact object if found, otherwise None.
        """
        try:
            return await self.repository.update_contact(contact_id, body, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def remove_contact(self, contact_id: int, user: User):
        """
        Remove/Delete a contact.

        :param contact_id: The ID of the contact to remove.
        :param user: The owner of the contact.
        :return: The removed Contact object if found, otherwise None.
        """
        return await self.repository.remove_contact(contact_id, user)
