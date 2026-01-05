"""
Remove 'author: "[[hayward-kory]]"' from markdown frontmatter.
"""
import os
import pathlib
import re

VAULT_ROOT = pathlib.Path(os.environ.get('VAULT_ROOT', '/Users/kory/_vault'))

def process_file(path: pathlib.Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to match the frontmatter block
        # We look for the pattern strictly in the frontmatter.
        
        def remove_author(match):
            fm_content = match.group(1)
            lines = fm_content.splitlines(keepends=True)
            # Filter out the specific author line
            # We strip whitespace from the comparison line to be robust against minor formatting diffs,
            # but the request was specific about 'author: "[[hayward-kory]]"'
            # We'll check for the exact string or close variations just in case.
            
            new_lines = []
            for line in lines:
                if 'author: "[[hayward-kory]]"' in line:
                    continue
                new_lines.append(line)
            
            return f"---\n{''.join(new_lines)}---"

        # Match content between first --- and second ---
        new_content = re.sub(r'^---\n(.*?)\n---', remove_author, content, count=1, flags=re.DOTALL)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
            
    except Exception as e:
        print(f"Error processing {path}: {e}")
    return False

def main():
    modified_count = 0
    print(f"Scanning vault at: {VAULT_ROOT}")
    
    for root, dirs, files in os.walk(VAULT_ROOT):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.md'):
                path = pathlib.Path(root) / file
                if process_file(path):
                    modified_count += 1
                    # print(f"Modified: {path.name}") # Verbose logging can be enabled if needed

    print(f"Finished. Modified {modified_count} files.")

if __name__ == "__main__":
    main()
