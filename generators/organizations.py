#!/usr/bin/env python3
"""Generate organization notes from individual notes.
Refactored to use vault_modules.
"""
import os
import re
import pathlib
import uuid
import datetime
import sys

# Adjust path to find vault_modules if running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vault_modules import frontmatter, file_utils
import config

BASE_DIR = pathlib.Path(config.VAULT_ROOT)
INDIVIDUALS_DIR = BASE_DIR / '_individuals'
ORG_DIR = BASE_DIR / '_organizations'
TEMPLATE_PATH = BASE_DIR / '_templates' / 'template-organization.md'

def load_template() -> str:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def extract_employers(fm: dict) -> list[str]:
    employers = fm.get('employers', '')
    if not isinstance(employers, str):
        return []
    
    cleaned_employers = []
    raw_list = [e.strip() for e in re.split(r'[;,]', employers) if e.strip()]
    
    for item in raw_list:
        item = item.replace('[[', '').replace(']]', '')
        if item:
            cleaned_employers.append(item)
            
    return cleaned_employers

def ensure_org_dir():
    ORG_DIR.mkdir(parents=True, exist_ok=True)

def create_org_file(org_name: str, template: str) -> pathlib.Path:
    content = template
    new_uuid = str(uuid.uuid4())
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    content = content.replace('<% tp.user.generate_uuid() %>', new_uuid)
    content = content.replace('<% tp.file.creation_date("YYYY-MM-DD") %>', today)
    content = content.replace('<% tp.file.last_modified_date("YYYY-MM-DD") %>', today)
    
    pattern_name_block = r'name:\s*"\[\[<%\*.*?%>\]\]"'
    replacement_name = f'name: "[[{org_name}]]"'
    content = re.sub(pattern_name_block, replacement_name, content, flags=re.DOTALL)
    
    pattern_header = r'# <%\* tR \+= companyName %>'
    replacement_header = f'# {org_name}'
    content = re.sub(pattern_header, replacement_header, content)

    safe_name = file_utils.sanitize_filename(org_name)
    file_path = ORG_DIR / f"{safe_name}.md"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return file_path

def append_dataview(org_file: pathlib.Path, org_name: str):
    dv = f"""
```dataview
TABLE name-full as \"Name\", role, email
FROM #individual
WHERE contains(employers, \"{org_name}\")
SORT name-last ASC
```
"""
    with open(org_file, 'a', encoding='utf-8') as f:
        f.write('\n## linked-individuals\n')
        f.write(dv)

def main():
    ensure_org_dir()
    template = load_template()
    org_to_individuals = {}
    
    print("Scanning individual files...")
    for md_path in file_utils.iter_files(INDIVIDUALS_DIR):
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        fm = frontmatter.parse(content)
        employers = extract_employers(fm)
        for org in employers:
            if org:
                org_to_individuals.setdefault(org, []).append(md_path)
            
    print(f"Found {len(org_to_individuals)} unique organizations.")
    
    for org_name in sorted(org_to_individuals.keys()):
        org_file = create_org_file(org_name, template)
        append_dataview(org_file, org_name)
        
    print(f"Generated/Updated {len(org_to_individuals)} organization files.")

if __name__ == "__main__":
    main()
