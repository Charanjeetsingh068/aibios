import os
import sys
import urllib.request
import zipfile
import subprocess
import time

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_dir = os.path.join(base_dir, "database")
    os.makedirs(db_dir, exist_ok=True)
    
    zip_path = os.path.join(db_dir, "redis-5.0.14.1.zip")
    bin_dir = os.path.join(db_dir, "redis_bin")
    
    # 1. Download Redis zip
    url = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"
    if not os.path.exists(zip_path):
        print(f"Downloading Redis from {url}...")
        try:
            # Set user agent to avoid 403 from Github
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
            print("Download completed.")
        except Exception as e:
            print(f"Failed to download: {e}")
            sys.exit(1)
    else:
        print("Redis ZIP already downloaded.")
        
    # 2. Extract ZIP
    if not os.path.exists(bin_dir):
        print(f"Extracting Redis to {bin_dir}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(bin_dir)
            print("Extraction completed.")
        except Exception as e:
            print(f"Failed to extract: {e}")
            sys.exit(1)
    else:
        print("Redis already extracted.")
        
    redis_server_exe = os.path.join(bin_dir, "redis-server.exe")
    redis_conf = os.path.join(db_dir, "redis", "redis.conf")
    
    # 3. Start Redis Server
    print("Starting Redis server...")
    try:
        # On Windows, we run it in a separate process that doesn't block
        # We can pass the conf file
        log_file = os.path.join(db_dir, "redis", "redis.log")
        
        # Check if already running on port 6379
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("127.0.0.1", 6379))
            print("Redis server is already running on port 6379.")
            s.close()
            return
        except Exception:
            pass
            
        # Start in background
        cmd = f'"{redis_server_exe}" "{redis_conf}"'
        print(f"Executing: {cmd}")
        # Run with creation flags to avoid console window popup
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # Open a file for stdout/stderr logging
        log_fp = open(log_file, "a")
        subprocess.Popen(
            [redis_server_exe, redis_conf],
            stdout=log_fp,
            stderr=log_fp,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
        print("Redis server started in background.")
    except Exception as e:
        print(f"Failed to start Redis server: {e}")
        sys.exit(1)

    print("Redis setup completed successfully!")

if __name__ == "__main__":
    main()
