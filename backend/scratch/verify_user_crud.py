import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_registration():
    print("Testing Registration...")
    payload = {
        "email": "test_notaire@notaire-ia.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "Notaire"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Status: {response.statusCode}")
    print(f"Response: {response.json()}")
    return response.statusCode == 200

def test_login():
    print("\nTesting Login...")
    payload = {
        "username": "mohamedleminaidelha@gmail.com",
        "password": "Notaire2024!"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=payload)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("Login successful.")
        return token
    else:
        print(f"Login failed: {response.text}")
        return None

def test_admin_list_users(token):
    print("\nTesting Admin List Users...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"Status: {response.status_code}")
    users = response.json()
    print(f"Found {len(users)} users.")
    return users

if __name__ == "__main__":
    # Note: Backend must be running
    try:
        token = test_login()
        if token:
            test_admin_list_users(token)
            # test_registration() # May fail if already exists
    except Exception as e:
        print(f"Error during verification: {e}")
