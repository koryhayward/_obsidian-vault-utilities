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

BASE_DIR = pathlib.Path(os.getenv('VAULT_ROOT', '/Users/kory/_vault'))
INDIVIDUALS_DIR = BASE_DIR / '_individuals'
ORG_DIR = BASE_DIR / '_organizations'
TEMPLATE_PATH = BASE_DIR / '_templates' / 'template-organization.md'

def load_template() -> str:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        raw = f.read()
    # Remove Templater placeholder lines (those containing "let companyName" or "await tp.system.prompt" or "%>")
    cleaned_lines = [ln for ln in raw.splitlines() if not (
        'let companyName' in ln or 'await tp.system.prompt' in ln or '%>' in ln)]
    return "\n".join(cleaned_lines)

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
    employers = fm.get('employers', '')
    if not isinstance(employers, str):
        return []
    # Split on commas and semicolons, strip whitespace
    return [e.strip() for e in re.split(r'[;,]', employers) if e.strip()]

def ensure_org_dir():
    ORG_DIR.mkdir(parents=True, exist_ok=True)

def create_org_file(org_name: str, template: str) -> pathlib.Path:
    # Replace the placeholder name line with the actual organization name
    new_content = re.sub(r'name: ".*?"', f'name: "{org_name}"', template)
    # Replace the heading line ("# <...>") with the organization name
    new_content = re.sub(r'# <.*?>', f'# {org_name}', new_content)
    safe_name = org_name.replace('/', '_')
    file_path = ORG_DIR / f"{safe_name}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
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
        f.write('\n## contacts-connections\n')
        f.write(dv)

def main():
    ensure_org_dir()
    template = load_template()
    org_to_individuals = {}
    for md_path in INDIVIDUALS_DIR.rglob('*.md'):
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        fm = parse_frontmatter(content)
        employers = extract_employers(fm)
        for org in employers:
            org_to_individuals.setdefault(org, []).append(md_path)
    for org_name in sorted(org_to_individuals.keys()):
        org_file = create_org_file(org_name, template)
        append_dataview(org_file, org_name)
    print(f"Generated {len(org_to_individuals)} organization files.")

if __name__ == "__main__":
    main()
