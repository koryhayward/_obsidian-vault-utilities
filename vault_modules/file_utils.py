import os
import pathlib
import re

def iter_files(root: pathlib.Path, extension: str = '.md'):
    """
    Yields pathlib.Path objects for all files with the given extension,
    skipping hidden directories (starting with .).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # Modify dirnames in-place to skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        
        for file in filenames:
            if file.endswith(extension):
                yield pathlib.Path(dirpath) / file

def sanitize_filename(text: str) -> str:
    """
    Sanitize text to be safe for filenames.
    Alphanumeric, spaces, underscores, hyphens only.
    """
    # Keep only safe chars
    safe = "".join([c for c in text if c.isalnum() or c in (' ', '-', '_')]).strip()
    return safe
