import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def analyze_aol_search(query):
    url = f"https://search.aol.com/aol/search?q={urllib.parse.quote_plus(query)}"
    print(f"\n================ QUERY: {query} ================")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"Failed to fetch: {res.status_code}")
            return
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # AOL search results are typically in list items with class containing 'algo'
        # Let's search all divs/list items that represent a search result
        results = []
        for li in soup.find_all(['li', 'div'], class_=re.compile(r'algo|compListing|dd')):
            title_el = li.find('h3')
            link_el = li.find('a', href=True)
            snippet_el = li.find(['span', 'div', 'p'], class_=re.compile(r'compText|desc|snippet|abstr'))
            
            if title_el and link_el:
                title = title_el.get_text().strip()
                href = link_el['href']
                
                # Decode RU redirect
                actual_url = href
                ru_match = re.search(r'/RU=([^/]+)/', href)
                if ru_match:
                    actual_url = urllib.parse.unquote(ru_match.group(1))
                else:
                    actual_url = urllib.parse.unquote(href)
                    
                snippet = snippet_el.get_text().strip() if snippet_el else ""
                
                # Filter to target domains
                if 'naukri.com' in actual_url.lower() or 'indeed.com' in actual_url.lower():
                    results.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet
                    })
        
        print(f"Found {len(results)} structured results:")
        for idx, r in enumerate(results[:5]):
            print(f"\nResult #{idx+1}:")
            print(f"  Title: {r['title']}")
            print(f"  URL: {r['url']}")
            print(f"  Snippet: {r['snippet']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_aol_search('site:naukri.com "job-listings" python india')
    analyze_aol_search('site:indeed.com "viewjob" python india')
