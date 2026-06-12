import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def search_aol_for_jobs():
    queries = [
        'site:naukri.com "job-listings" python india',
        'site:indeed.com "viewjob" python india'
    ]
    links = []
    for q in queries:
        url = f"https://search.aol.com/aol/search?q={urllib.parse.quote_plus(q)}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if 'naukri.com' in href or 'indeed.com' in href:
                        ru_match = re.search(r'/RU=([^/]+)/', href)
                        if ru_match:
                            actual_url = urllib.parse.unquote(ru_match.group(1))
                            links.append(actual_url)
                        else:
                            links.append(urllib.parse.unquote(href))
        except Exception as e:
            print(f"Error searching AOL for {q}: {e}")
    return list(set(links))

def test_fetch_detail(url):
    print(f"Testing detail fetch for: {url}")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"  Status code: {res.status_code}")
        print(f"  Content length: {len(res.content)} bytes")
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Look for description text length
            text = soup.get_text()
            print(f"  Cleaned text sample: {text[:200].strip()}")
        else:
            print(f"  Failed. Sample response: {res.text[:300]}")
    except Exception as e:
        print(f"  Error fetching: {e}")

if __name__ == "__main__":
    found_links = search_aol_for_jobs()
    print(f"Found {len(found_links)} links from AOL.")
    naukri_links = [l for l in found_links if 'naukri.com' in l]
    indeed_links = [l for l in found_links if 'indeed.com' in l]
    
    print("\n--- Testing Naukri Links ---")
    for link in naukri_links[:2]:
        test_fetch_detail(link)
        
    print("\n--- Testing Indeed Links ---")
    for link in indeed_links[:2]:
        test_fetch_detail(link)
