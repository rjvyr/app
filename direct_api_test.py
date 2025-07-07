import requests
import json
import sys

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            base_url = line.strip().split('=')[1].strip('"\'')
            break

print(f"Using backend URL: {base_url}")

# Login with admin credentials
login_data = {
    "email": "admin@futureseo.io",
    "password": "admin123"
}

login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code} - {login_response.text}")
    sys.exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login successful")

# Get existing brands
brands_response = requests.get(f"{base_url}/api/brands", headers=headers)
if brands_response.status_code != 200:
    print(f"Failed to get brands: {brands_response.status_code} - {brands_response.text}")
    sys.exit(1)

brands = brands_response.json()["brands"]
print(f"Found {len(brands)} existing brands:")
for brand in brands:
    print(f"  - {brand['name']} (ID: {brand['_id']})")

# Create Upraised brand if it doesn't exist
upraised_brand = None
for brand in brands:
    if brand["name"] == "Upraised":
        upraised_brand = brand
        print(f"Upraised brand already exists with ID: {upraised_brand['_id']}")
        break

if not upraised_brand:
    brand_data = {
        "name": "Upraised",
        "industry": "Career Development Platform",
        "keywords": ["career coaching", "skill development", "job placement"],
        "competitors": ["Springboard", "Pathrise", "Pesto Tech"],
        "website": "https://upraised.co"
    }
    
    create_response = requests.post(f"{base_url}/api/brands", json=brand_data, headers=headers)
    if create_response.status_code != 200:
        print(f"Failed to create Upraised brand: {create_response.status_code} - {create_response.text}")
        sys.exit(1)
    
    upraised_brand_id = create_response.json()["brand_id"]
    print(f"✅ Created Upraised brand with ID: {upraised_brand_id}")
    
    # Get the brand details
    brand_response = requests.get(f"{base_url}/api/brands/{upraised_brand_id}", headers=headers)
    if brand_response.status_code != 200:
        print(f"Failed to get Upraised brand details: {brand_response.status_code} - {brand_response.text}")
        sys.exit(1)
    
    upraised_brand = brand_response.json()["brand"]

# Run a scan for the Upraised brand
print(f"Running scan for Upraised brand (ID: {upraised_brand['_id']})...")
scan_data = {
    "brand_id": upraised_brand["_id"],
    "scan_type": "quick"
}

scan_response = requests.post(f"{base_url}/api/scans", json=scan_data, headers=headers)
if scan_response.status_code != 200:
    print(f"Failed to run scan: {scan_response.status_code} - {scan_response.text}")
    sys.exit(1)

scan_result = scan_response.json()
print(f"✅ Scan completed with {len(scan_result['results'])} results")
print(f"  - Scan ID: {scan_result['scan_id']}")
print(f"  - Visibility score: {scan_result['visibility_score']}%")

# Check source domains
print("\nChecking source domains...")
domains_response = requests.get(f"{base_url}/api/source-domains?brand_id={upraised_brand['_id']}", headers=headers)
if domains_response.status_code != 200:
    print(f"Failed to get source domains: {domains_response.status_code} - {domains_response.text}")
    sys.exit(1)

domains_data = domains_response.json()
print(f"✅ Found {domains_data['total']} source domains:")
for domain in domains_data["domains"]:
    print(f"  - {domain['domain']} (impact: {domain['impact']})")

# Check source articles
print("\nChecking source articles...")
articles_response = requests.get(f"{base_url}/api/source-articles?brand_id={upraised_brand['_id']}", headers=headers)
if articles_response.status_code != 200:
    print(f"Failed to get source articles: {articles_response.status_code} - {articles_response.text}")
    sys.exit(1)

articles_data = articles_response.json()
print(f"✅ Found {articles_data['total']} source articles:")
for article in articles_data["articles"]:
    print(f"  - {article['title']}: {article['url']}")

# Check dashboard data
print("\nChecking dashboard data...")
dashboard_response = requests.get(f"{base_url}/api/dashboard/real?brand_id={upraised_brand['_id']}", headers=headers)
if dashboard_response.status_code != 200:
    print(f"Failed to get dashboard data: {dashboard_response.status_code} - {dashboard_response.text}")
    sys.exit(1)

dashboard_data = dashboard_response.json()
print(f"✅ Dashboard data:")
print(f"  - Total queries: {dashboard_data['total_queries']}")
print(f"  - Total mentions: {dashboard_data['total_mentions']}")
print(f"  - Visibility score: {dashboard_data['overall_visibility']}%")

# Check competitors data
print("\nChecking competitors data...")
competitors_response = requests.get(f"{base_url}/api/competitors/real?brand_id={upraised_brand['_id']}", headers=headers)
if competitors_response.status_code != 200:
    print(f"Failed to get competitors data: {competitors_response.status_code} - {competitors_response.text}")
    sys.exit(1)

competitors_data = competitors_response.json()
print(f"✅ Competitors data:")
print(f"  - Total queries analyzed: {competitors_data['total_queries_analyzed']}")
print(f"  - Competitors found:")
for comp in competitors_data["competitors"]:
    print(f"    - {comp['name']} (mentions: {comp['mentions']})")

print("\n✅ All tests completed successfully!")