import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_ddg_lite():
    q = 'site:lever.co OR site:greenhouse.io "python" "india" junior'
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    data = {
        'q': q,
        'kl': 'in-en' # India English
    }
    try:
        print(f"Posting to {url} with query: {q}...")
        res = requests.post(url, headers=headers, data=data, timeout=10)
        print(f"Response code: {res.status_code}")
        print(f"Response length: {len(res.text)} bytes")
        
        soup = BeautifulSoup(res.text, 'html.parser')
        links = []
        for td in soup.find_all('td', class_='result-link'):
            a = td.find('a')
            if a and a.get('href'):
                links.append(a['href'])
                
        print(f"Found {len(links)} links:")
        for l in links[:10]:
            print(f"  - {l}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ddg_lite()
