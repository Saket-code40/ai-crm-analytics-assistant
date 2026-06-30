import sqlite3
import pandas as pd

conn = sqlite3.connect("crm.db")

query = """
SELECT COUNT(*)
FROM account_analytics
"""

df = pd.read_sql(query, conn)

print(df)

conn.close()