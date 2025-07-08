import requests
import json
import uuid

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            base_url = line.strip().split('=')[1].strip('"\'')
            break

print(f"Using backend URL: {base_url}")

# Generate unique email for testing
user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
user_password = "Test@123456"

# Step 1: Register a new user
print("\n1. Registering a new user...")
user_data = {
    "email": user_email,
    "password": user_password,
    "full_name": "Test User",
    "company": "Test Company",
    "website": "https://example.com"
}

reg_response = requests.post(f"{base_url}/api/auth/register", json=user_data)
print(f"Registration response: {reg_response.status_code}")
print(reg_response.json())

# Step 2: Login with the new user
print("\n2. Logging in with the new user...")
login_data = {
    "email": user_email,
    "password": user_password
}

login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
print(f"Login response: {login_response.status_code}")
token = login_response.json()["access_token"]
print(f"Got token: {token[:10]}...")

# Step 3: Create a brand
print("\n3. Creating a brand...")
brand_data = {
    "name": "Weekly Limit Test Brand",
    "industry": "Project Management Software",
    "keywords": ["productivity", "team collaboration", "project tracking"],
    "competitors": ["Asana", "Monday.com", "Trello"],
    "website": "https://weeklylimittest.com"
}

headers = {"Authorization": f"Bearer {token}"}
brand_response = requests.post(f"{base_url}/api/brands", json=brand_data, headers=headers)
print(f"Brand creation response: {brand_response.status_code}")
if brand_response.status_code == 200:
    brand_id = brand_response.json()["brand_id"]
    print(f"Created brand with ID: {brand_id}")
else:
    print(f"Error creating brand: {brand_response.text}")
    exit(1)

# Step 4: Run first scan - should succeed
print("\n4. Running first scan (should succeed)...")
scan_data = {
    "brand_id": brand_id,
    "scan_type": "quick"
}

first_scan_response = requests.post(f"{base_url}/api/scans", json=scan_data, headers=headers)
print(f"First scan response: {first_scan_response.status_code}")
if first_scan_response.status_code == 200:
    scan_id = first_scan_response.json()["scan_id"]
    print(f"Scan started with ID: {scan_id}")
else:
    print(f"Error: {first_scan_response.json()}")
    exit(1)

# Step 5: Run second scan immediately - should fail with 429 error
print("\n5. Running second scan immediately (should fail with 429)...")
second_scan_response = requests.post(f"{base_url}/api/scans", json=scan_data, headers=headers)
print(f"Second scan response: {second_scan_response.status_code}")
if second_scan_response.status_code == 429:
    error_message = second_scan_response.json()["detail"]
    print(f"Error message: {error_message}")
    
    # Check if brand name is in the error message
    if brand_data["name"] in error_message:
        print("✅ Error message correctly includes brand name")
    else:
        print("❌ Error message does not include brand name")
    
    # Check if error message mentions Monday 11 AM PST
    if "Monday" in error_message and "11:00 AM PST" in error_message:
        print("✅ Error message correctly includes next available scan time")
    else:
        print("❌ Error message does not include proper next available scan time")
else:
    print("❌ Second scan did not return the expected 429 error")
    print(second_scan_response.json())

print("\n=== Weekly Scan Limit Test Results ===")
print("✅ First scan: SUCCESS" if first_scan_response.status_code == 200 else "❌ First scan: FAILED")
print("✅ Second scan: FAILED WITH 429" if second_scan_response.status_code == 429 else "❌ Second scan: DID NOT FAIL AS EXPECTED")

if second_scan_response.status_code == 429:
    print("✅ Weekly scan limit is correctly enforced")
    if brand_data["name"] in error_message:
        print("✅ Error message correctly includes brand-specific information")
    else:
        print("❌ Error message does not include brand-specific information")
else:
    print("❌ Weekly scan limit test failed")

print("\nTest completed!")