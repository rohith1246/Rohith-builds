import requests
import urllib.parse

def dump_aol():
    q = 'site:naukri.com "job-listings" python'
    url = f"https://search.aol.com/aol/search?q={urllib.parse.quote_plus(q)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"Code: {res.status_code}, Length: {len(res.text)} bytes")
        with open("scratch/aol_response.html", "w", encoding="utf-8") as f:
            f.write(res.text)
        print("Saved to scratch/aol_response.html")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_aol()
