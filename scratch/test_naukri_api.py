import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'appid': '109',
    'systemid': '109',
    'Accept': 'application/json',
}

job_id = "300126005361"

urls = [
    f"https://www.naukri.com/jobapi/v3/job/{job_id}",
    f"https://www.naukri.com/jobapi/v3/job?jobId={job_id}",
    f"https://www.naukri.com/jobapi/v3/jobDetails/{job_id}",
    f"https://www.naukri.com/jobapi/v3/job-details?jobId={job_id}",
]

for url in urls:
    print(f"\nTesting API URL: {url}")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"  Status code: {res.status_code}")
        print(f"  Content length: {len(res.content)} bytes")
        if res.status_code == 200:
            print("  [SUCCESS] Sample response:")
            print(res.text[:1000])
            # Save to file
            with open("scratch/naukri_api_success.json", "w", encoding="utf-8") as f:
                f.write(res.text)
            break
        else:
            print(f"  Failed. Sample: {res.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")
