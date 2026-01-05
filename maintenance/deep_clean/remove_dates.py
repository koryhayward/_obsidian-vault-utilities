"""
Title: Remove Date Fields
Filename: remove_dates.py
Created: 2026-01-05
Last Updated: 2026-01-05

Description:
    A one-time deep clean utility to remove 'created' and 'modified' fields 
    from the frontmatter of Individual and Organization notes.

Usage:
    python3 maintenance/deep_clean/remove_dates.py
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Add vault root to path to locate config (3 levels up from here)
# File is in: _obsidian-vault-utilities/maintenance/deep_clean/
# Config is in: _obsidian-vault-utilities/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

# --- CONFIGURATION ---
INDIVIDUALS_DIR = os.path.join(config.VAULT_ROOT, "_individuals")
ORGANIZATIONS_DIR = os.path.join(config.VAULT_ROOT, "_organizations")
LOG_FILE = os.path.join(config.LOGS_DIR, 'remove_dates.log')

def setup_logging():
    logger = logging.getLogger('remove_dates')
    logger.setLevel(logging.INFO)
    if logger.hasHandlers(): logger.handlers.clear()
    
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler())
    return logger

def process_file(filepath, logger):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return

    new_lines = []
    in_frontmatter = False
    frontmatter_count = 0
    changes_made = False

    for line in lines:
        stripped = line.strip()
        
        # Detect frontmatter boundaries
        if stripped == '---':
            frontmatter_count += 1
            if frontmatter_count == 1:
                in_frontmatter = True
            elif frontmatter_count == 2:
                in_frontmatter = False
            
            new_lines.append(line)
            continue

        if in_frontmatter:
            # Check for keys to remove
            if stripped.startswith('created:') or stripped.startswith('modified:'):
                changes_made = True
                continue # Skip adding this line
            
        new_lines.append(line)

    if changes_made:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            logger.info(f"Cleaned {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")

def main():
    logger = setup_logging()
    logger.info("Starting Date Removal Deep Clean...")
    
    dirs_to_process = [INDIVIDUALS_DIR, ORGANIZATIONS_DIR]
    
    total_scanned = 0
    
    for directory in dirs_to_process:
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            continue
            
        logger.info(f"Scanning {directory}...")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.md'):
                    process_file(os.path.join(root, file), logger)
                    total_scanned += 1
                    
    logger.info(f"Process complete. Scanned {total_scanned} files.")

if __name__ == "__main__":
    main()
