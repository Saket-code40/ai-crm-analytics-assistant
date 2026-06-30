import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "crm.db")

def get_connection():
    return sqlite3.connect(DB_PATH)