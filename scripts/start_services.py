import os
import sys
import subprocess
import time
import socket

def is_port_open(host, port):
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except Exception:
        return False

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")
    database_dir = os.path.join(base_dir, "database")
    
    # Paths to binaries
    postgres_exe = os.path.join(database_dir, "postgres_bin", "pgsql", "bin", "postgres.exe")
    postgres_data = os.path.join(database_dir, "postgres_data")
    redis_exe = os.path.join(database_dir, "redis_bin", "redis-server.exe")
    redis_conf = os.path.join(database_dir, "redis", "redis.conf")
    python_exe = os.path.join(backend_dir, ".venv", "Scripts", "python.exe")
    
    processes = {}
    
    # 1. Start PostgreSQL if not already running
    if is_port_open("localhost", 5432):
        print("[Services] PostgreSQL is already running on port 5432.")
    else:
        print("[Services] Starting PostgreSQL...")
        pg_log = open(os.path.join(database_dir, "postgres_data", "server_orchestrator.log"), "a")
        processes["postgres"] = subprocess.Popen(
            [postgres_exe, "-D", postgres_data],
            stdout=pg_log,
            stderr=pg_log,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        print("[Services] Spawninged PostgreSQL process.")
        
    # 2. Start Redis if not already running
    if is_port_open("localhost", 6379):
        print("[Services] Redis is already running on port 6379.")
    else:
        print("[Services] Starting Redis...")
        redis_log = open(os.path.join(database_dir, "redis", "server_orchestrator.log"), "a")
        processes["redis"] = subprocess.Popen(
            [redis_exe, redis_conf],
            stdout=redis_log,
            stderr=redis_log,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        print("[Services] Spawned Redis process.")
        
    # Wait for database ports to open
    print("[Services] Waiting for databases to initialize ports...")
    for _ in range(15):
        pg_ok = is_port_open("localhost", 5432)
        redis_ok = is_port_open("localhost", 6379)
        if pg_ok and redis_ok:
            print("[Services] Both database ports are open and listening!")
            break
        time.sleep(1)
    else:
        print(f"[Services] Warning: Database ports not fully ready. Postgres: {is_port_open('localhost', 5432)}, Redis: {is_port_open('localhost', 6379)}")
        
    # 3. Start Celery Worker
    print("[Services] Starting Celery worker...")
    celery_log = open(os.path.join(backend_dir, "celery_worker.log"), "a")
    processes["celery"] = subprocess.Popen(
        [python_exe, "-m", "celery", "-A", "app.core.celery_app", "worker", "-l", "info", "--pool", "solo"],
        cwd=backend_dir,
        stdout=celery_log,
        stderr=celery_log,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print("[Services] Spawned Celery worker.")
    
    # 4. Start Backend API Server
    print("[Services] Starting FastAPI Backend...")
    backend_log = open(os.path.join(backend_dir, "backend_server.log"), "a")
    processes["backend"] = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=backend_dir,
        stdout=backend_log,
        stderr=backend_log,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print("[Services] Spawned FastAPI Backend.")
    
    # 5. Start Frontend Server
    print("[Services] Starting Next.js Frontend...")
    frontend_log = open(os.path.join(frontend_dir, "frontend_server.log"), "a")
    processes["frontend"] = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=frontend_dir,
        stdout=frontend_log,
        stderr=frontend_log,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print("[Services] Spawned Next.js Frontend.")
    
    print("[Services] All services spawned. Entering monitoring loop (Ctrl+C to terminate)...")
    
    try:
        while True:
            # Check status of spawned processes
            for name, proc in list(processes.items()):
                poll = proc.poll()
                if poll is not None:
                    print(f"[Services] ERROR: Service '{name}' exited with code {poll}!")
                    # Try to restart?
                    # For now just print error.
            time.sleep(5)
    except KeyboardInterrupt:
        print("[Services] Terminating all services...")
    finally:
        for name, proc in processes.items():
            try:
                proc.terminate()
                print(f"[Services] Terminated {name}")
            except Exception as e:
                print(f"[Services] Failed to terminate {name}: {e}")

if __name__ == "__main__":
    main()
