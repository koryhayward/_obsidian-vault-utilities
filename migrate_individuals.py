import os
import shutil
import logging
import config

# --- CONFIGURATION ---
TARGET_DIR = os.path.join(config.VAULT_ROOT, '_individuals')

setup_logger = logging.getLogger('migration')
setup_logger.setLevel(logging.INFO)

def main():
    if not os.path.exists(TARGET_DIR):
        print(f"Directory not found: {TARGET_DIR}")
        return

    print(f"Migrating files in {TARGET_DIR}...")
    
    # 1. Create A-Z Directories
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ#":
        subpath = os.path.join(TARGET_DIR, char)
        os.makedirs(subpath, exist_ok=True)
        
    # 2. Move Files
    moved_count = 0
    for filename in os.listdir(TARGET_DIR):
        filepath = os.path.join(TARGET_DIR, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue
            
        if not filename.endswith('.md'):
            continue
            
        # Determine Folder (First char or #)
        first_char = filename[0].upper()
        if not first_char.isalpha():
            first_char = '#'
            
        dest_dir = os.path.join(TARGET_DIR, first_char)
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            shutil.move(filepath, dest_path)
            moved_count += 1
        except Exception as e:
            print(f"Error moving {filename}: {e}")
            
    print(f"Migration complete. Moved {moved_count} files into A-Z subfolders.")

if __name__ == "__main__":
    main()
