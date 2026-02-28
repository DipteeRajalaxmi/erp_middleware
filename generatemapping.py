import pyodbc
import csv
from dotenv import load_dotenv
import os

load_dotenv()

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('SQL_SERVER')},1433;"
    f"DATABASE={os.getenv('SQL_DB')};"
    f"UID={os.getenv('SQL_USER')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
)

cursor = conn.cursor()

# EmployeeCode = eSSL biometric code (e.g. 1037)
# LoginName    = ERPNext Employee ID (e.g. E1001)
cursor.execute("""
    SELECT EmployeeCode, EmployeeName, LoginName
    FROM Employees
    WHERE LoginName IS NOT NULL
    AND LoginName != ''
    AND LoginName LIKE 'E%'
    ORDER BY EmployeeCode
""")

rows = cursor.fetchall()

with open("mapping.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["essl_code", "erp_employee"])
    for row in rows:
        essl_code    = str(row[0]).strip()
        erp_employee = str(row[2]).strip()
        writer.writerow([essl_code, erp_employee])

print(f"✔ mapping.csv generated with {len(rows)} employees\n")
print(f"{'eSSL Code':<12} {'ERPNext ID':<12} {'Name'}")
print("-" * 45)
for row in rows:
    print(f"{str(row[0]).strip():<12} {str(row[2]).strip():<12} {row[1]}")

conn.close()