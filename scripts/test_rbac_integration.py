import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL = "charanjeet.s7730@gmail.com"
ADMIN_PASSWORD = "123456"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if data is not None:
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def print_result(step, status, response_text):
    if status in [200, 201]:
        print(f"[PASS] {step}")
        if response_text:
            return json.loads(response_text)
        return None
    else:
        print(f"[FAIL] {step}")
        print(f"Status: {status}")
        print(f"Response: {response_text}")
        sys.exit(1)

def main():
    print("=== Testing FastAPI Enterprise RBAC APIs ===")

    # 1. Login
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    status, text = make_request(f"{BASE_URL}/auth/login", method="POST", data=login_data)
    token_data = print_result("Login as Super Admin", status, text)
    token = token_data.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Roles
    status, text = make_request(f"{BASE_URL}/roles", method="GET", headers=headers)
    roles = print_result("Get Roles List", status, text)
    print(f"  -> Found {len(roles['roles'])} roles")

    # 3. Get Permissions
    status, text = make_request(f"{BASE_URL}/roles/permissions", method="GET", headers=headers)
    permissions = print_result("Get Permissions List", status, text)
    print(f"  -> Found {len(permissions['permissions'])} permissions")

    # 4. Create Role
    role_payload = {
        "id": "test_role",
        "name": "Test Role",
        "description": "Integration Test Role",
        "permissions": ["users.read"]
    }
    status, text = make_request(f"{BASE_URL}/roles", method="POST", data=role_payload, headers=headers)
    if (status == 400 or status == 409) and "already exists" in text:
        print("[SKIP] Create Role (already exists)")
    else:
        print_result("Create Role", status, text)

    # 5. Assign Permission
    status, text = make_request(f"{BASE_URL}/roles/test_role/permissions", method="POST", data={"permission_id": "roles.read"}, headers=headers)
    if status == 400 and "already assigned" in text:
        print("[SKIP] Assign Permission (already assigned)")
    else:
        print_result("Assign Permission", status, text)

    # 6. Get Users
    status, text = make_request(f"{BASE_URL}/users", method="GET", headers=headers)
    users = print_result("Get Users List", status, text)
    print(f"  -> Found {users['total']} users")

    # 7. Delete Role
    status, text = make_request(f"{BASE_URL}/roles/test_role", method="DELETE", headers=headers)
    print_result("Delete Role", status, text)

    print("\n=============================================")
    print("   ALL RBAC API TESTS PASSED!    ")
    print("=============================================")

if __name__ == "__main__":
    main()
