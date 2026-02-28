import requests
from dotenv import load_dotenv
import os

load_dotenv()

headers = {
    "Authorization": f"token {os.getenv('ERP_KEY')}:{os.getenv('ERP_SECRET')}",
    "Accept": "application/json"
}

# Get all employees (not just 20)
response = requests.get(
    f"{os.getenv('ERP_URL')}/api/resource/Employee"
    f"?fields=[\"name\",\"employee_name\"]&limit=200",
    headers=headers
)

print(f"{'ERP ID':<10} {'Employee Name'}")
print("-" * 40)
for emp in response.json()['data']:
    print(f"{emp['name']:<10} {emp['employee_name']}")