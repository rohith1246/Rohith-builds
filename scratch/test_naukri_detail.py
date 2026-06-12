import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

url = "https://www.naukri.com/job-listings-python-programming-language-backend-accnture-cloudxtreme-hyderabad-bengaluru-2-to-5-years-300126005361"

try:
    print(f"Requesting Naukri Job Page: {url}...")
    res = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Response content length: {len(res.content)} bytes")
    
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        # Let's clean script/styles and print text
        for s in soup(["script", "style"]):
            s.decompose()
        text = soup.get_text()
        print("Cleaned text (first 500 chars):")
        print(text[:500].strip())
    else:
        print("Sample response:")
        print(res.text[:500])
except Exception as e:
    print(f"Error: {e}")
