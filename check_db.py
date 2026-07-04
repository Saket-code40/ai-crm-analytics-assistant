from database_manager import get_connection

conn = get_connection()

cursor = conn.cursor()

cursor.execute(
    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE();"
)

print(cursor.fetchall())

conn.close()
