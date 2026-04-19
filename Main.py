import os
import sys
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- CONFIGURATION ---
# The API key is provided by the execution environment at runtime.
API_KEY = ""

def setup_gemini():
    """Initializes the Gemini AI model with exponential backoff configuration."""
    if not API_KEY:
        # In a local environment, you would use os.getenv("GOOGLE_API_KEY")
        # For this preview, we assume the environment handles the key.
        pass
    
    genai.configure(api_key=API_KEY)
    # Using the latest supported model for text generation
    return genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

def scrape_content(url):
    """
    Scrapes the main text content from a given URL.
    Focuses on paragraphs to avoid navigation menus and footers.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script or style in soup(["script", "style"]):
            script.decompose()

        # Extract text from paragraph tags
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs])
        
        # Basic cleanup
        content = " ".join(content.split())
        
        if len(content) < 100:
            raise ValueError("Insufficient content found at the URL.")
            
        return content[:10000]  # Limit content length for the prompt
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def generate_summary(content):
    """
    Uses Gemini AI to generate the executive summary, takeaways, and viral title.
    Includes exponential backoff for API reliability.
    """
    model = setup_gemini()
    
    prompt = f"""
    Analyze the following article content and provide:
    1. A "Click-bait" style Title for social media (Twitter/LinkedIn).
    2. A 3-sentence executive summary.
    3. 5 Key Takeaways as bullet points.

    Format the output clearly as:
    TITLE: [Title]
    SUMMARY: [Summary]
    TAKEAWAYS:
    - [Point 1]
    ...
    
    Article Content:
    {content}
    """
    
    # Simple retry logic for the API
    import time
    for i in range(5):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            wait_time = 2 ** i
            print(f"API busy, retrying in {wait_time}s...")
            time.sleep(wait_time)
            
    return "Failed to generate summary after multiple attempts."

def main():
    """Main entry point for the Smart-Link-Summarizer."""
    print("🚀 Smart-Link-Summarizer | AI-Powered Content Insights")
    print("-" * 50)
    
    target_url = input("Enter the URL to summarize: ").strip()
    
    if not target_url.startswith("http"):
        print("❌ Error: Please enter a valid URL (starting with http:// or https://)")
        return

    print(f"\n🔍 Scraping content from: {target_url}...")
    article_text = scrape_content(target_url)
    
    if article_text:
        print("🧠 Processing with Gemini AI...")
        result = generate_summary(article_text)
        print("\n" + "="*50)
        print(result)
        print("="*50)
        print("\n✅ Task Complete!")
    else:
        print("❌ Failed to retrieve content. Please check the URL and try again.")

if __name__ == "__main__":
    main()
