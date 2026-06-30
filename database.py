import sqlite3
import pandas as pd

conn = sqlite3.connect("crm.db")

# Load CSVs
accounts = pd.read_csv("Data/account_analytics.csv")
leads = pd.read_csv("Data/CRM_Lead_Analytics_Cleaned.csv")
opportunities = pd.read_csv("Data/opportunity_cleaned.csv")

# Save as SQL tables
accounts.to_sql(
    "account_analytics",
    conn,
    if_exists="replace",
    index=False
)

leads.to_sql(
    "lead_analytics",
    conn,
    if_exists="replace",
    index=False
)

opportunities.to_sql(
    "opportunity_analytics",
    conn,
    if_exists="replace",
    index=False
)

conn.commit()

print("Database created successfully!")

conn.close()