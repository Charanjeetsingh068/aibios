# API Test Report — AI-BOS

This report documents the live test execution outcomes and JSON schemas returned by the diagnostic REST endpoints of the FastAPI server.

---

## 1. Test Summary

* **Test Date:** July 7, 2026
* **Host environment:** Windows 11
* **FastAPI Server Endpoint:** `http://localhost:8000`
* **Outcome:** **PASS**. All new system endpoints serve compliant, standard-conforming JSON payloads. Database status checks and agent registries are dynamically evaluated.

---

## 2. API Endpoint Schemas & Responses

### 1. Uptime and Status Check
* **Endpoint:** `GET /api/v1/system/status`
* **Response Payload:**
```json
{
  "backend": "online",
  "version": "1.0.0",
  "environment": "development",
  "uptime": "28s",
  "python_version": "3.13.14",
  "fastapi": "running"
}
```

### 2. Host Metrics and Specifications
* **Endpoint:** `GET /api/v1/system/info`
* **Response Payload:**
```json
{
  "app_name": "AI-BOS Enterprise",
  "app_version": "1.0.0",
  "os": "Windows",
  "hostname": "Charanjeet",
  "current_time": "2026-07-07T15:19:57.072457",
  "timezone": "India Standard Time",
  "memory": "11.48 GB / 15.34 GB (74%)",
  "cpu_count": 12,
  "platform": "Windows-11-10.0.26200-SP0"
}
```

### 3. Parallel Database Connectivity Check
* **Endpoint:** `GET /api/v1/system/database`
* **Response Payload:**
```json
{
  "postgres": {
    "connected": false
  },
  "mongodb": {
    "connected": true
  },
  "redis": {
    "connected": false
  },
  "qdrant": {
    "connected": false
  }
}
```
*(Note: Connection attempts are wrapped in parallel tasks with 2.0 seconds timeouts, returning instantly without blocking the server loop when services are offline).*

### 4. Agent Installation Registry
* **Endpoint:** `GET /api/v1/system/agents`
* **Response Payload:**
```json
{
  "supervisor_agent": "Running",
  "planner_agent": "Not Installed",
  "executor_agent": "Running",
  "developer_agent": "Not Installed"
}
```
*(Note: Dynamically parses active compiled graph builders to query running nodes).*
