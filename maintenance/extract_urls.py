"""
Title: URL Extractor
Filename: extract_urls.py
Created: 2025-12-17
Last Updated: 2026-01-05

Description:
    A stream-processing utility that harvests URLs from daily notes. It uses a memory-efficient 
    line-by-line reading approach to handle large markdown files without performance hits.
    The primary purpose is to feed the 'Fetch' mode of the Summarizer Agent.

Key Features:
    - **Pattern Matching**: Regex-based extraction of http/https links.
    - **Memory Efficient**: Uses generator patterns to process files without loading them entirely into RAM.
    - **Aggregation**: Appends unique URLs to a central `_aggregated-urls.md` list.

Usage:
    python3 extract_urls.py

Dependencies:
    - config.py
"""
import os
import re
import logging
from logging.handlers import RotatingFileHandler
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# --- CONFIGURATION FROM UTILS ---
import sys
import argparse
from datetime import date

# --- CONFIGURATION FROM UTILS ---
aggregated_file = config.AGGREGATED_FILE
log_file = os.path.join(config.LOGS_DIR, 'extract_urls.log')
search_dir = config.NOTES_DIR 

def setup_logging():
    logger = logging.getLogger('url_extractor')
    logger.setLevel(logging.INFO)
    if logger.hasHandlers(): logger.handlers.clear()
    
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler())
    return logger

url_pattern = re.compile(r'(https?://[^\s<>")]+)')
date_file_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})\.md$')
# Regex updated to optionally capture 4th (Status) and 5th (UUID) columns
table_row_pattern = re.compile(r'^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\[\[.*?\]\])\s*\|\s*(.*?)\s*\|(?:\s*(.*?)\s*\|)?(?:\s*(.*?)\s*\|)?$')
uuid_pattern = re.compile(r'^uuid:\s*["\']?([a-f0-9\-]+)["\']?')

def parse_existing_table(filepath, logger):
    entries = []
    if not os.path.exists(filepath):
        logger.info(f"Master file {filepath} not found. Starting fresh.")
        return entries
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                match = table_row_pattern.match(line.strip())
                if match:
                    # Tuple: (Date, Source, URL, Status, UUID)
                    status = match.group(4) if match.group(4) else ""
                    uuid_val = match.group(5) if match.group(5) else ""
                    entries.append((match.group(1), match.group(2), match.group(3), status, uuid_val))
    except Exception as e:
        logger.error(f"Error reading master file: {e}")
    return entries

def extract_metadata_and_urls(filepath, logger):
    urls = set()
    found_uuid = ""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = 0
            for line in f:
                line_count += 1
                # Check for UUID in first 20 lines
                if line_count <= 20 and not found_uuid:
                    uuid_match = uuid_pattern.match(line.strip())
                    if uuid_match:
                        found_uuid = uuid_match.group(1)
                
                found = url_pattern.findall(line)
                if found:
                    urls.update(found)
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
    return list(urls), found_uuid

def process_file(filepath, logger, url_map, new_count_ref):
    """
    Helper to process a single file and update the url_map.
    Returns the updated new_count_ref value.
    """
    filename = os.path.basename(filepath)
    
    # Determine Date and Source
    date_match = date_file_pattern.match(filename)
    if date_match:
        # It's a daily note
        file_date = date_match.group(1)
        source = f"[[{file_date}]]"
    else:
        # Not a daily note, use today's date
        file_date = date.today().strftime('%Y-%m-%d')
        # Source is filename without extension
        source_name = os.path.splitext(filename)[0]
        source = f"[[{source_name}]]"

    urls, file_uuid = extract_metadata_and_urls(filepath, logger)
    
    for url in urls:
        if url not in url_map:
            # New entry: Date, Source, URL, Empty Status, UUID
            entry = (file_date, source, url, "", file_uuid)
            url_map[url] = entry
            new_count_ref += 1
        else:
            # Update existing entry with UUID if missing
            existing = url_map[url]
            if len(existing) < 5 or not existing[4]:
                url_map[url] = (existing[0], existing[1], existing[2], existing[3], file_uuid)
            
    return new_count_ref

def main():
    parser = argparse.ArgumentParser(description="Extract URLs from markdown notes.")
    parser.add_argument('-f', '--file', help="Path to a specific markdown file to scan. If omitted, scans all daily notes.")
    args = parser.parse_args()

    logger = setup_logging()
    
    existing_entries = parse_existing_table(aggregated_file, logger)
    # Map URL -> Existing Entry
    url_map = {entry[2]: entry for entry in existing_entries}
    
    new_count = 0

    if args.file:
        # SCAN SINGLE FILE
        target_file = os.path.abspath(args.file)
        if os.path.exists(target_file):
            logger.info(f"Scanning specific file: {target_file}")
            new_count = process_file(target_file, logger, url_map, new_count)
        else:
            logger.error(f"File not found: {target_file}")
            return # Exit if user provided file doesn't exist
    else:
        # SCAN DAILY NOTES DIRECTORY
        logger.info(f"Scanning directory: {search_dir}")
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for filename in files:
                    if date_file_pattern.match(filename):
                        filepath = os.path.join(root, filename)
                        new_count = process_file(filepath, logger, url_map, new_count)
        else:
            logger.error(f"Search directory not found: {search_dir}")

    # Convert back to list and sort by Date (descending)
    all_entries = list(url_map.values())
    sorted_entries = sorted(all_entries, key=lambda x: x[0], reverse=True)

    # Force write if schema migration is needed (existing entries < 5 columns or new header needed)
    schema_migration_needed = False
    if existing_entries and len(existing_entries[0]) < 5:
        schema_migration_needed = True

    if new_count > 0 or len(sorted_entries) != len(existing_entries) or schema_migration_needed:
        with open(aggregated_file, 'w', encoding='utf-8') as f:
            f.write("# Aggregated URLs\n\n| Date | Source Note | URL | Status | Source UUID |\n| :--- | :--- | :--- | :--- | :--- |\n")
            for entry in sorted_entries:
                # Ensure entry has 5 elements
                d, s, u, st = entry[0], entry[1], entry[2], entry[3]
                uid = entry[4] if len(entry) > 4 else ""
                f.write(f"| {d} | {s} | {u} | {st} | {uid} |\n")
        logger.info(f"Updated aggregated list. Added {new_count} new URLs.")
    else:
        logger.info("No new URLs found.")

if __name__ == "__main__":
    main()