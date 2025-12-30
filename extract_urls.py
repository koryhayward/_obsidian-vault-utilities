"""
Title: URL Extractor
Filename: extract_urls.py
Created: 2025-12-17
Last Updated: 2025-12-30

Description:
    A stream-processing utility that harvests URLs from daily notes. It uses a memory-efficient 
    line-by-line reading approach to handle large markdown files without performance hits.
    The primary purpose is to feed the 'Fetch' mode of the News Agent.

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
import config

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
table_row_pattern = re.compile(r'^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\[\[.*?\]\])\s*\|\s*(.*?)\s*\|$')

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
                    entries.append((match.group(1), match.group(2), match.group(3)))
    except Exception as e:
        logger.error(f"Error reading master file: {e}")
    return entries

def extract_urls_from_file(filepath, logger):
    urls = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                found = url_pattern.findall(line)
                if found:
                    urls.update(found)
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
    return list(urls)

def main():
    logger = setup_logging()
    logger.info(f"Scanning directory: {search_dir}")

    existing_entries = parse_existing_table(aggregated_file, logger)
    existing_urls = {entry[2] for entry in existing_entries}
    new_entries = []

    if os.path.exists(search_dir):
        for root, dirs, files in os.walk(search_dir):
            for filename in files:
                if date_file_pattern.match(filename):
                    date = filename.replace('.md', '')
                    filepath = os.path.join(root, filename)
                    
                    urls = extract_urls_from_file(filepath, logger)
                    
                    for url in urls:
                        if url not in existing_urls:
                            entry = (date, f"[[{date}]]", url)
                            existing_entries.append(entry)
                            existing_urls.add(url)
                            new_entries.append(entry)
    else:
        logger.error(f"Search directory not found: {search_dir}")

    if new_entries:
        sorted_entries = sorted(existing_entries, key=lambda x: x[0], reverse=True)
        with open(aggregated_file, 'w', encoding='utf-8') as f:
            f.write("# Aggregated URLs\n\n| Date | Source Note | URL |\n| :--- | :--- | :--- |\n")
            for date, source, url in sorted_entries:
                f.write(f"| {date} | {source} | {url} |\n")
        logger.info(f"Added {len(new_entries)} new URLs.")
    else:
        logger.info("No new URLs found.")

if __name__ == "__main__":
    main()