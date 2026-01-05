"""
Title: Resurfacing Engine
Filename: resurface.py
Created: 2025-12-30
Last Updated: 2025-12-30

Description:
    Combats "digital hoarding" by algorithmically surfacing forgotten notes. It identifies "Orphans" (notes 
    isolate from the graph) and "Dusty Notes" (active notes identifying as valid but untouched for >90 days).
    Generates a dashboard for weekly review.

Key Features:
    - **Orphan Detection**: graph analysis to find notes with in-degree 0.
    - **Dusty Note Detection**: Time-delta analysis on file modification times.
    - **Smart Exclusion**: Ignores templates, scripts, archiving tags, and trash.
    - **Dashboard Generation**: Outputs a Markdown report to `_dashboards/resurfacing.md`.

Usage:
    python3 resurface.py

Dependencies:
    - config.py
"""
import os
import re
import random
import logging
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# --- CONFIGURATION ---
SEARCH_DIR = config.VAULT_ROOT
OUTPUT_FILE = os.path.join(config.DASHBOARDS_DIR, 'resurfacing.md')
DUSTY_THRESHOLD_DAYS = 90
IGNORE_DIRS = {'.git', '.obsidian', '.trash', '_templates', '_scripts', '_artifacts', '_obsidian-vault-utilities'}
IGNORE_TAGS = {'#archive', '#completed'}

setup_logger = logging.getLogger('resurfacer')
setup_logger.setLevel(logging.INFO)

def get_all_notes(root_dir):
    """Scans for all markdown files."""
    notes = []
    for root, dirs, files in os.walk(root_dir):
        # Filter directories in place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith('.md'):
                notes.append(os.path.join(root, file))
    return notes

def parse_note(filepath):
    """Extracts links and metadata."""
    out_links = set()
    tags = set()
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Extract Wikilinks [[Link]]
            matches = re.findall(r'\[\[(.*?)\]\]', content)
            for m in matches:
                # Handle aliases [[Link|Alias]]
                link_target = m.split('|')[0].strip()
                out_links.add(link_target)
                
            # Extract Tags #tag
            # Use (?:^|\s) to match start of line or whitespace without lookbehind
            tag_matches = re.findall(r'(?:^|\s)(#[a-zA-Z0-9_\-/]+)', content)
            tags.update(tag_matches)
            
    except Exception as e:
        setup_logger.warning(f"Error extracting links from {filepath}: {e}")
        
    return out_links, tags

def main():
    start_time = datetime.now()
    print(f"Starting Resurfacing scan at {start_time}")
    
    notes = get_all_notes(SEARCH_DIR)
    note_map = {os.path.splitext(os.path.basename(n))[0]: n for n in notes}
    
    # Build Graph
    adjacency = {name: set() for name in note_map}
    in_degree = {name: 0 for name in note_map}
    
    dusty_candidates = []
    
    for filepath in notes:
        name = os.path.splitext(os.path.basename(filepath))[0]
        links, tags = parse_note(filepath)
        
        # Check Dusty Status
        if not any(t in IGNORE_TAGS for t in tags):
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            age_days = (datetime.now() - mtime).days
            if age_days > DUSTY_THRESHOLD_DAYS:
                dusty_candidates.append((name, age_days))
        
        # Update Graph
        for link in links:
            # Clean link (remove section anchors # header)
            clean_link = link.split('#')[0]
            if clean_link in note_map:
                adjacency[name].add(clean_link)
                in_degree[clean_link] += 1
                
    # Identify Orphans
    orphans = [n for n in in_degree if in_degree[n] == 0]
    
    # Pick Random selections
    selected_orphans = random.sample(orphans, min(5, len(orphans)))
    selected_dusty = random.sample(dusty_candidates, min(5, len(dusty_candidates)))
    
    # Generate Report
    report = f"""---
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags: [dashboard, resurfacing]
---

# Resurfacing Dashboard

> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Total Notes**: {len(notes)}
> **Orphans Found**: {len(orphans)}
> **Dusty Notes (> {DUSTY_THRESHOLD_DAYS} days)**: {len(dusty_candidates)}

## Random Resurfaced Ideas
*(Notes you haven't touched in a while)*

"""
    for name, age in selected_dusty:
        report += f"- [[{name}]] (Last edited: {age} days ago)\n"

    report += """
## Lonely Orphans
*(Notes with 0 incoming links)*

"""
    for name in selected_orphans:
        report += f"- [[{name}]]\n"
        
    report += """
## Full Orphan List (Top 50)
"""
    for name in orphans[:50]:
        report += f"- [[{name}]]\n"

    # Write Output
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report report generated at: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing report: {e}")

if __name__ == "__main__":
    main()
