import pandas as pd
from database_manager import get_connection

conn = get_connection()

query = """
SELECT COUNT(*)
FROM account_analytics
"""

df = pd.read_sql(query, conn)

print(df)

conn.close()
