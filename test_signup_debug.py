import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_signup():
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "full_name": "Test User",
        "email": email,
        "password": "password123",
        "role": "citizen",
        "state": "Tamil Nadu",
        "district": "Thiruvarur",
        "sub_district": "Mannargudi"
    }
    
    print(f"Attempting signup with: {email}...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("Signup successful via API.")
            return True
        else:
            print("Signup failed via API.")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to backend. Is it running?")
        return False

if __name__ == "__main__":
    test_signup()
