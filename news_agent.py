"""
Title: News Agent & Intelligence Summarizer
Filename: news_agent.py
Created: 2025-12-17
Last Updated: 2025-12-30
Author: Antigravity (Google DeepMind)

Description:
    A comprehensive intelligence agent designed to ingest specific URLs or PDF documents, extract their full content 
    (without truncation), and produce high-value executive summaries using OpenAI's GPT models. It operates in three 
    distinct modes to support a complete information lifecycle: fetching/processing, daily synthesis (Digest), 
    and weekly strategic review.

Key Features:
    - **Robust Extraction**: Handles standard HTML articles and complex PDFs (using pypdf).
    - **AI Personas**: Uses "Intelligence Analyst", "Chief of Staff", and "Strategic Futurist" system prompts.
    - **No Limits**: Context window raised to 100k tokens; file writing has no character limit.
    - **Lifecycle Management**: Can aggregate individual notes into Daily Digests and Weekly Reviews.

Usage:
    python3 news_agent.py --mode fetch   # Process URLs from aggregated list
    python3 news_agent.py --mode digest  # Create daily digest from today's articles
    python3 news_agent.py --mode review  # Create weekly strategic review

Dependencies:
    - openai, requests, newspaper3k, pypdf, python-frontmatter
    - Environment Variable: OPENAI_API_KEY
"""
import os
import io
import re
import datetime
import argparse
import requests
import frontmatter
from bs4 import BeautifulSoup
from pypdf import PdfReader  # The new PDF tool
from newspaper import Article
from openai import OpenAI
import config

# Initialize Client
if not config.OPENAI_API_KEY:
    print("ERROR: OpenAI API Key not found. Please export OPENAI_API_KEY.")
    exit(1)

client = OpenAI(api_key=config.OPENAI_API_KEY)

# Mimic a real browser to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def clean_filename(title):
    keepcharacters = (' ','.','_')
    safe_title = "".join(c for c in title if c.isalnum() or c in keepcharacters).rstrip()
    return safe_title.replace(" ", "_")[:60]

def fetch_smart_content(url):
    """
    Robust fetcher:
    1. Checks if PDF -> Extracts PDF text.
    2. Tries Newspaper3k for HTML.
    3. Falls back to BeautifulSoup if Newspaper3k fails.
    """
    try:
        # 1. Download content with browser headers
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        
        # --- PATH A: HANDLE PDF ---
        if url.lower().endswith('.pdf') or 'application/pdf' in content_type:
            print(f"  -> Detected PDF...")
            try:
                f = io.BytesIO(response.content)
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Clean up PDF noise
                title = "PDF Document"
                if reader.metadata and reader.metadata.title:
                    title = reader.metadata.title
                
                return title, text
            except Exception as e:
                print(f"  -> PDF Parse Error: {e}")
                return None, None

        # --- PATH B: HANDLE HTML (Article) ---
        # Try Newspaper3k first (best for main content extraction)
        try:
            article = Article(url)
            article.download(input_html=response.content)
            article.parse()
            
            if len(article.text) > 300:
                return article.title, article.text
        except Exception:
            pass # Fail silently and try fallback

        # --- PATH C: FALLBACK (BeautifulSoup) ---
        print("  -> Newspaper failed, attempting gentle scrape...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Kill all script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text()
        
        # Basic cleanup of empty lines
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        title = soup.title.string if soup.title else "Web_Capture"
        return title, clean_text

    except Exception as e:
        print(f"  -> Download failed: {e}")
        return None, None

def get_ai_summary(text, model="gpt-4o-mini", prompt_type="article"):
    system_prompts = {
        "article": """You are a high-level Intelligence Analyst. Your mission is to distill this text into a strategic briefing.
Target Audience: Executive decision-maker.
Format: Markdown.

Output Structure:
1.  **Executive Summary**: 2-3 sentences capturing the core thesis and immediate value.
2.  **Key Intelligence**: Bullet points of factual assertions, data points, or new developments.
3.  **Strategic Implications**: Why this matters. Connection to broader trends (tech, politics, economy).
4.  **Entities & Methodology**: Key people/companies mentioned and how the information was gathered (if stated).
5.  **Critique/Bias Check**: Brief note on potential author bias or missing perspective.""",
        "digest": """You are a Chief of Staff preparing a Daily Intelligence Brief (DIB).
Input: A collection of summarized articles.
Goal: Synthesize, don't just list. Group stories by theme.
Format: Markdown. Do NOT use emojis.

Structure:
# Daily Intelligence Brief
> Date: {{date}}

## Headlines & Critical Alerts
(Top 1-3 most important items that require immediate attention)

## Thematic Threads
(Group stories by theme: e.g., 'Artificial Intelligence', 'Geopolitics', 'Market Shifts'. Connect the dots between separate articles.)

## Signal vs. Noise
(Point out conflicting reports or weak signals worth monitoring)

## Opportunity Radar
(Actionable insights or new tools mentioned)""",
        "review": """You are a Strategic Futurist writing a Weekly Review.
Input: A week's worth of article summaries.
Goal: Identify macro-trends and shifts in the zeitgeist.
Format: Markdown. Do NOT use emojis.

Structure:
# Weekly Strategic Horizon

## 1. The Big Picture
(What was the dominant narrative this week?)

## 2. Emergent Patterns
*   **Trend A**: description...
*   **Trend B**: description...

## 3. Outlier Events
(Events that broke the pattern or signal disruption)

## 4. Forward Outlook
(Predictions for next week based on current trajectory)"""
    }
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompts[prompt_type]},
                {"role": "user", "content": text[:100000]} # Increase limit for long PDFs
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None

