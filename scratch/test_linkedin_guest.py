import requests
from bs4 import BeautifulSoup
import re

def test_linkedin():
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python+developer&location=India&f_TPR=r604800&start=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        print(f"Requesting search: {url}...")
        res = requests.get(url, headers=headers, timeout=10)
        print(f"Search code: {res.status_code}")
        
        soup = BeautifulSoup(res.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/jobs/view/' in href:
                clean_url = href.split('?')[0].split('#')[0].strip()
                links.append(clean_url)
                
        print(f"Found {len(links)} links.")
        if not links:
            return
            
        test_url = links[0]
        # Modify to use jobs-guest / guest view if needed, or check if direct view works
        print(f"Requesting job page: {test_url}...")
        res_job = requests.get(test_url, headers=headers, timeout=10)
        print(f"Job page code: {res_job.status_code}")
        print(f"Job page length: {len(res_job.text)} bytes")
        
        soup_job = BeautifulSoup(res_job.text, 'html.parser')
        
        # Strip script/style
        for script in soup_job(["script", "style"]):
            script.decompose()
            
        title = soup_job.find('h1')
        title_text = title.get_text(strip=True) if title else "No Title Found"
        print(f"Found H1: {title_text}")
        
        # Look for description class on public job view
        # Common classes for public linkedin description: 'description__text', 'show-more-less-html__markup'
        desc = soup_job.find(class_=re.compile(r'description|show-more-less'))
        desc_text = desc.get_text(separator=' ', strip=True)[:500] if desc else "No description block found"
        print(f"Description sample: {desc_text}")
        
        # Let's print first 1000 characters of page text to see if descriptions are there
        all_text = soup_job.get_text(separator=' ')
        all_text_clean = re.sub(r'\s+', ' ', all_text).strip()
        print(f"All text sample: {all_text_clean[:1000]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_linkedin()
