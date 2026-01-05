"""
Migrate 'template' frontmatter field to '#template/type' tag.
"""
import os
import pathlib
import sys
import re

# Determine Vault Root
# Default to current working dir if env var not set, or typical path
VAULT_ROOT = pathlib.Path(os.environ.get('VAULT_ROOT', '/Users/kory/_vault'))

def get_template_tag(template_value: str) -> str:
    # Value is typically "[[template-name]]" or "template-name"
    # Remove quotes, brackets
    clean = template_value.replace('[[', '').replace(']]', '').replace('"', '').replace("'", "").strip()
    
    # Check for "template-" prefix and strip it
    if clean.startswith('template-'):
        short_name = clean[len('template-'):]
        # logic: #template/individual
        return f"#template/{short_name}"
    
    # If no prefix, just use the value? e.g. "prime" -> #template/prime
    return f"#template/{clean}"

def process_file(path: pathlib.Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file has frontmatter
        if not content.startswith('---'):
            return False
            
        # Extract frontmatter
        fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        if not fm_match:
            return False
            
        fm_content = fm_match.group(1)
        
        # Check if 'template:' exists in FM (simple check)
        if 'template:' not in fm_content:
            return False

        lines = fm_content.splitlines()
        new_lines = []
        tag_to_add = None
        has_template_field = False
        
        for line in lines:
            # Check for template field line
            # Regex for robust matching of key: value
            m = re.match(r'^template:\s*(.*)$', line)
            if m:
                has_template_field = True
                val = m.group(1).strip()
                if val:
                    tag_to_add = get_template_tag(val)
                # We do NOT append this line to new_lines, effectively removing it.
                continue
            
            new_lines.append(line)
        
        if not has_template_field or not tag_to_add:
            return False

        # Add the tag
        # We need to find where 'tags:' is, or add it.
        # Check if 'tags:' line exists
        tags_index = -1
        for i, line in enumerate(new_lines):
            if re.match(r'^tags:\s*$', line.strip()) or re.match(r'^tags:\s*\[.*\]', line.strip()):
                tags_index = i
                break
        
        target_tag_line = f'- "{tag_to_add}"'
        
        if tags_index != -1:
            # Found tags:
            # If it's inline list tags: [a, b], we might have a hard time appending without parsing.
            # Assuming YAML list format based on user's vault style seen previously:
            # tags:
            # - "#foo"
            
            # We will insert after the tags: line
            # But wait, if it is 'tags: []', then we need to change it?
            # User's files usually show:
            # tags:
            # - "#tag"
            
            # Let's insert at tags_index + 1
            new_lines.insert(tags_index + 1, target_tag_line)
        else:
            # No tags field, append to end of FM
            new_lines.append("tags:")
            new_lines.append(target_tag_line)

        # Reconstruct content
        new_fm = "\n".join(new_lines)
        new_full_content = re.sub(r'^---\n(.*?)\n---', f"---\n{new_fm}\n---", content, count=1, flags=re.DOTALL)
        
        if new_full_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_full_content)
            return True

    except Exception as e:
        print(f"Error processing {path}: {e}")
    return False

def main():
    count = 0
    print(f"Scanning vault... {VAULT_ROOT}")
    
    for root, dirs, files in os.walk(VAULT_ROOT):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.md'):
                path = pathlib.Path(root) / file
                if process_file(path):
                    count += 1
                    # print(f"Migrated: {path.name}")

    print(f"Finished. Migrated {count} files.")

if __name__ == "__main__":
    main()
