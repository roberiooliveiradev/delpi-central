# app/infrastructure/providers/totvs/database.py
import pyodbc
from app.config import settings

def get_connection():
    connection = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.DB_HOST},{settings.DB_PORT};"
        f"DATABASE={settings.DB_DATABASE};"
        f"UID={settings.DB_USER};"
        f"PWD={settings.DB_PASSWORD};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    return connection