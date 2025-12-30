import os
import logging
from datetime import datetime
import config

# --- CONFIGURATION ---
SEARCH_DIR = config.VAULT_ROOT
OUTPUT_FILE = os.path.join(config.DASHBOARDS_DIR, 'auto_tagger_suggestions.md')
IGNORE_DIRS = {'.git', '.obsidian', '.trash', '_templates', '_scripts', '_artifacts', '_obsidian-vault-utilities'}
SYSTEM_PROMPT = "You are an expert librarian. Analyze the following note content and suggest 3-5 relevant hashtags (kebab-case). Return ONLY the tags significantly separated by spaces."

setup_logger = logging.getLogger('auto_tagger')
setup_logger.setLevel(logging.INFO)

def get_untagged_recent_notes(root_dir, days=7):
    """Finds notes modified recently that have no tags."""
    candidates = []
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (datetime.now() - mtime).days <= days:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(2000) # Read first 2k chars
                            if "#" not in content[:500]: # Simple heuristic for frontmatter/top tags
                                candidates.append((filepath, content))
                except Exception:
                    pass
    return candidates

def get_ai_tags(content):
    """Calls OpenAI to get tags."""
    if not config.OPENAI_API_KEY:
        return None
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        setup_logger.error(f"API Error: {e}")
        return None

def main():
    print("--- Auto-Tagger Intelligence ---")
    
    candidates = get_untagged_recent_notes(SEARCH_DIR)
    print(f"Found {len(candidates)} recent potential untagged notes.")
    
    if not candidates:
        print("No candidates found.")
        return

    report = f"""---
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags: [dashboard, ai, suggestions]
---

# AI Tag Suggestions
> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
    
    processed_count = 0
    # Process top 5 candidates to save tokens/time
    for filepath, content in candidates[:5]:
        filename = os.path.basename(filepath)
        print(f"Analyzing: {filename}")
        
        suggested_tags = get_ai_tags(content)
        
        if suggested_tags:
            report += f"## [[{os.path.splitext(filename)[0]}]]\n"
            report += f"**Suggested**: `{suggested_tags}`\n\n"
            processed_count += 1
        elif not config.OPENAI_API_KEY:
            report += f"## [[{os.path.splitext(filename)[0]}]]\n"
            report += "**Error**: OpenAI API Key missing. Please set `OPENAI_API_KEY`.\n\n"
            break # Stop if no key
            
    if processed_count == 0 and not config.OPENAI_API_KEY:
        print("Skipped AI processing (No Key).")
    
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Suggestions saved to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving report: {e}")

if __name__ == "__main__":
    main()
