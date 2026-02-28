import pymssql
import requests
import os
import json
import urllib3
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# ================================================================
#  CONFIGURATION
# ================================================================
SQL_SERVER   = os.getenv("SQL_SERVER")
SQL_DB       = os.getenv("SQL_DB")
SQL_USER     = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

ERP_URL      = os.getenv("ERP_URL")
ERP_KEY      = os.getenv("ERP_KEY")
ERP_SECRET   = os.getenv("ERP_SECRET")

SYNC_INTERVAL  = int(os.getenv("SYNC_INTERVAL", 2))
LAST_SYNC_FILE = "last_sync.txt"

# Dummy coordinates — satisfies ERPNext geo validation
DUMMY_LAT  = 23.1853548
DUMMY_LNG  = 77.458905
DUMMY_GEO  = json.dumps({
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Point",
            "coordinates": [DUMMY_LNG, DUMMY_LAT]
        }
    }]
})

# ================================================================
#  AUTO MAPPING: eSSL 1001 -> ERPNext E1001
# ================================================================
def get_erp_employee(essl_code):
    return f"E{essl_code}"

# ================================================================
#  LAST SYNC TIME
# ================================================================
def get_last_sync_time():
    if not os.path.exists(LAST_SYNC_FILE):
        return "2000-01-01 00:00:00"
    with open(LAST_SYNC_FILE, "r") as f:
        value = f.read().strip()
        return value if value else "2000-01-01 00:00:00"

def update_last_sync_time(sync_time):
    with open(LAST_SYNC_FILE, "w") as f:
        f.write(sync_time)

# ================================================================
#  SQL CONNECTION  (pymssql — works on Render without any drivers)
# ================================================================
def connect_sql():
    return pymssql.connect(
        server=SQL_SERVER,
        user=SQL_USER,
        password=SQL_PASSWORD,
        database=SQL_DB,
        port=1433,
        login_timeout=10
    )

# ================================================================
#  PUSH TO ERPNext
# ================================================================
def push_to_erpnext(erp_employee, punch_time, log_type):
    headers = {
        "Authorization": f"token {ERP_KEY}:{ERP_SECRET}",
        "Content-Type": "application/json"
    }
    payload = {
        "doctype": "Employee Checkin",
        "employee": erp_employee,
        "time": punch_time.strftime("%Y-%m-%d %H:%M:%S"),
        "log_type": log_type,
        "device_id": "eSSL-Biometric",
        "skip_auto_attendance": 0,
        "latitude": DUMMY_LAT,
        "longitude": DUMMY_LNG,
        "geolocation": DUMMY_GEO
    }
    try:
        response = requests.post(
            f"{ERP_URL}/api/resource/Employee Checkin",
            headers=headers,
            json=payload,
            timeout=15,
            verify=False
        )
        if response.status_code in (200, 201):
            return True, None
        if response.status_code == 409:
            return True, "duplicate"
        # ERPNext returns 500 for duplicate timestamp instead of 409
        if "already has a log with the same timestamp" in response.text:
            return True, "duplicate"
        return False, response.text[:200]
    except Exception as e:
        return False, str(e)

# ================================================================
#  MAIN SYNC
# ================================================================
def sync_attendance():
    print(f"\n{'='*52}")
    print(f"  Sync Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*52}")

    last_sync = get_last_sync_time()
    print(f"  Last Sync    : {last_sync}")

    try:
        conn = connect_sql()
        print(f"  SQL Server   : Connected")
    except Exception as e:
        print(f"  SQL Server   : FAILED - {e}")
        return

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT EmployeeCode, LogDateTime, Direction
        FROM AttenInfo
        WHERE LogDateTime > %s
        ORDER BY LogDateTime ASC
        """,
        (last_sync,)
    )

    latest_time = last_sync
    synced  = 0
    failed  = 0
    dupes   = 0

    rows = cursor.fetchmany(100)
    while rows:
        for row in rows:
            essl_code    = str(row[0]).strip()
            punch_time   = row[1]
            direction    = str(row[2]).strip().lower()
            log_type     = "IN" if direction == "in" else "OUT"
            erp_employee = get_erp_employee(essl_code)

            success, reason = push_to_erpnext(erp_employee, punch_time, log_type)

            if success and reason == "duplicate":
                print(f"  Skip   : {essl_code} -> {erp_employee} | {punch_time} | duplicate")
                latest_time = punch_time.strftime("%Y-%m-%d %H:%M:%S")
                dupes += 1
            elif success:
                print(f"  Synced : {essl_code} -> {erp_employee} | {punch_time} | {log_type}")
                latest_time = punch_time.strftime("%Y-%m-%d %H:%M:%S")
                synced += 1
            else:
                print(f"  Failed : {essl_code} -> {erp_employee} | {punch_time} | {reason}")
                failed += 1

        update_last_sync_time(latest_time)
        rows = cursor.fetchmany(100)

    cursor.close()
    conn.close()

    print(f"\n  Synced: {synced} | Skipped: {dupes} | Failed: {failed}")
    print(f"  Next run in {SYNC_INTERVAL} min")
    print(f"{'='*52}\n")

# ================================================================
#  SCHEDULER
# ================================================================
scheduler = BlockingScheduler()
scheduler.add_job(sync_attendance, 'interval', minutes=SYNC_INTERVAL)

print(f"\nMiddleware Started (syncing every {SYNC_INTERVAL} minutes)\n")
sync_attendance()
scheduler.start()