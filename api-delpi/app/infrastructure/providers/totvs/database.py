# app/infrastructure/providers/totvs/database.py
import os

import pyodbc
from app.config import settings

TOTVS_CONNECT_TIMEOUT = int(os.getenv("TOTVS_CONNECT_TIMEOUT", "10"))
TOTVS_QUERY_TIMEOUT = int(os.getenv("TOTVS_QUERY_TIMEOUT", "120"))


def get_connection():
    connection = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.DB_HOST},{settings.DB_PORT};"
        f"DATABASE={settings.DB_DATABASE};"
        f"UID={settings.DB_USER};"
        f"PWD={settings.DB_PASSWORD};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;",
        timeout=TOTVS_CONNECT_TIMEOUT,
    )
    connection.timeout = TOTVS_QUERY_TIMEOUT
    return connection