"""
database_manager.py — Centralized MySQL database connection manager.

Provides a reusable SQLAlchemy engine and raw DB-API connections
for the AI CRM Analytics Assistant.

All credentials are read from environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Usage:
    from database_manager import get_engine, get_connection, verify_connection
"""

import os
import warnings
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Suppress pandas UserWarning about raw DBAPI2 connections.
# get_connection() intentionally returns a raw PyMySQL connection so it is a
# drop-in replacement for sqlite3.connect() (supports .cursor(), .execute(),
# .close()). PyMySQL connections are fully functional with pandas.read_sql().
# ---------------------------------------------------------------------------
warnings.filterwarnings(
    "ignore",
    message="pandas only supports SQLAlchemy connectable.*",
    category=UserWarning,
)

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "cleaned_files")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ---------------------------------------------------------------------------
# SQLAlchemy engine (singleton pattern — created once per process)
# ---------------------------------------------------------------------------

_engine = None


def get_engine():
    """
    Return the SQLAlchemy engine for the MySQL database.

    The engine is created lazily on first call and reused afterwards.

    Returns:
        sqlalchemy.engine.Engine
    """
    global _engine

    if _engine is None:
        # URL-encode password to handle special characters (e.g. @, #, %)
        encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
        connection_url = (
            f"mysql+pymysql://{DB_USER}:{encoded_password}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        _engine = create_engine(connection_url, pool_pre_ping=True)

    return _engine


def get_connection():
    """
    Return a raw DB-API (PyMySQL) connection.

    This is a drop-in replacement for sqlite3.connect(...).
    Callers must close the connection when done.

    Returns:
        A PyMySQL connection object compatible with pd.read_sql().
    """
    engine = get_engine()
    return engine.raw_connection()


def verify_connection():
    """
    Verify that the MySQL database connection is working.

    Attempts to connect and run a lightweight query.
    Returns True on success, raises an exception on failure.

    Returns:
        bool: True if connection is successful

    Raises:
        Exception: If connection or query execution fails
    """
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        result.fetchone()

    return True


if __name__ == "__main__":
    try:
        if verify_connection():
            print("✅ MySQL connection successful!")
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
