import os

skip_dirs = {
    "windows", "system32", "node_modules", "package-lock.json", 
    "microsoft", "package", "packages", "cache", "temp", "tmp",
    "$recycle.bin", "sadplog", "inetpub", "log files"
}

def search_drive(drive_letter):
    print(f"Scanning {drive_letter}:\\ for pg_ctl.exe or postgres.exe...")
    for root, dirs, files in os.walk(drive_letter + ":\\"):
        # Modify dirs in-place to skip skipped directories
        dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
        
        # Check files
        for filename in files:
            if filename.lower() in ("pg_ctl.exe", "postgres.exe"):
                full_path = os.path.join(root, filename)
                print(f"FOUND: {full_path}")
                return full_path
    return None

for d in ["C", "D", "E", "F", "G", "H"]:
    search_drive(d)
