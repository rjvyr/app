import requests
import json
import time

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            base_url = line.strip().split('=')[1].strip('"\'')
            break

print(f"Using backend URL: {base_url}")

# Test the health endpoint
print("\nTesting health endpoint...")
health_response = requests.get(f"{base_url}/api/health")
print(f"Health response: {health_response.status_code}")
if health_response.status_code == 200:
    print(health_response.json())
else:
    print("Health endpoint not available")

# Test the plans endpoint
print("\nTesting plans endpoint...")
plans_response = requests.get(f"{base_url}/api/plans")
print(f"Plans response: {plans_response.status_code}")
if plans_response.status_code == 200:
    print(json.dumps(plans_response.json(), indent=2))
else:
    print("Plans endpoint not available")

print("\nTest completed!")