import sys
import os

# Add admin_dashboard directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard"))

# Make sure .env is loaded in context
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard", ".env"))

from app import app, fetch_job_links_from_search

def test_scraper_shuffle():
    print("Testing fetch_job_links_from_search() with shuffle...")
    
    with app.app_context():
        results = fetch_job_links_from_search()
        
    print(f"Total results fetched: {len(results)}")
    
    # Count sources
    sources = [r["source"] for r in results]
    linkedin_count = sources.count("linkedin")
    naukri_count = sources.count("naukri")
    indeed_count = sources.count("indeed")
    
    print(f"LinkedIn jobs: {linkedin_count}")
    print(f"Naukri jobs: {naukri_count}")
    print(f"Indeed jobs: {indeed_count}")
    
    print("\nFirst 15 job listings in queue:")
    for idx, r in enumerate(results[:15]):
        print(f"#{idx+1}: {r['source'].upper()} - {r['url']}")
        
    # Check if Naukri or Indeed listings appear in the first 15 listings
    mix_present = any(r["source"] in ["naukri", "indeed"] for r in results[:15])
    if mix_present:
        print("\n[SUCCESS] Indeed/Naukri listings are mixed in the first 15 links, showing logs will appear immediately!")
    else:
        print("\n[WARNING] No Indeed/Naukri in first 15 links (could be due to no results returned from search, check log outputs above).")

if __name__ == "__main__":
    test_scraper_shuffle()
