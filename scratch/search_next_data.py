import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

url = "https://www.naukri.com/job-listings-python-programming-language-backend-accnture-cloudxtreme-hyderabad-bengaluru-2-to-5-years-300126005361"

try:
    res = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {res.status_code}")
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Check for __NEXT_DATA__
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        print("Found __NEXT_DATA__!")
        # Print a small part of it
        data_text = next_data.string
        print(f"Length of Next Data: {len(data_text)}")
        parsed = json.loads(data_text)
        # Save to file to inspect
        with open("scratch/naukri_next_data.json", "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)
        print("Saved __NEXT_DATA__ to scratch/naukri_next_data.json")
    else:
        print("No __NEXT_DATA__ found.")
        
    # Check all scripts
    for idx, s in enumerate(soup.find_all('script')):
        if s.string and 'jobDetails' in s.string:
            print(f"Script #{idx} contains 'jobDetails' (length {len(s.string)})")
            
except Exception as e:
    print(f"Error: {e}")
