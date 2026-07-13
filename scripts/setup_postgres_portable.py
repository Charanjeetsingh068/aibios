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
    
    zip_path = os.path.join(db_dir, "postgresql-15.8.zip")
    bin_dir = os.path.join(db_dir, "postgres_bin")
    data_dir = os.path.join(db_dir, "postgres_data")
    pw_file = os.path.join(db_dir, "pg_pw.txt")
    
    # 1. Download PostgreSQL zip
    url = "https://get.enterprisedb.com/postgresql/postgresql-15.8-1-windows-x64-binaries.zip"
    if not os.path.exists(zip_path):
        print(f"Downloading PostgreSQL from {url}...")
        try:
            urllib.request.urlretrieve(url, zip_path)
            print("Download completed.")
        except Exception as e:
            print(f"Failed to download: {e}")
            sys.exit(1)
    else:
        print("PostgreSQL ZIP already downloaded.")
        
    # 2. Extract ZIP
    if not os.path.exists(bin_dir):
        print(f"Extracting PostgreSQL to {bin_dir}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(bin_dir)
            print("Extraction completed.")
        except Exception as e:
            print(f"Failed to extract: {e}")
            sys.exit(1)
    else:
        print("PostgreSQL already extracted.")
        
    pg_bin = os.path.join(bin_dir, "pgsql", "bin")
    initdb_exe = os.path.join(pg_bin, "initdb.exe")
    pg_ctl_exe = os.path.join(pg_bin, "pg_ctl.exe")
    createdb_exe = os.path.join(pg_bin, "createdb.exe")
    psql_exe = os.path.join(pg_bin, "psql.exe")
    
    # Write password file
    with open(pw_file, 'w', encoding='utf-8') as f:
        f.write("aibios_secure_password_2026")
        
    # 3. Initialize Data Directory
    if not os.path.exists(os.path.join(data_dir, "PG_VERSION")):
        print(f"Initializing database cluster at {data_dir}...")
        try:
            cmd = [
                initdb_exe,
                "-D", data_dir,
                "-U", "aibios_admin",
                f"--pwfile={pw_file}",
                "--auth=trust",
                "-E", "UTF8"
            ]
            subprocess.run(cmd, check=True)
            print("Database cluster initialized.")
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            sys.exit(1)
    else:
        print("Database cluster already initialized.")
        
    # 4. Start PostgreSQL Server
    print("Starting PostgreSQL server...")
    try:
        cmd = [
            pg_ctl_exe,
            "-D", data_dir,
            "-l", os.path.join(data_dir, "server.log"),
            "start"
        ]
        subprocess.run(cmd, check=True)
        print("PostgreSQL server started successfully.")
    except Exception as e:
        print(f"Failed to start PostgreSQL server: {e}")
        # Server might be already running, let's wait a bit anyway
        
    time.sleep(3)
    
    # 5. Create database aibios_db
    print("Creating database aibios_db...")
    try:
        cmd = [
            createdb_exe,
            "-U", "aibios_admin",
            "-h", "localhost",
            "-p", "5432",
            "aibios_db"
        ]
        # Ignore error if database already exists
        subprocess.run(cmd, capture_output=True)
        print("Database creation command run.")
    except Exception as e:
        print(f"Failed to create database: {e}")
        
    # 6. Enable uuid-ossp extension
    print("Enabling uuid-ossp extension...")
    try:
        cmd = [
            psql_exe,
            "-U", "aibios_admin",
            "-h", "localhost",
            "-d", "aibios_db",
            "-p", "5432",
            "-c", 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
        ]
        subprocess.run(cmd, check=True)
        print("uuid-ossp extension enabled.")
    except Exception as e:
        print(f"Failed to enable uuid-ossp extension: {e}")
        sys.exit(1)

    print("PostgreSQL setup completed successfully!")

if __name__ == "__main__":
    main()
