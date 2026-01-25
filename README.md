# Obsidian Vault Utilities

- **Last Updated**: [[2026-01-05]]
- **Location**: `_obsidian-vault-utilities`
> **Note**: This is the root of the Git repository, independent of the parent Vault.

This directory contains a suite of Python automation scripts designed to enhance the Obsidian experience through intelligence, maintenance, and structure.

---

## Automation Core

### `automation/run_pipeline.sh`
- **Intent**: The master orchestration script. It activates the virtual environment and executes the full Intelligence Pipeline in sequence: Extraction -> Summarization -> Scrubbing.
- **Usage**:
  ```bash
  ./automation/run_pipeline.sh
  ```

---

## Core Configuration

### `config.py`
- **Intent**: Acts as the central nervous system for all other scripts. It defines absolute paths for the vault directories and handles environment variables (like `OPENAI_API_KEY`).
- **Features**:
    - **Local LLM Support**: Can be configured to use a local LLM via LM Studio (default: `openai/gpt-oss-20b`) instead of OpenAI's API.
    - **Toggle**: Set `USE_LOCAL_LLM = True` in the file to switch modes.
- **Usage**:
  ```python
  import config
  ```
  *Imported by other scripts. Edit this file to change directory structures or key file locations.*

---

## Intelligence Agents

### `summarizer.py`
- **Intent**: A robust content fetcher and AI summarizer. It turns URLs into structured, high-value markdown notes.
- **Modes**:
    - `fetch`: Downloads content from `_notes/_aggregated-urls.md`, removing limits on text length. Connects to Local LLM if configured.
    - `digest`: Compiles daily readings into a "Daily Intelligence Brief".
    - `review`: Synthesizes weekly notes into a "Strategic Horizon" review.
- **Usage**:
  ```bash
  # Process URLs from aggregated list (saves to _articles)
  python3 agents/summarizer.py --mode fetch

  # Process and save to a custom directory relative to Vault Root
  python3 agents/summarizer.py --mode fetch --output-dir _research/ai-papers
  ```
- **New Features**:
    - **PDF Support**: Automatically extracts text from PDF links.
    - **Custom Output**: `--output-dir` allows targeting specific folders for research.

### `auto_tagger.py`
- **Intent**: Uses OpenAI to audit recent notes and suggest relevant tags, keeping the graph interconnected without manual friction.
- **Requirements**: `OPENAI_API_KEY` (or Local LLM if updated).
- **Usage**:
  ```bash
  python3 auto_tagger.py
  ```
  *(Outputs to `_dashboards/auto_tagger_suggestions.md`)*

---

## Maintenance & Structure

### `resurface.py`
- **Intent**: Combats "digital hoarder" syndrome by identifying:
    - **Orphans**: Notes with zero incoming links.
    - **Dusty Notes**: Active notes untouched for >90 days.
- **Usage**:
  ```bash
  python3 resurface.py
  ```
  *(Outputs to `_dashboards/resurfacing.md`)*

### `map_vault.py`
- **Intent**: Visualizes the vault's physical structure. Generates an ASCII tree view with file counts and sizes to help spot bloat.
- **Usage**:
  ```bash
  python3 map_vault.py
  ```
  *(Outputs to `_artifacts/vault_structure.md`)*

### `extract_urls.py`
- **Intent**: Scans Daily Notes for URLs, extracting them line-by-line (memory efficient) into a master processing queue.
- **Usage**:
  ```bash
  # Scan all daily notes
  python3 extract_urls.py

  # Scan a specific file
  python3 extract_urls.py --file path/to/note.md
  ```
- **New Features**:
    - **Source UUID**: Tracks the UUID of the source note.
    - **CLI Target**: Use `--file` to scan a single note instead of the whole folder.

### `scrub_urls.py`
- **Intent**: Cleans daily notes by removing URLs that have already been aggregated into `_aggregated-urls.md`. Supports `latest` or `all` scope to reduce clutter.
- **Usage**:
  ```bash
  python3 maintenance/scrub_urls.py --scope latest
  ```
  python3 maintenance/scrub_urls.py --scope latest
  ```

---

## Media Tools

### `media/yt-scribe`
- **Intent**: Downloads YouTube subtitles or transcribes audio using OpenAI Whisper.
- **Usage**:
  ```bash
  ./media/yt-scribe <VIDEO_URL> [OUTPUT_DIR]
  ```

---
---

## Generators

### `generators/linkedin_people.py`
- **Intent**: Converts a CSV export of LinkedIn connections into individual "Person" nodes in the vault.
- **Feature**: Automatically sorts files into alphabetical subdirectories (`A-Z`) to prevent folder overload.
- **Usage**:
  1. Place CSV in `_artifacts`.
  2. Check `config.py`.
  3. Run:
     ```bash
     python3 generators/linkedin_people.py
     ```

### `maintenance/migrate_individuals.py`
- **Intent**: A one-time migration utility used to restructure the `_individuals` folder from a flat list into A-Z subdirectories.
- **Usage**:
  ```bash
  python3 maintenance/migrate_individuals.py
  ```
  *(Run once found in `_individuals`)*

### `generators/organizations.py`
- **Intent**: Scans individual notes for employer data and generates/updates organization files in `_organizations`.
- **Features**: 
    - **Intelligent Linking**: Wraps organization names in wikilinks.
    - **Context**: Adds Dataview queries to link employees back to the organization.
    - **Templating**: Fixes templater placeholders (UUIDs, Dates) at runtime.
- **Usage**:
  ```bash
  python3 generators/organizations.py
  ```

### `maintenance/deep_clean/migrate_templates.py`
- **Intent**: Refactors the vault from using `template: "[[name]]"` frontmatter to `#template/name` tags.
- **Usage**:
  ```bash
  python3 maintenance/deep_clean/migrate_templates.py
  ```

### `maintenance/deep_clean/remove_author.py`
- **Intent**: Bulk removes the `author: "[[hayward-kory]]"` field from all markdown files to clean up metadata.
- **Usage**:
  ```bash
  python3 maintenance/deep_clean/remove_author.py
  ```

### `maintenance/deep_clean/repair_frontmatter.py`
- **Intent**: Fixes broken YAML frontmatter (missing newlines before closing `---`) caused by bulk edits.
- **Usage**:
  ```bash
  python3 maintenance/deep_clean/repair_frontmatter.py
  ```

### `maintenance/deep_clean/remove_met_via.py`
- **Intent**: Removes the specific "Met via" line containing a ghost link to `[[Previous Job]]` from individual notes.
- **Usage**:
  ```bash
  python3 maintenance/deep_clean/remove_met_via.py
  ```

### `maintenance/deep_clean/remove_dates.py`
- **Intent**: Removes `created` and `modified` frontmatter fields from Individual and Organization notes to declutter the graph.
- **Usage**:
  ```bash
  python3 maintenance/deep_clean/remove_dates.py
  ```

---

## Setup & Requirements

- **Python**: 3.10+
- **Local LLM (Optional but Recommended)**: 
  - Install [LM Studio](https://lmstudio.ai/).
  - Load a model (e.g., `openai/gpt-oss-20b`).
  - Start the Local Server on port `1234`.
- **Environment**: Set `OPENAI_API_KEY` if *not* using Local LLM.
- **Dependencies**: 
  - `openai`
  - `requests`
  - `beautifulsoup4`
  - `newspaper3k`
  - `pypdf`
  - `python-frontmatter`
