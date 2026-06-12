import requests

def test_searx():
    # Public Searx instance JSON API
    url = "https://searx.be/search"
    params = {
        'q': 'site:naukri.com OR site:indeed.com "python" "india" junior',
        'format': 'json',
        'pageno': '1'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        print(f"Requesting Searx API: {url}...")
        res = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Response code: {res.status_code}")
        print(f"Response length: {len(res.text)} bytes")
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            print(f"Found {len(results)} search results:")
            for r in results[:10]:
                title = r.get("title")
                link = r.get("url")
                print(f"  - Title: {title}\n    URL: {link}")
        else:
            print(f"Response sample: {res.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_searx()
