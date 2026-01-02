# Obsidian Vault Utilities

**Author**: [[hayward-kory]]
**Last Updated**: 2026-01-02

- **Location**: `_obsidian-vault-utilities`
> **Note**: This is the root of the Git repository, independent of the parent Vault.

This directory contains a suite of Python automation scripts designed to enhance the Obsidian experience through intelligence, maintenance, and structure.

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

### `news_agent.py`
- **Intent**: A robust content fetcher and AI summarizer. It turns URLs into structured, high-value markdown notes.
- **Modes**:
    - `fetch`: Downloads content from `_notes/_aggregated-urls.md`, removing limits on text length. Connects to Local LLM if configured.
    - `digest`: Compiles daily readings into a "Daily Intelligence Brief".
    - `review`: Synthesizes weekly notes into a "Strategic Horizon" review.
- **Usage**:
  ```bash
  python3 news_agent.py --mode fetch
  ```

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
  python3 extract_urls.py
  ```

---

## Generators

### `linkedin_individual.py`
- **Intent**: Converts a CSV export of LinkedIn connections into individual "Person" nodes in the vault.
- **Feature**: Automatically sorts files into alphabetical subdirectories (`A-Z`) to prevent folder overload.
- **Usage**:
  1. Place CSV in `_artifacts`.
  2. Check `config.py`.
  3. Run:
     ```bash
     python3 linkedin_individual.py
     ```

### `migrate_individuals.py`
- **Intent**: A one-time migration utility used to restructure the `_individuals` folder from a flat list into A-Z subdirectories.
- **Usage**:
  ```bash
  python3 migrate_individuals.py
  ```
  *(Run once found in `_individuals`)*

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
