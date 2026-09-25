import requests

API_BASE = "http://127.0.0.1:8000"

print("Authenticating with default Administrator credentials...")
token = ""
try:
    auth_resp = requests.post(
        f"{API_BASE}/api/auth/login",
        data={"username": "admin@apex.com", "password": "admin123"},
        timeout=5
    )
    if auth_resp.status_code == 200:
        token = auth_resp.json().get("access_token", "")
        print("[OK] Session authenticated successfully. JWT Token acquired.")
    else:
        print(f"[ERROR] Failed to authenticate: Status {auth_resp.status_code} - {auth_resp.text}")
except Exception as e:
    print(f"[ERROR] Auth endpoint connection failed: {e}")

headers = {"Authorization": f"Bearer {token}"} if token else {}

endpoints = [
    {"method": "GET", "url": f"{API_BASE}/", "headers": {}, "desc": "Health Check Root"},
    {"method": "GET", "url": f"{API_BASE}/api/leads/", "headers": headers, "desc": "CRM Leads List"},
    {"method": "GET", "url": f"{API_BASE}/api/leads/1", "headers": headers, "desc": "Lead Details (ID=1)"},
    {"method": "GET", "url": f"{API_BASE}/api/analytics/dashboard", "headers": headers, "desc": "Analytics Dashboard KPI Summary"},
    {"method": "GET", "url": f"{API_BASE}/api/analyzer/reports/1", "headers": {}, "desc": "Web Audit Reports (ID=1)"},
    {"method": "GET", "url": f"{API_BASE}/api/proposals/lead/1", "headers": headers, "desc": "Proposals List (ID=1)"},
    {"method": "GET", "url": f"{API_BASE}/api/portfolio/preview/1?niche=Restaurant", "headers": {}, "desc": "Portfolio Dynamic Site Preview"},
    {"method": "GET", "url": "http://127.0.0.1:5173/", "headers": {}, "desc": "Vite React Frontend Shell"}
]

print("\nVerifying system HTTP endpoints:")
print("=" * 60)

all_ok = True
for ep in endpoints:
    try:
        resp = requests.get(ep["url"], headers=ep["headers"], timeout=5)
        status = resp.status_code
        is_ok = status == 200
        indicator = "[OK]" if is_ok else "[ERROR]"
        print(f"{indicator} {ep['desc']}: GET {ep['url']} -> Status {status}")
        
        if not is_ok:
            all_ok = False
            print(f"   Response error body: {resp.text[:200]}")
    except Exception as e:
        all_ok = False
        print(f"[ERROR] {ep['desc']}: GET {ep['url']} -> Connection Failed: {e}")

print("=" * 60)
if all_ok:
    print("ALL API ENDPOINTS ARE RETURNING VALID 200 OK RESPONSES UNDER AUTHENTICATION!")
else:
    print("WARNING: Some endpoints failed verification.")
