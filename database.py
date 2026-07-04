import pandas as pd
from database_manager import get_engine

engine = get_engine()

# Load CSVs
accounts = pd.read_csv("Data/account_analytics.csv")
leads = pd.read_csv("Data/CRM_Lead_Analytics_Cleaned.csv")
opportunities = pd.read_csv("Data/opportunity_cleaned.csv")

# Save as SQL tables
accounts.to_sql(
    "account_analytics",
    engine,
    if_exists="replace",
    index=False
)

leads.to_sql(
    "crm_leads",
    engine,
    if_exists="replace",
    index=False
)

opportunities.to_sql(
    "opportunity",
    engine,
    if_exists="replace",
    index=False
)

print("Database created successfully!")
