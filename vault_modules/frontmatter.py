import re
import yaml

def parse(content: str) -> dict:
    """
    Parse content to extract frontmatter. 
    Returns a dictionary of frontmatter data.
    """
    fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
    if not fm_match:
        return {}
    fm_text = fm_match.group(1)
    try:
        return yaml.safe_load(fm_text) or {}
    except Exception:
        return {}

def extract_frontmatter_raw(content: str) -> str:
    """Attributes existing raw frontmatter block string"""
    match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
    if match:
        return match.group(1)
    return ""

def replace_frontmatter(content: str, new_fm_dict: dict) -> str:
    """
    Replaces the frontmatter of the content with new dictionary.
    """
    new_fm_str = yaml.dump(new_fm_dict, sort_keys=False, default_flow_style=None)
    # Check if FM exists
    if content.startswith('---'):
        return re.sub(r'^---\n(.*?)\n---', f"---\n{new_fm_str}---", content, count=1, flags=re.DOTALL)
    else:
        return f"---\n{new_fm_str}---\n{content}"
