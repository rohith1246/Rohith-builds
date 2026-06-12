import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

url = "https://www.naukri.com/job-listings-python-programming-language-backend-accnture-cloudxtreme-hyderabad-bengaluru-2-to-5-years-300126005361"

try:
    res = requests.get(url, headers=headers, timeout=10)
    with open("scratch/naukri_sample.txt", "w", encoding="utf-8") as f:
        f.write(f"Status Code: {res.status_code}\n\n")
        f.write(res.text[:2000])
    print("Done")
except Exception as e:
    print(f"Error: {e}")
