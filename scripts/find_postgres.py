import os

def find_file(filename, roots):
    for root in roots:
        print(f"Scanning root: {root}")
        for dirpath, dirnames, filenames in os.walk(root):
            # Check depth (limit to 4 levels)
            depth = dirpath.count(os.sep) - root.count(os.sep)
            if depth > 4:
                # Clear dirnames so we don't go deeper
                dirnames.clear()
                continue
            if filename in filenames:
                full_path = os.path.join(dirpath, filename)
                print(f"FOUND: {full_path}")
                return full_path
    print(f"NOT FOUND: {filename}")
    return None

find_file("postgres.exe", ["C:\\", "D:\\"])
