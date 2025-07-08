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

# Step 3: Create a brand
print("\n3. Creating a brand...")
brand_data = {
    "name": "WeeklyScanLimitTestBrand",
    "industry": "E-commerce Platform",
    "keywords": ["online store", "e-commerce", "shopping cart"],
    "competitors": ["Shopify", "WooCommerce", "BigCommerce"],
    "website": "https://weeklyscanlimittest.com"
}

headers = {"Authorization": f"Bearer {token}"}
brand_response = requests.post(f"{base_url}/api/brands", json=brand_data, headers=headers)
print(f"Brand creation response: {brand_response.status_code}")
brand_id = brand_response.json()["brand_id"]
print(f"Created brand with ID: {brand_id}")

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

# Step 5: Check scan progress
print("\n5. Checking scan progress...")
time.sleep(2)  # Wait a bit for the scan to start
progress_response = requests.get(f"{base_url}/api/scans/{scan_id}/progress", headers=headers)
print(f"Progress response: {progress_response.status_code}")
print(json.dumps(progress_response.json(), indent=2))

# Step 6: Run second scan immediately - should fail with 429 error
print("\n6. Running second scan immediately (should fail with 429)...")
second_scan_response = requests.post(f"{base_url}/api/scans", json=scan_data, headers=headers)
print(f"Second scan response: {second_scan_response.status_code}")
print(json.dumps(second_scan_response.json(), indent=2))

# Step 7: Wait for scan to complete and check results
print("\n7. Waiting for scan to complete and checking results...")
max_wait = 60  # Maximum wait time in seconds
wait_interval = 5  # Check every 5 seconds
elapsed = 0

while elapsed < max_wait:
    progress_response = requests.get(f"{base_url}/api/scans/{scan_id}/progress", headers=headers)
    progress_data = progress_response.json()
    
    if progress_data["status"] == "completed":
        print("Scan completed!")
        print(json.dumps(progress_data, indent=2))
        break
    
    print(f"Scan in progress: {progress_data['progress']}/{progress_data['total_queries']} queries processed")
    time.sleep(wait_interval)
    elapsed += wait_interval

# Step 8: Check scan results for OpenAI integration
print("\n8. Checking scan results for OpenAI integration...")
scans_response = requests.get(f"{base_url}/api/scans/{brand_id}", headers=headers)
print(f"Scans response: {scans_response.status_code}")

if scans_response.status_code == 200:
    scans_data = scans_response.json()
    if scans_data["scans"]:
        recent_scan = scans_data["scans"][0]
        print(f"Found scan with {len(recent_scan['results'])} results")
        
        # Check first result for OpenAI integration
        if recent_scan["results"]:
            result = recent_scan["results"][0]
            print(f"Platform: {result['platform']}")
            print(f"Model: {result['model']}")
            print(f"Response length: {len(result['response'])}")
            print(f"Source domains: {len(result.get('source_domains', []))}")
            print(f"Source articles: {len(result.get('source_articles', []))}")
            
            # Print a sample of the response
            print("\nSample response:")
            print(result['response'][:200] + "...")
    else:
        print("No scans found")
else:
    print(f"Error: {scans_response.json()}")

print("\nTest completed!")