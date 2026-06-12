import requests
import json
import re

def test_hn():
    domains = ["lever.co", "greenhouse.io"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    for dom in domains:
        # Search by date for the most recent comments containing the domain
        url = f"https://hn.algolia.com/api/v1/search_by_date?query={dom}&tags=comment&numericFilters=created_at_i%3E{int(time.time() - 30*24*60*60) if 'time' in globals() else 1770000000}"
        # Let's simplify url
        url = f"https://hn.algolia.com/api/v1/search_by_date?query={dom}&tags=comment&hitsPerPage=20"
        try:
            print(f"Requesting HN Algolia API for '{dom}'...")
            res = requests.get(url, headers=headers, timeout=10)
            print(f"Response code: {res.status_code}")
            data = res.json()
            hits = data.get("hits", [])
            print(f"Found {len(hits)} comments.")
            
            links = set()
            for h in hits:
                text = h.get("comment_text", "")
                # find URLs matching lever.co or greenhouse.io
                found = re.findall(r'https?://[^\s<"\']*(?:' + dom + r')[^\s<"\']*', text)
                for f in found:
                    clean = f.split("?")[0].split("#")[0].strip()
                    clean = re.sub(r'[.,;:)\]\s]+$', '', clean)
                    links.add(clean)
            
            print(f"Extracted {len(links)} unique links:")
            for l in list(links)[:5]:
                print(f"  - {l}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_hn()
