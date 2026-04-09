import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_create_user():
    # Login as admin first
    login_payload = {
        "username": "mohamedleminaidelha@gmail.com",
        "password": "Notaire2024!"
    }
    login_res = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
    if login_res.status_code != 200:
        print(f"Admin login failed: {login_res.text}")
        return
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # User data from screenshot
    user_payload = {
        "email": "sidimohamedkh088@gmail.com",
        "password": "password123",
        "first_name": "Sidi Mohamed",
        "last_name": "Kherchi",
        "birth_date": "2004/10/25",
        "bureau": "402",
        "role": "notaire"
    }
    
    response = requests.post(f"{BASE_URL}/admin/users", json=user_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_create_user()
