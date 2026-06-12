import sys
import os
from flask import json
import time

# Add admin_dashboard directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard"))

# Make sure .env is loaded in context
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard", ".env"))

# Import admin app
from app import app

def test_jobs_scraper():
    print("Initializing admin test client...")
    client = app.test_client()

    # Log in the admin
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_username'] = 'rohith'

    # 1. Check Initial Scraper Status
    print("Testing GET /jobs/scraper/status...")
    response = client.get('/jobs/scraper/status')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    status_data = json.loads(response.data.decode('utf-8'))
    print(f"Initial status: {status_data}")
    assert status_data["status"] == "Idle", f"Expected 'Idle', got {status_data['status']}"
    assert "logs" in status_data, "logs field missing"
    assert "links_found" in status_data, "links_found field missing"

    # 2. Trigger Scraper Start
    print("Testing POST /jobs/scraper/start...")
    response = client.post('/jobs/scraper/start', content_type='application/json')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    start_data = json.loads(response.data.decode('utf-8'))
    assert start_data.get("success") is True, f"Failed to start: {start_data.get('error')}"
    print("[SUCCESS] Scraper thread launched.")

    # 3. Poll status during execution
    print("Polling status for 3 seconds...")
    for i in range(3):
        time.sleep(1)
        response = client.get('/jobs/scraper/status')
        status_data = json.loads(response.data.decode('utf-8'))
        print(f"Poll #{i+1} status: {status_data['status']} | Action: {status_data['current_action']}")
        log_text = "\n".join(status_data['logs'][-3:])
        try:
            print(f"Logs:\n{log_text}")
        except UnicodeEncodeError:
            print(f"Logs:\n{log_text.encode('ascii', errors='replace').decode('ascii')}")

    # 4. Trigger Scraper Stop
    print("Testing POST /jobs/scraper/stop...")
    response = client.post('/jobs/scraper/stop', content_type='application/json')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    stop_data = json.loads(response.data.decode('utf-8'))
    assert stop_data.get("success") is True, "Failed to stop scraper"
    
    # Check status again to verify stop logs
    time.sleep(1)
    response = client.get('/jobs/scraper/status')
    status_data = json.loads(response.data.decode('utf-8'))
    print(f"Status after stop request: {status_data['status']}")
    
    stop_logs = "\n".join(status_data['logs'][-3:])
    try:
        print(f"Latest logs after stop:\n{stop_logs}")
    except UnicodeEncodeError:
        print(f"Latest logs after stop:\n{stop_logs.encode('ascii', errors='replace').decode('ascii')}")
    
    try:
        print("[SUCCESS] Scraper API endpoints tested successfully!")
    except UnicodeEncodeError:
        print("[SUCCESS] Scraper API endpoints tested successfully!".encode('ascii', errors='replace').decode('ascii'))


if __name__ == "__main__":
    test_jobs_scraper()
