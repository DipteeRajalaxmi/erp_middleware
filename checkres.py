import pyodbc
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
cursor.execute("SELECT DISTINCT EmployeeCode FROM AttenInfo ORDER BY EmployeeCode")

print("eSSL Codes:")
for row in cursor.fetchall():
    print(row[0])