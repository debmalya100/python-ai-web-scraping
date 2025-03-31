import requests
import spacy
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import re

# Load English language model for spaCy
nlp = spacy.load("en_core_web_sm")

def is_same_domain(base_url, check_url):
    return urlparse(base_url).netloc == urlparse(check_url).netloc

def is_news_article(url):
    """Check if URL looks like a news article path"""
    article_pattern = re.compile(r'/\d{8}$')  # Matches URLs ending with 8 digits (common in BBC news)
    return article_pattern.search(url) or '/news/' in url

def is_animal_related(text):
    """Improved animal content detection"""
    doc = nlp(text.lower())
    
    # Specific animal-related terms
    animal_terms = {
        'wildlife', 'species', 'mammal', 'bird', 'reptile', 'marine',
        'habitat', 'conservation', 'zoo', 'endangered', 'extinction',
        'elephant', 'tiger', 'whale', 'shark', 'ape', 'bear', 'wolf'
    }
    
    # Check for animal entities and keywords
    animal_entities = {ent.text.lower() for ent in doc.ents if ent.label_ in ['ANIMAL', 'ORG']}
    found_terms = {term for term in animal_terms if term in text}
    
    return len(animal_entities) >= 2 or len(found_terms) >= 3

def find_animal_news(base_url, max_pages=50):
    visited = set()
    queue = deque([base_url])
    results = []
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
    
    while queue and len(results) < max_pages:
        url = queue.popleft()
        
        if url in visited or not is_news_article(url):
            continue
            
        try:
            print(f"Crawling: {url}")
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            title = soup.title.string.strip() if soup.title else 'No Title'
            
            # Skip non-content pages
            if len(page_text) < 500:  # Minimum content length
                continue
                
            if is_animal_related(page_text):
                content = ' '.join(soup.get_text().split()[:500])
                results.append({
                    'page_name': title,
                    'url': url,
                    'content': content
                })
                
            # Find new links with better filtering
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                if (is_same_domain(base_url, absolute_url) 
                    and absolute_url not in visited
                    and is_news_article(absolute_url)):
                    queue.append(absolute_url)
            
            visited.add(url)
            time.sleep(1)  # Respectful delay
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            continue
            
    return results

if __name__ == "__main__":
    # Target specific BBC sections more likely to contain animal news
    target_urls = [
        "https://www.bbc.com/news/",
        "https://www.bbc.com/"
    ]
    
    animal_articles = []
    for url in target_urls:
        animal_articles.extend(find_animal_news(url, max_pages=20))
    
    print(f"\nFound {len(animal_articles)} animal-related articles:")
    for idx, article in enumerate(animal_articles, 1):
        print(f"\nArticle {idx}:")
        print(f"Title: {article['page_name']}")
        print(f"URL: {article['url']}")
        print(f"Content Preview: {article['content'][:200]}...")