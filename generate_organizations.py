#!/usr/bin/env python3
"""Generate organization notes from individual notes.

- Scans `_individuals/**/*.md` for `employers` front‑matter entries.
- Normalises employer strings (splits on commas, strips whitespace).
- Creates one markdown file per unique employer in `_organizations/`.
- Uses the `template-organization.md` content as a base, inserting the organization name.
- Removes Templater placeholder lines from the template.
- Adds a Dataview query that lists all individuals whose `employers` contain the organization.
"""
import os
import re
import pathlib
import yaml
import uuid
import datetime

BASE_DIR = pathlib.Path(os.getenv('VAULT_ROOT', '/Users/kory/_vault'))
INDIVIDUALS_DIR = BASE_DIR / '_individuals'
ORG_DIR = BASE_DIR / '_organizations'
TEMPLATE_PATH = BASE_DIR / '_templates' / 'template-organization.md'

def load_template() -> str:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        raw = f.read()
    
    # We want to remove the specific Templater Javascript prompt block for the name, 
    # but initially we keep the raw string to do replacements.
    # The template has a block like:
    # name: "[[<%*
    #   let companyName = await tp.system.prompt("Company Name");
    #   await tp.file.rename(companyName);
    #   tR += companyName;
    # %>]]"
    
    # We will handle the "name:" field replacement via regex in create_org_file
    # matching strictly the multi-line block if possible, or just identifying where it is.
    return raw

def parse_frontmatter(content: str) -> dict:
    # Frontmatter is between the first pair of '---' lines
    fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
    if not fm_match:
        return {}
    fm_text = fm_match.group(1)
    try:
        return yaml.safe_load(fm_text) or {}
    except Exception:
        return {}

def extract_employers(fm: dict) -> list[str]:
    # Employers might already be wikilinked like "[[Deloitte]]" or plain "Deloitte"
    employers = fm.get('employers', '')
    if not isinstance(employers, str):
        return []
    
    # Clean up wikilink brackets if present to get raw names
    # e.g. "[[Deloitte]]" -> "Deloitte"
    cleaned_employers = []
    
    # Split on commas and semicolons
    raw_list = [e.strip() for e in re.split(r'[;,]', employers) if e.strip()]
    
    for item in raw_list:
        # Strip [[ and ]]
        item = item.replace('[[', '').replace(']]', '')
        if item:
            cleaned_employers.append(item)
            
    return cleaned_employers

def ensure_org_dir():
    ORG_DIR.mkdir(parents=True, exist_ok=True)

def create_org_file(org_name: str, template: str) -> pathlib.Path:
    content = template
    
    # 1. Generate Runtime Values
    new_uuid = str(uuid.uuid4())
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # 2. Replace Templater UUID
    content = content.replace('<% tp.user.generate_uuid() %>', new_uuid)
    
    # 3. Replace Templater Dates
    content = content.replace('<% tp.file.creation_date("YYYY-MM-DD") %>', today)
    content = content.replace('<% tp.file.last_modified_date("YYYY-MM-DD") %>', today)
    
    # 4. Handle "name:" field
    # The regex needs to match the multi-line templater block starting at name: "[[<%* ... %>]]"
    # match starts with name: and ends with "
    # We'll try a regex that matches name: "[[<%* ... %>]]" allowing for newlines.
    
    # Regex for the specific complex block in template-organization.md
    # name: "[[<%*
    #   ...
    # %>]]"
    pattern_name_block = r'name:\s*"\[\[<%\*.*?%>\]\]"'
    replacement_name = f'name: "[[{org_name}]]"'
    content = re.sub(pattern_name_block, replacement_name, content, flags=re.DOTALL)
    
    # Fallback/Safety: if the template changed and regex didn't match, maybe it's just name: ""
    # If the regex matched, content is updated.
    
    # 5. Handle the Header "# <%* tR += companyName %>"
    pattern_header = r'# <%\* tR \+= companyName %>'
    replacement_header = f'# {org_name}'
    content = re.sub(pattern_header, replacement_header, content)

    # 6. Final cleanup of any lingering <% ... %> if we missed something specific? 
    # For now, we trust specific replacements.
    
    safe_name = org_name.replace('/', '_')
    file_path = ORG_DIR / f"{safe_name}.md"
    
    # Only write if content meaningfully changed or file doesn't exist? 
    # Requirement implies checking/updating. Overwriting is fine.
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return file_path

def append_dataview(org_file: pathlib.Path, org_name: str):
    # Check if dataview already exists to avoid duplication if we re-run and append?
    # Actually create_org_file overwrites the file with template content, so we are fresh.
    # But wait, create_org_file overwrites. 
    # Yes, create_org_file returns valid path after writing.
    
    # We need to ensure we don't double append if we ran this logic differently, 
    # but since create_org_file wipes it, we are safe.
    
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
    for md_path in INDIVIDUALS_DIR.rglob('*.md'):
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        fm = parse_frontmatter(content)
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
