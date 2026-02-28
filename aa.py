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
cursor.execute("SELECT TOP 3 * FROM AttenInfo")

columns = [col[0] for col in cursor.description]
print("COLUMNS:", columns)

for row in cursor.fetchall():
    print("ROW:", row)