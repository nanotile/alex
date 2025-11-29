#!/usr/bin/env python3
"""Test the API job status endpoint directly"""

import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)

API_URL = os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')

# The most recent job ID from the database
job_id = "6f6f8baf-748f-4125-a966-d9580cac7377"

print(f"Testing API endpoint: {API_URL}/api/jobs/{job_id}")
print("=" * 80)

try:
    response = requests.get(f"{API_URL}/api/jobs/{job_id}")
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(response.text)

    if response.ok:
        data = response.json()
        print(f"\nParsed JSON:")
        print(f"  Job ID: {data.get('id')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Created: {data.get('created_at')}")
        print(f"  Completed: {data.get('completed_at')}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
