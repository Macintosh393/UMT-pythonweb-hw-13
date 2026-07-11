import pytest
from datetime import date
from src.repository.contacts import ContactRepository
from src.repository.users import UserRepository
from src.schemas.contacts import ContactModel
from src.schemas.users import UserCreate
from src.database.models import Contact

@pytest.mark.asyncio
async def test_contacts_operations(db_session):
    # Setup user
    user_repo = UserRepository(db_session)
    user_data = UserCreate(
        username="contactowner",
        email="owner@example.com",
        password="hashedpassword",
    )
    user = await user_repo.create_user(user_data)

    contact_repo = ContactRepository(db_session)
    
    # 1. Test Create Contact
    contact_data = ContactModel(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+380991234567",
        date_of_birth=date(1990, 5, 15),
    )
    contact = await contact_repo.create_contact(contact_data, user)
    assert contact.id is not None
    assert contact.first_name == "John"
    assert contact.user_id == user.id

    # 2. Test Get Contacts
    contacts = await contact_repo.get_contacts(skip=0, limit=10, user=user)
    assert len(contacts) == 1
    assert contacts[0].first_name == "John"

    # 3. Test Get Contact by ID
    fetched_contact = await contact_repo.get_contact_by_id(contact.id, user)
    assert fetched_contact is not None
    assert fetched_contact.first_name == "John"

    # 4. Test Update Contact
    update_data = ContactModel(
        first_name="Johnny",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+380991234567",
        date_of_birth=date(1990, 5, 15),
    )
    updated_contact = await contact_repo.update_contact(contact.id, update_data, user)
    assert updated_contact is not None
    assert updated_contact.first_name == "Johnny"

    # 5. Test Remove Contact
    removed_contact = await contact_repo.remove_contact(contact.id, user)
    assert removed_contact is not None
    
    # Verify removal
    fetched_again = await contact_repo.get_contact_by_id(contact.id, user)
    assert fetched_again is None
