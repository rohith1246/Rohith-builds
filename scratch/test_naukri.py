import requests
import json

def test_naukri():
    url = "https://www.naukri.com/jobapi/v3/search?noOfResults=20&urlType=searchForm&searchType=adv&keyword=python&location=India"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'appid': '109',
        'systemid': '109'
    }
    try:
        print(f"Requesting Naukri API: {url}...")
        res = requests.get(url, headers=headers, timeout=10)
        print(f"Response code: {res.status_code}")
        print(f"Response length: {len(res.text)} bytes")
        if res.status_code == 200:
            data = res.json()
            jobs = data.get("jobDetails", [])
            print(f"Found {len(jobs)} jobs:")
            for j in jobs[:5]:
                title = j.get("title")
                company = j.get("companyName")
                jd_url = j.get("jdURL")
                print(f"  - Title: {title}, Company: {company}, URL: {jd_url}")
        else:
            print(f"Response sample: {res.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_naukri()
