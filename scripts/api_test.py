import httpx
import asyncio

async def test_api():
    passed = 0
    failed = 0
    
    # Very rudimentary hit test
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            resp = await client.get("/api/v1/health")
            if resp.status_code == 200:
                passed += 1
            else:
                failed += 1
                
            resp = await client.get("/api/v1/health/meta")
            if resp.status_code == 200:
                passed += 1
            else:
                failed += 1
                
            resp = await client.get("/api/v1/health/facebook")
            if resp.status_code == 200:
                passed += 1
            else:
                failed += 1
                
            resp = await client.get("/api/v1/integrations/meta/oauth/url")
            # Usually requires auth, so expecting 401
            if resp.status_code == 401:
                passed += 1
            else:
                failed += 1
                
            resp = await client.get("/api/v1/integrations/meta/webhook")
            # Expecting 403 or 400 because no verify_token
            if resp.status_code in [403, 400]:
                passed += 1
            else:
                failed += 1
    except Exception as e:
        failed += 5
        print(f"API Error: {e}")
        
    print(f"API TESTS: Passed={passed}, Failed={failed}")

if __name__ == "__main__":
    asyncio.run(test_api())
