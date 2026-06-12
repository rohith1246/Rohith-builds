import requests
from bs4 import BeautifulSoup

def test_indeed():
    url = "https://in.indeed.com/jobs?q=python&l=India"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    try:
        print(f"Requesting Indeed: {url}...")
        res = requests.get(url, headers=headers, timeout=10)
        print(f"Response code: {res.status_code}")
        print(f"Response length: {len(res.text)} bytes")
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            print("Page sample:")
            print(res.text[:1000])
        else:
            print("Failed to fetch. Sample response:")
            print(res.text[:1000])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_indeed()
