import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "crm.db"


def get_schema():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = ""

    # Get all tables
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name;
    """)

    tables = cursor.fetchall()

    for table in tables:

        table_name = table[0]

        schema += "\n"
        schema += "=" * 80 + "\n"
        schema += f"TABLE : {table_name}\n"
        schema += "=" * 80 + "\n"

        # -----------------------------
        # Row Count
        # -----------------------------

        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        row_count = cursor.fetchone()[0]

        schema += f"Rows : {row_count}\n\n"

        # -----------------------------
        # Columns
        # -----------------------------

        cursor.execute(f'PRAGMA table_info("{table_name}")')
        columns = cursor.fetchall()

        for col in columns:

            column = col[1]
            datatype = col[2].upper()

            schema += "-" * 50 + "\n"
            schema += f"Column : {column}\n"
            schema += f"Type   : {datatype}\n"

            try:

                # --------------------------------
                # Numeric Columns
                # --------------------------------

                if any(x in datatype for x in ["INT", "REAL", "NUM", "FLOAT", "DOUBLE"]):

                    cursor.execute(f'''
                        SELECT
                            MIN("{column}"),
                            MAX("{column}"),
                            AVG("{column}")
                        FROM "{table_name}"
                        WHERE "{column}" IS NOT NULL
                    ''')

                    minimum, maximum, average = cursor.fetchone()

                    schema += f"Minimum : {minimum}\n"
                    schema += f"Maximum : {maximum}\n"

                    if average is not None:
                        schema += f"Average : {round(average,2)}\n"

                # --------------------------------
                # Date Columns
                # --------------------------------

                elif (
                    "DATE" in column.upper()
                    or "DATE" in datatype
                    or "TIME" in column.upper()
                ):

                    cursor.execute(f'''
                        SELECT
                            MIN("{column}"),
                            MAX("{column}")
                        FROM "{table_name}"
                        WHERE "{column}" IS NOT NULL
                    ''')

                    earliest, latest = cursor.fetchone()

                    schema += f"Earliest : {earliest}\n"
                    schema += f"Latest   : {latest}\n"

                # --------------------------------
                # Text Columns
                # --------------------------------

                else:

                    cursor.execute(f'''
                        SELECT COUNT(DISTINCT "{column}")
                        FROM "{table_name}"
                    ''')

                    distinct = cursor.fetchone()[0]

                    schema += f"Distinct Values : {distinct}\n"

                    # Show actual values only if cardinality is small
                    if distinct <= 20:

                        cursor.execute(f'''
                            SELECT DISTINCT "{column}"
                            FROM "{table_name}"
                            WHERE "{column}" IS NOT NULL
                            ORDER BY "{column}"
                            LIMIT 20
                        ''')

                        values = cursor.fetchall()

                        values = [
                            str(v[0])
                            for v in values
                            if str(v[0]).strip() != ""
                        ]

                        if values:

                            schema += "Possible Values:\n"

                            for value in values:
                                schema += f"   • {value}\n"

                    else:

                        cursor.execute(f'''
                            SELECT "{column}"
                            FROM "{table_name}"
                            WHERE "{column}" IS NOT NULL
                            LIMIT 5
                        ''')

                        samples = cursor.fetchall()

                        samples = [
                            str(v[0])
                            for v in samples
                        ]

                        schema += "Sample Values:\n"

                        for value in samples:
                            schema += f"   • {value}\n"

            except Exception:
                pass

            schema += "\n"

        schema += "\n"

    conn.close()

    return schema


if __name__ == "__main__":
    print(get_schema())