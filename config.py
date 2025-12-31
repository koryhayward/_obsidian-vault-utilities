"""
Title: Configuration Settings
Filename: config.py
Created: 2025-12-17
Last Updated: 2025-12-30

Description:
    The central source of truth for the vault's file system layout. All other scripts import 
    this module to ensure consistency in path resolution. It also handles secure retrieval 
    of environment variables.

Key Features:
    - **Absolute Path Resolution**: Anchors all paths to `VAULT_ROOT`.
    - **Directory Constants**: Defines `_dashboards`, `_artifacts`, `_templates`, etc.
    - **API Key Management**: Checks for `OPENAI_API_KEY`.

Usage:
    import config
    print(config.VAULT_ROOT)
"""
import os
import sys

# --- ENVIRONMENT DETECTION ---
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# The Vault Root is the parent of the script directory
VAULT_ROOT = os.path.dirname(SCRIPT_DIR)

# --- DIRECTORY CONSTANTS ---
NOTES_DIR = os.path.join(VAULT_ROOT, "_notes") 
ARTIFACTS_DIR = os.path.join(VAULT_ROOT, "_artifacts")
DASHBOARDS_DIR = os.path.join(VAULT_ROOT, "_dashboards")
TEMPLATES_DIR = os.path.join(VAULT_ROOT, "_templates")
LOGS_DIR = os.path.join(ARTIFACTS_DIR, "logs")

# Specific File Paths
AGGREGATED_FILE = os.path.join(NOTES_DIR, "_aggregated-urls.md")
# ARTICLES_DIR = os.path.join(VAULT_ROOT, "_articles") 
ARTICLES_DIR = os.path.join(NOTES_DIR, "_articles") 

# --- API KEYS ---
# We retrieve the key here as a string only.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create directories if missing
for d in [LOGS_DIR, ARTICLES_DIR]:
    os.makedirs(d, exist_ok=True)

# Stop script if key is missing (Safety Check)
if not OPENAI_API_KEY:
    # Optional: print warning but don't crash if you want other scripts to run
    print("WARNING: OPENAI_API_KEY not found in environment variables.")