import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def search_aol(query):
    url = f"https://search.aol.com/aol/search?q={urllib.parse.quote_plus(query)}"
    print(f"\nQUERY: {query}")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"Failed, status: {res.status_code}")
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Decode RU redirect
            ru_match = re.search(r'/RU=([^/]+)/', href)
            if ru_match:
                actual_url = urllib.parse.unquote(ru_match.group(1))
            else:
                actual_url = urllib.parse.unquote(href)
            
            # Keep query parameters for Indeed jk, but clean for Naukri
            if 'naukri.com/job-listings-' in actual_url:
                clean_url = actual_url.split("?")[0].split("#")[0].strip()
                links.append(clean_url)
            elif 'indeed.com/viewjob' in actual_url or 'indeed.com/rc/clk' in actual_url:
                clean_url = actual_url.split("#")[0].strip()
                links.append(clean_url)
                
        # Deduplicate
        unique_links = list(set(links))
        print(f"Found {len(unique_links)} job links:")
        for l in unique_links[:5]:
            print(f"  - {l}")
        return unique_links
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    search_aol('site:naukri.com "job-listings" "python"')
    search_aol('site:naukri.com "job-listings" "backend"')
    search_aol('site:indeed.com "viewjob" "python" "india"')
    search_aol('site:indeed.com "viewjob" "backend" "india"')
