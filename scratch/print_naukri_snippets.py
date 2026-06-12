import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def check_naukri_snippets():
    query = 'site:naukri.com "job-listings" "python"'
    url = f"https://search.aol.com/aol/search?q={urllib.parse.quote_plus(query)}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for li in soup.find_all(['li', 'div'], class_=re.compile(r'algo|compListing|dd')):
                title_el = li.find('h3')
                link_el = li.find('a', href=True)
                snippet_el = li.find(['span', 'div', 'p'], class_=re.compile(r'compText|desc|snippet|abstr'))
                
                if title_el and link_el:
                    title = title_el.get_text().strip()
                    href = link_el['href']
                    ru_match = re.search(r'/RU=([^/]+)/', href)
                    actual_url = urllib.parse.unquote(ru_match.group(1)) if ru_match else urllib.parse.unquote(href)
                    snippet = snippet_el.get_text().strip() if snippet_el else ""
                    
                    if 'naukri.com/job-listings-' in actual_url:
                        print(f"\nTitle: {title}")
                        print(f"URL: {actual_url}")
                        print(f"Snippet: {snippet}")
        else:
            print(f"Failed to fetch AOL: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_naukri_snippets()
