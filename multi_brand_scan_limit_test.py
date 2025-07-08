import requests
import json
import uuid
import time

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

# Step 3: Create Brand A
print("\n3. Creating Brand A...")
brand_a_data = {
    "name": "Brand A",
    "industry": "Project Management Software",
    "keywords": ["productivity", "team collaboration", "project tracking"],
    "competitors": ["Asana", "Monday.com", "Trello"],
    "website": "https://branda.com"
}

headers = {"Authorization": f"Bearer {token}"}
brand_a_response = requests.post(f"{base_url}/api/brands", json=brand_a_data, headers=headers)
print(f"Brand A creation response: {brand_a_response.status_code}")
if brand_a_response.status_code == 200:
    brand_a_id = brand_a_response.json()["brand_id"]
    print(f"Created Brand A with ID: {brand_a_id}")
else:
    print(f"Error creating Brand A: {brand_a_response.text}")
    exit(1)

# Step 4: Run scan for Brand A - should succeed
print("\n4. Running scan for Brand A (should succeed)...")
scan_a_data = {
    "brand_id": brand_a_id,
    "scan_type": "quick"
}

scan_a_response = requests.post(f"{base_url}/api/scans", json=scan_a_data, headers=headers)
print(f"Brand A scan response: {scan_a_response.status_code}")
if scan_a_response.status_code == 200:
    scan_a_id = scan_a_response.json()["scan_id"]
    print(f"Brand A scan started with ID: {scan_a_id}")
else:
    print(f"Error: {scan_a_response.json()}")
    exit(1)

# Step 5: Try to run a second scan for Brand A - should fail with 429 error
print("\n5. Running second scan for Brand A (should fail with 429)...")
scan_a2_response = requests.post(f"{base_url}/api/scans", json=scan_a_data, headers=headers)
print(f"Brand A second scan response: {scan_a2_response.status_code}")
if scan_a2_response.status_code == 429:
    error_a = scan_a2_response.json()["detail"]
    print(f"Brand A error: {error_a}")
    
    # Check if Brand A's name is in its error message
    if "Brand A" in error_a:
        print("✅ Brand A's error message correctly includes its name")
    else:
        print("❌ Brand A's error message does not include its name")
    
    # Check if error message mentions Monday 11 AM PST
    if "Monday" in error_a and "11:00 AM PST" in error_a:
        print("✅ Brand A's error message correctly includes next available scan time")
    else:
        print("❌ Brand A's error message does not include proper next available scan time")
else:
    print("❌ Second scan for Brand A did not return the expected 429 error")
    print(scan_a2_response.json())

# Step 6: Create Brand B
print("\n6. Creating Brand B...")
brand_b_data = {
    "name": "Brand B",
    "industry": "E-commerce Platform",
    "keywords": ["online store", "e-commerce", "shopping cart"],
    "competitors": ["Shopify", "WooCommerce", "BigCommerce"],
    "website": "https://brandb.com"
}

brand_b_response = requests.post(f"{base_url}/api/brands", json=brand_b_data, headers=headers)
print(f"Brand B creation response: {brand_b_response.status_code}")
if brand_b_response.status_code == 200:
    brand_b_id = brand_b_response.json()["brand_id"]
    print(f"Created Brand B with ID: {brand_b_id}")
else:
    print(f"Error creating Brand B: {brand_b_response.text}")
    exit(1)

# Step 7: Run scan for Brand B - should succeed (not affected by Brand A's scan)
print("\n7. Running scan for Brand B (should succeed)...")
scan_b_data = {
    "brand_id": brand_b_id,
    "scan_type": "quick"
}

scan_b_response = requests.post(f"{base_url}/api/scans", json=scan_b_data, headers=headers)
print(f"Brand B scan response: {scan_b_response.status_code}")
if scan_b_response.status_code == 200:
    scan_b_id = scan_b_response.json()["scan_id"]
    print(f"Brand B scan started with ID: {scan_b_id}")
else:
    print(f"Error: {scan_b_response.json()}")
    exit(1)

# Step 8: Try to run a second scan for Brand B - should fail with 429 error
print("\n8. Running second scan for Brand B (should fail with 429)...")
scan_b2_response = requests.post(f"{base_url}/api/scans", json=scan_b_data, headers=headers)
print(f"Brand B second scan response: {scan_b2_response.status_code}")
if scan_b2_response.status_code == 429:
    error_b = scan_b2_response.json()["detail"]
    print(f"Brand B error: {error_b}")
    
    # Check if Brand B's name is in its error message
    if "Brand B" in error_b:
        print("✅ Brand B's error message correctly includes its name")
    else:
        print("❌ Brand B's error message does not include its name")
    
    # Check if error message mentions Monday 11 AM PST
    if "Monday" in error_b and "11:00 AM PST" in error_b:
        print("✅ Brand B's error message correctly includes next available scan time")
    else:
        print("❌ Brand B's error message does not include proper next available scan time")
else:
    print("❌ Second scan for Brand B did not return the expected 429 error")
    print(scan_b2_response.json())

print("\n=== Weekly Scan Limit Test Results ===")
print("✅ Brand A first scan: SUCCESS" if scan_a_response.status_code == 200 else "❌ Brand A first scan: FAILED")
print("✅ Brand B first scan: SUCCESS" if scan_b_response.status_code == 200 else "❌ Brand B first scan: FAILED")
print("✅ Brand A second scan: FAILED WITH 429" if scan_a2_response.status_code == 429 else "❌ Brand A second scan: DID NOT FAIL AS EXPECTED")
print("✅ Brand B second scan: FAILED WITH 429" if scan_b2_response.status_code == 429 else "❌ Brand B second scan: DID NOT FAIL AS EXPECTED")

if scan_a2_response.status_code == 429 and scan_b2_response.status_code == 429:
    print("✅ Weekly scan limit is correctly enforced per brand")
    if "Brand A" in error_a and "Brand B" in error_b:
        print("✅ Error messages correctly include brand-specific information")
    else:
        print("❌ Error messages do not include brand-specific information")
else:
    print("❌ Weekly scan limit test failed")

print("\nTest completed!")