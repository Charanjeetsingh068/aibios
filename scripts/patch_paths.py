import os
import glob

def patch_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        target = "c:/react/aibios"
        replacement = "c:/react/aibios"
        
        if target in content:
            new_content = content.replace(target, replacement)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Patched: {filepath}")
    except Exception as e:
        print(f"Error patching {filepath}: {e}")

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Scanning files in: {root_dir}")
    
    # Scan python files
    for filepath in glob.glob(os.path.join(root_dir, "**/*.py"), recursive=True):
        if ".venv" not in filepath and "node_modules" not in filepath:
            patch_file(filepath)
            
    # Scan ts/tsx/js files
    for ext in ["**/*.ts", "**/*.tsx", "**/*.js"]:
        for filepath in glob.glob(os.path.join(root_dir, ext), recursive=True):
            if ".next" not in filepath and "node_modules" not in filepath:
                patch_file(filepath)

if __name__ == "__main__":
    main()