def fetch_mode():
    print("--- Fetch Mode (State-Aware) ---")
    if not os.path.exists(config.AGGREGATED_FILE):
        print("Aggregated file not found.")
        return

    # 1. Load All Entries
    entries = []
    headers = []
    # Regex to handle 3 or 4 columns safely
    row_pattern = re.compile(r'^\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|(?:\s*(.*?)\s*\|)?$')
    
    with open(config.AGGREGATED_FILE, 'r') as f:
        lines = f.readlines()

    # Preserve headers
    data_start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("| :---"):
            headers.append(line)
            data_start_idx = i + 1
            break
        headers.append(line)

    # Parse Data
    for line in lines[data_start_idx:]:
        match = row_pattern.match(line.strip())
        if match:
            # (Date, Source, URL, Status)
            status = match.group(4) if match.group(4) else ""
            entries.append({
                'date': match.group(1),
                'source': match.group(2),
                'url': match.group(3),
                'status': status
            })

    # 2. Filter for Processing
    # Only process if status is empty or explicitly 'retry'
    to_process = [e for e in entries if not e['status'] or e['status'] == 'retry']
    
    print(f"Found {len(to_process)} pending URLs out of {len(entries)} total.")

    # 3. Process Loop
    for entry in to_process[:10]: # Batch size limit
        url = entry['url']
        print(f"Processing: {url}")
        
        try:
            # Check if file exists first to avoid re-fetching
            # Need to guess the filename or title first? 
            # Strategy: Fetch -> Clean Title -> Check File -> Save
            
            title, text = fetch_smart_content(url)
            
            if not text or len(text) < 100:
                print("  -> Content inaccessible.")
                entry['status'] = "Error: Content too short"
            else:
                # Generate Safe Filename
                if not title or title == "PDF Document":
                    title = url.split("/")[-1].replace(".pdf", "").replace(".html", "")
                
                safe_title = clean_filename(title)[:60]
                note_path = os.path.join(config.ARTICLES_DIR, f"{safe_title}.md")
                
                if os.path.exists(note_path):
                    print(f"  -> Exists: {safe_title}")
                    entry['status'] = f"[[{safe_title}]]"
                else:
                    summary = get_ai_summary(text, prompt_type="article")
                    if summary:
                        content = f"""---
url: {url}
date: {datetime.date.today()}
tags: [article, ai-summary]
status: read
---
# {title}

## AI Summary
{summary}

## Extracted Text
{text}
"""
                        with open(note_path, 'w') as f:
                            f.write(content)
                        print(f"  -> Saved: {safe_title}")
                        entry['status'] = f"[[{safe_title}]]"
                    else:
                        entry['status'] = "Error: AI Summary Failed"

        except Exception as e:
            print(f"  -> Failed: {e}")
            entry['status'] = f"Error: {str(e)[:50]}" # Truncate error

        # 4. Immediate Save (Persistence)
        # Reconstruct file content
        new_content = "".join(headers)
        # Ensure header supports 4 columns if it didn't before
        if "Status" not in headers[-2]:
            new_content = "# Aggregated URLs\n\n| Date | Source Note | URL | Status |\n| :--- | :--- | :--- | :--- |\n"
            
        for e in entries:
            new_content += f"| {e['date']} | {e['source']} | {e['url']} | {e['status']} |\n"
            
        with open(config.AGGREGATED_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)

# ... (Include digest_mode and review_mode from previous script here unchanged) ...
# For brevity, reusing the existing digest/review logic below

def digest_mode():
    print("--- Daily Digest Mode ---")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    daily_note_path = os.path.join(config.NOTES_DIR, f"{today_str}.md")
    
    summaries = ""
    if os.path.exists(config.ARTICLES_DIR):
        for filename in os.listdir(config.ARTICLES_DIR):
            if filename.endswith(".md"):
                path = os.path.join(config.ARTICLES_DIR, filename)
                try:
                    post = frontmatter.load(path)
                    if str(post.get('date')) == today_str:
                        summaries += f"\n\nSource: {post.get('url')}\n{post.content[:2000]}"
                except: continue

    if not summaries:
        print("No articles found for today.")
        return

    digest = get_ai_summary(summaries, model="gpt-4o", prompt_type="digest")
    
    with open(daily_note_path, 'a') as f:
        f.write(f"\n\n# AI Daily Digest\n{digest}\n")
    print(f"Digest appended to {daily_note_path}")

def review_mode():
    print("--- Weekly Review Mode ---")
    today = datetime.date.today()
    start_week = today - datetime.timedelta(days=7)
    fname = f"Week-Review-{start_week.strftime('%Y%m%d')}-{today.strftime('%Y%m%d')}.md"
    review_path = os.path.join(config.NOTES_DIR, fname)
    combined_text = ""
    
    if os.path.exists(config.ARTICLES_DIR):
        for filename in os.listdir(config.ARTICLES_DIR):
            if filename.endswith(".md"):
                path = os.path.join(config.ARTICLES_DIR, filename)
                try:
                    post = frontmatter.load(path)
                    p_date = post.get('date')
                    if isinstance(p_date, str):
                        p_date = datetime.datetime.strptime(p_date, "%Y-%m-%d").date()
                    if start_week <= p_date <= today:
                        combined_text += f"\n\nTitle: {filename}\nSummary: {post.content[:1500]}"
                except: continue

    if not combined_text:
        print("No articles found in range.")
        return

    review = get_ai_summary(combined_text, model="gpt-4o", prompt_type="review")
    with open(review_path, 'w') as f:
        f.write(f"# Weekly Review\n{review}")
    print(f"Review created: {review_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fetch", "digest", "review"], required=True)
    args = parser.parse_args()
    
    if args.mode == "fetch":
        fetch_mode()
    elif args.mode == "digest":
        digest_mode()
    elif args.mode == "review":
        review_mode()

