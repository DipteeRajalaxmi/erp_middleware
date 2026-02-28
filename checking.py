import requests
import urllib3
from dotenv import load_dotenv
import os

urllib3.disable_warnings()
load_dotenv()

ERP_URL    = os.getenv("ERP_URL")
ERP_KEY    = os.getenv("ERP_KEY")
ERP_SECRET = os.getenv("ERP_SECRET")

headers = {
    "Authorization": f"token {ERP_KEY}:{ERP_SECRET}",
    "Accept": "application/json"
}

# Step 1 — Get one existing Employee Checkin record to see exact fields
response = requests.get(
    f"{ERP_URL}/api/resource/Employee Checkin?limit=1&fields=[\"*\"]",
    headers=headers,
    verify=False
)

data = response.json()
print("STATUS:", response.status_code)
print("\nExisting Employee Checkin record:")
if data.get('data'):
    for key, val in data['data'][0].items():
        print(f"  {key}: {val}")
else:
    print("No records found")
    print(data)