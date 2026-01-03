import requests
import base64
import os

BASE_URL = "http://localhost:8000"

def test_report_image():
    # 1. Create a dummy base64 image (small red dot)
    # This is a valid 1x1 pixel PNG
    base64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    payload = {
        "title": "Test Report With Image",
        "description": "This is a test report to verify image upload.",
        "location": "Test Location",
        "tags": ["Test"],
        "image": base64_img,
        "user_id": 1 # Assuming User 1 exists
    }
    
    print("Creating report with image...")
    try:
        response = requests.post(f"{BASE_URL}/api/reports", json=payload)
        print(f"Create Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to create report: {response.text}")
            return

        report_id = response.json().get("id")
        print(f"Report Created. ID: {report_id}")

        # 2. Fetch reports and verify image_path
        print("Fetching reports...")
        response = requests.get(f"{BASE_URL}/api/reports")
        reports = response.json()
        
        target_report = next((r for r in reports if r["id"] == report_id), None)
        
        if target_report:
            print(f"Found Report. Image Path: {target_report.get('image_path')}")
            if target_report.get('image_path'):
                print("SUCCESS: Image path is present.")
            else:
                print("FAILURE: Image path is missing.")
        else:
            print("FAILURE: Could not find the created report.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_report_image()
