import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_mojeek_jobs():
    queries = [
        'site:naukri.com/job-listings "python" "india"',
        'site:in.indeed.com/viewjob "python"'
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    for q in queries:
        url = f"https://www.mojeek.com/search?q={urllib.parse.quote_plus(q)}"
        try:
            print(f"Requesting Mojeek with query: {q}...")
            res = requests.get(url, headers=headers, timeout=10)
            print(f"Response code: {res.status_code}")
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                links = []
                for a in soup.find_all('a', class_='ob'):
                    href = a['href']
                    links.append(href)
                print(f"Found {len(links)} links:")
                for l in links[:10]:
                    print(f"  - {l}")
            else:
                print(f"Failed to fetch. Sample response: {res.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_mojeek_jobs()
