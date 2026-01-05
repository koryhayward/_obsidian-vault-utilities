"""
Remove the specific 'Met via' line that causes ghost links.
"""
import os
import pathlib
import sys

VAULT_ROOT = pathlib.Path(os.environ.get('VAULT_ROOT', '/Users/kory/_vault'))
INDIVIDUALS_DIR = VAULT_ROOT / '_individuals'

# The line to look for (ignoring trailing whitespace/newline issues during check)
TARGET_LINE_PART = "- **Met via:** (e.g., Conference, Former Colleague at [[Previous Job]], Cold Outreach)"

def process_file(path: pathlib.Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        modified = False
        for line in lines:
            if TARGET_LINE_PART in line:
                modified = True
                continue # Skip this line
            new_lines.append(line)
        
        if modified:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
            
    except Exception as e:
        print(f"Error processing {path}: {e}")
    return False

def main():
    modified_count = 0
    print(f"Scanning individuals at: {INDIVIDUALS_DIR}")
    
    if not INDIVIDUALS_DIR.exists():
        print(f"Directory not found: {INDIVIDUALS_DIR}")
        return

    for root, dirs, files in os.walk(INDIVIDUALS_DIR):
        for file in files:
            if file.endswith('.md'):
                path = pathlib.Path(root) / file
                if process_file(path):
                    modified_count += 1
    
    print(f"Finished. Modified {modified_count} files.")

if __name__ == "__main__":
    main()
