import requests
import urllib.parse

def test_searx_rotation():
    instances = [
        "https://search.disclosure.gdn",
        "https://gruble.de",
        "https://searx.work",
        "https://searx.be",
        "https://searx.me"
    ]
    query = 'site:naukri.com/job-listings OR site:in.indeed.com/viewjob "python" "india"'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    links = []
    for inst in instances:
        url = f"{inst}/search"
        params = {
            'q': query,
            'format': 'json',
            'pageno': '1'
        }
        try:
            print(f"Trying Searx instance: {inst}...")
            res = requests.get(url, params=params, headers=headers, timeout=8)
            print(f"  Response: {res.status_code}")
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                print(f"  Found {len(results)} search results.")
                for r in results:
                    u = r.get("url")
                    if 'naukri.com' in u or 'indeed.com' in u:
                        links.append(u)
                if links:
                    print(f"[SUCCESS] Found links from {inst}!")
                    break
        except Exception as e:
            print(f"  Error with {inst}: {e}")
            
    print(f"Total links found: {len(links)}")
    for l in links[:5]:
        print(f"  - {l}")

if __name__ == "__main__":
    test_searx_rotation()
