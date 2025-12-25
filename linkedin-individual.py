import csv
import uuid
import datetime
import re
import os
import logging
from logging.handlers import RotatingFileHandler
import config

# --- CONFIGURATION FROM UTILS ---
CSV_FILENAME = 'linkedin-connections-20251201.csv'
TEMPLATE_REL_PATH = os.path.join('_templates', 'template-individual.md')
OUTPUT_REL_PATH = '_individuals'

# Construct Absolute Paths using config.py
csv_file = os.path.join(config.ARTIFACTS_DIR, CSV_FILENAME)
template_file = os.path.join(config.VAULT_ROOT, TEMPLATE_REL_PATH)
output_dir = os.path.join(config.VAULT_ROOT, OUTPUT_REL_PATH)
log_file = os.path.join(config.LOGS_DIR, 'linkedin_individual.log')

def setup_logging():
    logger = logging.getLogger('linkedin_gen')
    logger.setLevel(logging.INFO)
    if logger.hasHandlers(): logger.handlers.clear()

    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler())
    return logger

def yaml_quote(text):
    if not text: return ""
    text_str = str(text)
    escaped = text_str.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'

def clean_text(text):
    if not text: return ""
    return str(text).strip()

def main():
    logger = setup_logging()
    logger.info(f"Starting Generator (Lite). Vault Root: {config.VAULT_ROOT}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found at: {csv_file}")
            print(f"Please place '{CSV_FILENAME}' in '{config.ARTIFACTS_DIR}'")
            return
            
        if not os.path.exists(template_file):
            logger.error(f"Template file not found at: {template_file}")
            print(f"Template missing: {template_file}")
            return

        # Load Template
        with open(template_file, 'r', encoding='utf-8') as f:
            template_str = f.read()

        processed_count = 0
        
        # --- CSV PROCESSING ---
        with open(csv_file, 'r', encoding='utf-8', errors='replace') as f:
            start_pos = f.tell()
            
            # Robust skip logic: Skip first 3 lines blindly as per requirement
            for _ in range(3):
                next(f, None)
                
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                try:
                    # Map CSV keys to Variables
                    first_name = clean_text(row.get('First Name', ''))
                    last_name = clean_text(row.get('Last Name', ''))
                    
                    if not first_name and not last_name: continue # Skip empty rows

                    # Filename Generation
                    safe_last = "".join([c for c in last_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                    safe_first = "".join([c for c in first_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                    identity_name = f"{safe_last}-{safe_first}"
                    if not identity_name or identity_name == "-":
                        identity_name = f"Unknown-Contact-{i}"

                    full_name = f"{first_name} {last_name}".strip()
                    role = clean_text(row.get('Position', ''))
                    company = clean_text(row.get('Company', ''))
                    email = clean_text(row.get('Email Address', ''))
                    url = clean_text(row.get('URL', ''))
                    
                    # Template Logic
                    content = template_str
                    content = content.replace('<% tp.user.generate_uuid() %>', str(uuid.uuid4()))
                    today = datetime.date.today().strftime("%Y-%m-%d")
                    content = content.replace('<% tp.file.creation_date("YYYY-MM-DD") %>', today)
                    content = content.replace('<% tp.file.last_modified_date("YYYY-MM-DD") %>', today)
                    
                    # Regex Replacements
                    content = re.sub(r'identity: "\[\[<%[\s\S]*?%>\]\]"', f'identity: "[[{identity_name}]]"', content)
                    content = re.sub(r'# <%[\s\S]*?individualName[\s\S]*?%>', f'# {identity_name}', content)
                    
                    replacements = {
                        r'^name-full:\s*$': f'name-full: {yaml_quote(full_name)}',
                        r'^name-first:\s*$': f'name-first: {yaml_quote(first_name)}',
                        r'^name-last:\s*$': f'name-last: {yaml_quote(last_name)}',
                        r'^role:\s*$': f'role: {yaml_quote(role)}',
                        r'^employers:\s*$': f'employers: {yaml_quote(company)}',
                        r'^email:\s*$': f'email: {yaml_quote(email)}',
                        r'^linkedin:\s*$': f'linkedin: {yaml_quote(url)}'
                    }
                    
                    for pattern, replacement in replacements.items():
                        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

                    # Write
                    filepath = os.path.join(output_dir, f"{identity_name}.md")
                    with open(filepath, 'w', encoding='utf-8') as outfile:
                        outfile.write(content)
                    
                    processed_count += 1
                    
                except Exception as row_error:
                    logger.warning(f"Error processing row {i}: {row_error}")

        logger.info(f"Successfully generated {processed_count} notes.")

    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
        raise

if __name__ == "__main__":
    main()