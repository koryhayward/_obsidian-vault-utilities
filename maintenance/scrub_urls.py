"""
Title: URL Scrubs
Filename: scrub_urls.py
Created: 2026-01-05
Last Updated: 2026-01-05

Description:
    A maintenance utility that removes URLs from daily notes if they have already been 
    captured in the aggregated URL list. This helps de-clutter daily logs.

Key Features:
    - **Safe Removal**: Only removes URLs that exist in `_aggregated-urls.md`.
    - **Scope Control**: Can target just the `latest` daily note or `all` historical notes.
    - **Line Cleaning**: If a line becomes empty or meaningless after URL removal, it is deleted.

Usage:
    python3 scrub_urls.py --scope latest
    python3 scrub_urls.py --scope all

Dependencies:
    - config.py
"""
import os
import re
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Add parent directory to path to locate config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# --- CONFIGURATION ---
AGGREGATED_FILE = config.AGGREGATED_FILE
NOTES_DIR = config.NOTES_DIR
LOG_FILE = os.path.join(config.LOGS_DIR, 'scrub_urls.log')

# Regex to find URLs
URL_PATTERN = re.compile(r'(https?://[^\s<>")]+)')
# Regex to identify daily notes (YYYY-MM-DD.md)
DATE_FILE_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2})\.md$')

def setup_logging():
    logger = logging.getLogger('url_scrubber')
    logger.setLevel(logging.INFO)
    if logger.hasHandlers(): logger.handlers.clear()
    
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler())
    return logger

def get_aggregated_urls(filepath, logger):
    """
    Parses the aggregated URL markdown table to build a set of known URLs.
    Assumes URLs are in the 3rd column (index 2) of the pipe-delimited table.
    """
    known_urls = set()
    if not os.path.exists(filepath):
        logger.warning(f"Aggregated file not found at {filepath}. Nothing to scrub.")
        return known_urls

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # Basic check for table row structure
                if line.strip().startswith('|'):
                    parts = [p.strip() for p in line.split('|')]
                    # | Date | Source | URL | Status | -> URL is at index 3 (0 is empty before first pipe)
                    # Use a flexible check in case of variations, but standard is index 3
                    if len(parts) > 3:
                        url_candidate = parts[3]
                        if url_candidate.startswith('http'):
                            known_urls.add(url_candidate)
    except Exception as e:
        logger.error(f"Error reading aggregated file: {e}")
    
    return known_urls

def get_target_files(directory, scope):
    """
    Returns a list of absolute filepaths to process based on scope.
    """
    daily_notes = []
    if not os.path.exists(directory):
        return daily_notes

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if DATE_FILE_PATTERN.match(filename):
                daily_notes.append(os.path.join(root, filename))

    # Sort by date (filename)
    daily_notes.sort()

    if not daily_notes:
        return []

    if scope == 'latest':
        return [daily_notes[-1]]
    else:
        return daily_notes

def is_line_junk(line_content):
    """
    Determines if a line is 'junk' after URL removal.
    Junk = empty, only whitespace, or common bullets with no content.
    """
    stripped = line_content.strip()
    if not stripped:
        return True
    if stripped in ['-', '*', '[]', '[ ]']:
        return True
    return False

def scrub_file(filepath, known_urls, logger):
    """
    Reads a file, removes instances of known_urls, and rewrites the file if changes occurred.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return

    new_lines = []
    changes_made = False
    
    for line in lines:
        original_line = line
        urls_in_line = URL_PATTERN.findall(line)
        
        modified_line = line
        found_match = False

        for url in urls_in_line:
            if url in known_urls:
                found_match = True
                # Remove URL from line
                # We replace it with nothing, effectively cutting it out
                # NOTE: This might leave weird spacing, but is generally safe
                modified_line = modified_line.replace(url, "")

        if found_match:
            changes_made = True
            # Check if the line is now just junk
            if not is_line_junk(modified_line):
                new_lines.append(modified_line)
            else:
                # Ensure we end with newline if we skip a line but still have content?
                # Actually if we delete the line, we delete the newline too implicitly
                pass
        else:
            new_lines.append(line)

    if changes_made:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            logger.info(f"Scrubbed URLs from {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Failed to write to {filepath}: {e}")
    else:
        # logger.debug(f"No matching URLs found in {os.path.basename(filepath)}")
        pass

def main():
    parser = argparse.ArgumentParser(description="Remove processed URLs from daily notes.")
    parser.add_argument('--scope', choices=['latest', 'all'], default='latest', 
                        help="Scope of cleanup: 'latest' (newest daily note) or 'all' (entire history).")
    
    args = parser.parse_args()
    logger = setup_logging()

    logger.info(f"Starting URL Scrub. Scope: {args.scope}")

    # 1. Load Aggregated URLs
    known_urls = get_aggregated_urls(AGGREGATED_FILE, logger)
    logger.info(f"Loaded {len(known_urls)} processed URLs.")

    if not known_urls:
        logger.info("No aggregated URLs found to scrub.")
        return

    # 2. Get Target Files
    files_to_scrub = get_target_files(NOTES_DIR, args.scope)
    logger.info(f"Identified {len(files_to_scrub)} file(s) to process.")

    # 3. Process
    for filepath in files_to_scrub:
        scrub_file(filepath, known_urls, logger)

    logger.info("URL Scrub completed.")

if __name__ == "__main__":
    main()
