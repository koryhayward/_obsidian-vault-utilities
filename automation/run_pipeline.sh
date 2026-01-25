#!/bin/bash

# Title: Obsidian Vault Pipeline
# Description: Automates the URL extraction, summarization, and cleanup workflow.

# Define Paths
# Assumes the vault is located at ~/_vault. Adjust if necessary.
VAULT_ROOT="$HOME/_vault"
UTILS_DIR="$VAULT_ROOT/_obsidian-vault-utilities"
VENV_ACTIVATE="$VAULT_ROOT/.venv/bin/activate"

# 1. Activate Virtual Environment
if [ -f "$VENV_ACTIVATE" ]; then
    source "$VENV_ACTIVATE"
else
    echo "Error: Virtual environment not found at $VENV_ACTIVATE"
    echo "Please create it or check the path."
    exit 1
fi

# 2. Navigate to Utilities Directory
# This ensures relative imports in python scripts work correctly
cd "$UTILS_DIR" || { echo "Error: Could not cd to $UTILS_DIR"; exit 1; }

echo "=========================================="
echo "Starting Vault Automation Pipeline"
echo "Date: $(date)"
echo "=========================================="

# Step 1: Extract URLs
echo ""
echo "--- [1/3] Extracting URLs ---"
python3 maintenance/extract_urls.py
if [ $? -ne 0 ]; then echo "❌ Extraction failed."; exit 1; fi

# Step 2: Summarize (Fetch Mode)
echo ""
echo "--- [2/3] Summarizing Content ---"
python3 agents/summarizer.py --mode fetch
if [ $? -ne 0 ]; then echo "❌ Summarizer failed."; exit 1; fi

# Step 3: Scrub URLs (Latest Scope)
echo ""
echo "--- [3/3] Scrubbing Processed URLs ---"
python3 maintenance/scrub_urls.py --scope latest
if [ $? -ne 0 ]; then echo "❌ Scrubbing failed."; exit 1; fi

deactivate

echo ""
echo "=========================================="
echo "✅ Pipeline Completed Successfully"
echo "=========================================="
