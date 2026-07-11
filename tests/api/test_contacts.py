import pytest
from src.services.auth import create_email_token

async def get_auth_header(client, username, email):
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "password123"}
    )
    token = await create_email_token({"sub": email})
    await client.get(f"/api/auth/confirm_email/{token}")
    
    login_res = await client.post(
        "/api/auth/login",
        data={"username": username, "password": "password123"}
    )
    access_token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.mark.asyncio
async def test_contacts_crud(client):
    headers = await get_auth_header(client, "contactuser", "contactuser@example.com")
    
    # 1. Create contact
    contact_data = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "phone": "+380501234567",
        "date_of_birth": "1995-10-25"
    }
    response = await client.post("/api/contacts/", json=contact_data, headers=headers)
    assert response.status_code == 201
    contact_id = response.json()["id"]
    
    # 2. Get contacts
    response = await client.get("/api/contacts/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # 3. Get contact by ID
    response = await client.get(f"/api/contacts/{contact_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Alice"
    
    # 4. Update contact
    update_data = {
        "first_name": "Alisha",
        "last_name": "Smith",
        "email": "alice.smith@example.com",
        "phone": "+380501234567",
        "date_of_birth": "1995-10-25"
    }
    response = await client.put(f"/api/contacts/{contact_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Alisha"
    
    # 5. Delete contact
    response = await client.delete(f"/api/contacts/{contact_id}", headers=headers)
    assert response.status_code == 200
    
    # 6. Verify 404
    response = await client.get(f"/api/contacts/{contact_id}", headers=headers)
    assert response.status_code == 404
