"""
Repair broken frontmatter delimiters (e.g. 'value---').
"""
import os
import pathlib
import re

VAULT_ROOT = pathlib.Path(os.environ.get('VAULT_ROOT', '/Users/kory/_vault'))

def process_file(path: pathlib.Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the closing --- of frontmatter being on the same line as content
        # Frontmatter starts with ---\n
        # We want to find the closing ---.
        # Use regex to find start of file frontmatter, then look for the end.
        
        # This matches: start, any content, then a char that isn't newline, then --- followed by newline or EOF
        # We capture the char in group 2.
        pattern = r'^(?s)(---\n.*?)([^\n])---(\n|$)'
        
        def fixer(match):
            # match.group(1): Start of FM + content up to last char
            # match.group(2): The last char of content (non-newline)
            # match.group(3): Newline or EOF after ---
            
            # We want to insert a newline between char and ---
            return f"{match.group(1)}{match.group(2)}\n---{match.group(3)}"

        new_content = re.sub(pattern, fixer, content, count=1)

        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
            
    except Exception as e:
        print(f"Error processing {path}: {e}")
    return False

def main():
    modified_count = 0
    print(f"Scanning vault for repair at: {VAULT_ROOT}")
    
    for root, dirs, files in os.walk(VAULT_ROOT):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.md'):
                path = pathlib.Path(root) / file
                if process_file(path):
                    modified_count += 1
    
    print(f"Finished. Repaired {modified_count} files.")

if __name__ == "__main__":
    main()
