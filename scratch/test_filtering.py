import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def test_queries():
    queries = [
        'site:naukri.com "job-listings" "python"',
        'site:naukri.com/job-listings python',
        'site:in.indeed.com/viewjob python',
        'site:indeed.com/viewjob python',
        'site:naukri.com python entry level',
        'site:in.indeed.com python developer'
    ]
    
    for q in queries:
        url = f"https://search.aol.com/aol/search?q={urllib.parse.quote_plus(q)}"
        print(f"\nQUERY: {q}")
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                links = set()
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    decoded = urllib.parse.unquote(href)
                    if 'naukri.com' in decoded or 'indeed.com' in decoded:
                        ru_match = re.search(r'/RU=([^/]+)/', href)
                        if ru_match:
                            actual_url = urllib.parse.unquote(ru_match.group(1))
                        else:
                            actual_url = decoded
                        
                        # Clean/trim actual_url
                        actual_url = actual_url.split("?")[0].split("#")[0].strip()
                        
                        # Check if it's a real job page
                        is_naukri_job = 'naukri.com/job-listings-' in actual_url
                        is_indeed_job = 'indeed.com/viewjob' in actual_url or 'indeed.com/rc/clk' in actual_url
                        
                        if is_naukri_job or is_indeed_job:
                            links.add(actual_url)
                
                print(f"Found {len(links)} actual job links:")
                for l in sorted(list(links)):
                    print(f"  - {l}")
            else:
                print(f"Failed with code {res.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_queries()
