import os
import io
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
        "article": "Summarize this content. Include title, author/source, key facts, and methodology (if applicable). If it is a legal document/PDF, summarize the ruling or key filings. Format as Markdown.",
        "digest": "Synthesize these summaries into a 'Daily Intelligence Brief'. Focus on narrative flows and conflicting reports.",
        "review": "Write a 'Weekly Strategic Review' based on these summaries. Ignore noise; identify macro-trends."
    }
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompts[prompt_type]},
                {"role": "user", "content": text[:25000]} # Increase limit for long PDFs
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None

def fetch_mode():
    print("--- Fetch Mode (Robust) ---")
    if not os.path.exists(config.AGGREGATED_FILE):
        print("Aggregated file not found.")
        return

    # Read URLs
    urls_to_process = []
    with open(config.AGGREGATED_FILE, 'r') as f:
        for line in f:
            if "|" in line and "http" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    urls_to_process.append(parts[3])

    # Process Limit
    for url in urls_to_process[:5]: 
        try:
            print(f"Processing: {url}")
            
            # Use new Smart Fetcher
            title, text = fetch_smart_content(url)
            
            if not text or len(text) < 100:
                print("  -> Content too short or inaccessible.")
                continue

            # Generate Safe Filename
            if not title or title == "PDF Document":
                # Fallback to URL-based name for unnamed PDFs
                title = url.split("/")[-1].replace(".pdf", "").replace(".html", "")
            
            safe_title = clean_filename(title)
            note_path = os.path.join(config.ARTICLES_DIR, f"{safe_title}.md")
            
            if os.path.exists(note_path):
                print(f"  -> Skipping (Exists): {safe_title}")
                continue

            summary = get_ai_summary(text, prompt_type="article")
            if not summary: continue

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
{text[:5000]}... [Truncated for Notes]
"""
            with open(note_path, 'w') as f:
                f.write(content)
            print(f"  -> Saved: {safe_title}")
            
        except Exception as e:
            print(f"  -> Failed {url}: {e}")

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
        f.write(f"\n\n# 🧠 AI Daily Digest\n{digest}\n")
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

