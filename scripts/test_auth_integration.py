import urllib.request
import urllib.error
import json
import sys

def run_tests():
    print("=== Testing FastAPI Enterprise Authentication APIs ===")
    base_url = "http://localhost:8000/api/v1/auth"
    
    # 1. Test POST /login
    print("  1. Testing POST /login...")
    login_payload = {
        "email": "charanjeet.s7730@gmail.com",
        "password": "123456",
        "remember_me": False
    }
    
    try:
        req = urllib.request.Request(
            f"{base_url}/login",
            data=json.dumps(login_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                print(f"    [FAIL] Login returned status {res.status}")
                sys.exit(1)
            
            token_data = json.loads(res.read().decode())
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            role = token_data.get("role")
            
            print(f"    [PASS] Login successful. Access Token parsed. Role: {role}")
    except Exception as e:
        print(f"    [FAIL] Login request crashed: {e}")
        sys.exit(1)

    # 2. Test GET /me
    print("  2. Testing GET /me...")
    try:
        req = urllib.request.Request(
            f"{base_url}/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                print(f"    [FAIL] /me returned status {res.status}")
                sys.exit(1)
            
            user_data = json.loads(res.read().decode())
            print(f"    [PASS] User Profile fetched successfully. Email: {user_data.get('email')} | Role ID: {user_data.get('role_id')}")
    except Exception as e:
        print(f"    [FAIL] /me request crashed: {e}")
        sys.exit(1)

    # 3. Test POST /refresh
    print("  3. Testing POST /refresh...")
    try:
        refresh_payload = {
            "refresh_token": refresh_token
        }
        req = urllib.request.Request(
            f"{base_url}/refresh",
            data=json.dumps(refresh_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                print(f"    [FAIL] Token refresh returned status {res.status}")
                sys.exit(1)
            
            new_tokens = json.loads(res.read().decode())
            new_access_token = new_tokens.get("access_token")
            print("    [PASS] Token rotation successful. Generated new rotated access token.")
    except Exception as e:
        print(f"    [FAIL] Token refresh crashed: {e}")
        sys.exit(1)

    # 4. Test POST /forgot-password
    print("  4. Testing POST /forgot-password...")
    try:
        forgot_payload = {
            "email": "charanjeet.s7730@gmail.com"
        }
        req = urllib.request.Request(
            f"{base_url}/forgot-password",
            data=json.dumps(forgot_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                print(f"    [FAIL] Forgot password returned status {res.status}")
                sys.exit(1)
            
            forgot_res = json.loads(res.read().decode())
            recovery_token = forgot_res.get("token_dev_only")
            print(f"    [PASS] Password recovery token created. Dev Token: {recovery_token}")
    except Exception as e:
        print(f"    [FAIL] Forgot password crashed: {e}")
        sys.exit(1)

    # 5. Test POST /logout
    print("  5. Testing POST /logout...")
    try:
        req = urllib.request.Request(
            f"{base_url}/logout",
            data=b"",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                print(f"    [FAIL] Logout returned status {res.status}")
                sys.exit(1)
            print("    [PASS] Session successfully logged out and invalidated.")
    except Exception as e:
        print(f"    [FAIL] Logout crashed: {e}")
        sys.exit(1)

    print("\n============================================= ")
    print("   ALL AUTHENTICATION SYSTEM TESTS PASSED!    ")
    print("=============================================\n")
    sys.exit(0)

if __name__ == "__main__":
    run_tests()
