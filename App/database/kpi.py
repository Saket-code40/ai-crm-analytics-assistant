import sqlite3
import pandas as pd


def get_kpis():

    conn = sqlite3.connect("crm.db")

    kpis = {}

    # -------------------------
    # Accounts
    # -------------------------

    kpis["accounts"] = pd.read_sql(
        "SELECT COUNT(*) AS total FROM account_analytics",
        conn
    ).iloc[0, 0]

    # -------------------------
    # Leads
    # -------------------------

    kpis["leads"] = pd.read_sql(
        "SELECT COUNT(*) AS total FROM lead_analytics",
        conn
    ).iloc[0, 0]

    # -------------------------
    # Opportunities
    # -------------------------

    kpis["opportunities"] = pd.read_sql(
        "SELECT COUNT(*) AS total FROM opportunity_analytics",
        conn
    ).iloc[0, 0]

    # -------------------------
    # Active Accounts
    # -------------------------

    kpis["active"] = pd.read_sql(
        """
        SELECT COUNT(*)
        FROM account_analytics
        WHERE account_status='Active'
        """,
        conn
    ).iloc[0, 0]

    # -------------------------
    # Inactive Accounts
    # -------------------------

    kpis["inactive"] = pd.read_sql(
        """
        SELECT COUNT(*)
        FROM account_analytics
        WHERE account_status='Inactive'
        """,
        conn
    ).iloc[0, 0]

    # -------------------------
    # Converted Leads
    # -------------------------

    kpis["converted"] = pd.read_sql(
        """
        SELECT COUNT(*)
        FROM lead_analytics
        WHERE conversion_status='Converted'
        """,
        conn
    ).iloc[0, 0]

    # -------------------------
    # Revenue
    # -------------------------

    kpis["revenue"] = pd.read_sql(
        """
        SELECT SUM(amount)
        FROM opportunity_analytics
        """,
        conn
    ).iloc[0, 0]

    # -------------------------
    # Average Deal Size
    # -------------------------

    kpis["avg_deal"] = pd.read_sql(
        """
        SELECT AVG(amount)
        FROM opportunity_analytics
        """,
        conn
    ).iloc[0, 0]

    conn.close()

    return kpis