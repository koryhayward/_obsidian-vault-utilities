"""
Title: Vault Structure Mapper
Filename: map_vault.py
Created: 2025-12-30
Last Updated: 2025-12-30

Description:
    Visualizes the physical storage structure of the Obsidian vault. It generates an ASCII tree diagram
    annotated with file counts and directory sizes (in MB). This helps identify bloat and structural imbalances
    that aren't visible in the Obsidian graph view.

Key Features:
    - **ASCII Tree Generation**: Recursive visualization of folders.
    - **Size & Count Analytics**: Quantifies the "weight" of each valid directory.
    - **Noise Reduction**: Explicitly excludes .git, .obsidian, and other system folders.
    - **Artifact Output**: Saves result to `_artifacts/vault_structure.md` to avoid cluttering dashboards.

Usage:
    python3 map_vault.py

Dependencies:
    - config.py
"""
import os
import json
import logging
from datetime import datetime
import config

# --- CONFIGURATION ---
VAULT_ROOT = config.VAULT_ROOT
OUTPUT_FILE = os.path.join(config.ARTIFACTS_DIR, 'vault_structure.md')
EXCLUDE_DIRS = {'.git', '.obsidian', '.trash', '.venv', '__pycache__', '.gemini', '_scripts', '_templates'}

def setup_logging():
    logger = logging.getLogger('vault_mapper')
    logger.setLevel(logging.INFO)
    if logger.hasHandlers(): logger.handlers.clear()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_dir_stats(path):
    """Recursively counts files and calculates size."""
    file_count = 0
    total_size = 0
    
    try:
        for entry in os.scandir(path):
            if entry.name in EXCLUDE_DIRS:
                continue
            
            if entry.is_dir(follow_symlinks=False):
                c, s = get_dir_stats(entry.path)
                file_count += c
                total_size += s
            elif entry.is_file(follow_symlinks=False):
                if entry.name.endswith('.md'):
                    file_count += 1
                    total_size += entry.stat().st_size
    except PermissionError:
        pass
        
    return file_count, total_size

def generate_tree(path, prefix=""):
    """Generates a visual tree structure string."""
    tree_str = ""
    try:
        entries = sorted([e for e in os.scandir(path) if e.name not in EXCLUDE_DIRS], key=lambda e: (not e.is_dir(), e.name.lower()))
        entries_count = len(entries)
        
        for index, entry in enumerate(entries):
            connector = "└── " if index == entries_count - 1 else "├── "
            
            if entry.is_dir():
                count, size = get_dir_stats(entry.path)
                size_mb = size / (1024 * 1024)
                tree_str += f"{prefix}{connector}**{entry.name}/** `({count} notes, {size_mb:.2f} MB)`\n"
                
                extension = "    " if index == entries_count - 1 else "│   "
                tree_str += generate_tree(entry.path, prefix + extension)
            else:
                # Optional: Uncomment to list individual files, but might be too verbose for large vaults
                # tree_str += f"{prefix}{connector}{entry.name}\n"
                pass
                
    except PermissionError:
        tree_str += f"{prefix}└── [ACCESS DENIED]\n"
        
    return tree_str

def main():
    logger = setup_logging()
    logger.info(f"Mapping vault: {VAULT_ROOT}")
    
    start_time = datetime.now()
    
    tree_view = generate_tree(VAULT_ROOT)
    
    # Generate Dashboard Content
    content = f"""---
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags: [dashboard, meta]
---

# Vault Structure Map

> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Root**: `{VAULT_ROOT}`

## Directory Tree
```ascii
{tree_view}
```

## Summary
*   **Excluded Directories**: {', '.join(EXCLUDE_DIRS)}
*   *Note: Only listing directories and counts to keep this view clean.*
"""
    
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Structure map saved to: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to save map: {e}")

if __name__ == "__main__":
    main()