import sys
import os
import urllib.request
import json

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

def test_endpoints():
    print("=== Testing FastAPI System API Endpoints ===")
    base_url = "http://localhost:8000/api/v1/system"
    endpoints = {
        "status": ["backend", "version", "environment", "uptime", "python_version", "fastapi"],
        "info": ["app_name", "app_version", "os", "hostname", "current_time", "timezone", "memory", "cpu_count", "platform"],
        "database": ["postgres", "mongodb", "redis", "qdrant"],
        "agents": ["supervisor_agent", "planner_agent", "executor_agent", "developer_agent"]
    }
    
    api_values = {}
    
    for ep, keys in endpoints.items():
        url = f"{base_url}/{ep}"
        try:
            req = urllib.request.urlopen(url, timeout=10.0)
            code = req.getcode()
            if code != 200:
                print(f"  [FAIL] {ep} returned status code {code}")
                return False, None
            
            data = json.loads(req.read().decode())
            print(f"  [PASS] {ep} status 200, valid JSON payload.")
            
            # Validate keys
            for k in keys:
                if k not in data:
                    print(f"  [FAIL] Expected key '{k}' missing from {ep} response: {data.keys()}")
                    return False, None
            
            api_values[ep] = data
            
        except Exception as e:
            print(f"  [FAIL] Failed to execute {ep}: {e}")
            return False, None
            
    print("=== All Backend endpoints validated successfully! ===")
    return True, api_values

def check_frontend_alignment(api_values):
    print("\n=== Validating Frontend Dashboard Bindings ===")
    frontend_page_path = os.path.join(parent_dir, "frontend", "src", "app", "page.tsx")
    
    if not os.path.exists(frontend_page_path):
        print(f"  [FAIL] Frontend page.tsx not found at {frontend_page_path}")
        return False
        
    with open(frontend_page_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check that keys from status are referenced correctly in page.tsx
    status_keys = ["backend", "uptime", "environment", "version", "python_version", "fastapi"]
    for k in status_keys:
        ref = f"status?.{k}"
        if ref not in content:
            print(f"  [FAIL] Frontend key reference check: '{ref}' not found in page.tsx")
            return False
        print(f"  [PASS] Found reference to {ref} in page.tsx")
        
    # Check that keys from info are referenced
    info_keys = ["cpu_count", "memory", "platform"]
    for k in info_keys:
        ref = f"info?.{k}"
        if ref not in content:
            print(f"  [FAIL] Frontend key reference check: '{ref}' not found in page.tsx")
            return False
        print(f"  [PASS] Found reference to {ref} in page.tsx")
        
    # Check database keys
    db_keys = ["postgres", "mongodb", "redis", "qdrant"]
    for k in db_keys:
        ref = f"dbStatus?.{k}?.connected"
        if ref not in content:
            print(f"  [FAIL] Frontend key reference check: '{ref}' not found in page.tsx")
            return False
        print(f"  [PASS] Found reference to {ref} in page.tsx")
        
    # Check agent keys
    agent_keys = ["supervisor_agent", "executor_agent"]
    for k in agent_keys:
        ref = f"agents?.{k}"
        if ref not in content:
            print(f"  [FAIL] Frontend key reference check: '{ref}' not found in page.tsx")
            return False
        print(f"  [PASS] Found reference to {ref} in page.tsx")
        
    print("=== Frontend bindings matched backend schemas perfectly! ===")
    return True

def main():
    endpoints_ok, api_values = test_endpoints()
    if not endpoints_ok:
        sys.exit(1)
        
    frontend_ok = check_frontend_alignment(api_values)
    if not frontend_ok:
        sys.exit(1)
        
    print("\n==========================================================")
    print("   INTEGRATION PASSED: Backend & Frontend variables match. ")
    print("==========================================================\n")
    sys.exit(0)

if __name__ == "__main__":
    main()
