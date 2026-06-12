import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

def test_aol():
    queries = [
        'site:naukri.com python developer',
        'site:in.indeed.com/viewjob python'
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    for q in queries:
        url = f"https://search.aol.com/aol/search?q={urllib.parse.quote_plus(q)}"
        try:
            print(f"Requesting AOL Search with query: {q}...")
            res = requests.get(url, headers=headers, timeout=10)
            print(f"Response code: {res.status_code}")
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    decoded = urllib.parse.unquote(href)
                    if 'naukri.com' in decoded or 'indeed.com' in decoded:
                        ru_match = re.search(r'/RU=([^/]+)/', href)
                        if ru_match:
                            actual_url = urllib.parse.unquote(ru_match.group(1))
                            links.append(actual_url)
                        else:
                            links.append(decoded)
                print(f"Found {len(links)} candidate links:")
                for l in list(set(links))[:5]:
                    print(f"  - {l}")
            else:
                print(f"Response sample: {res.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_aol()
