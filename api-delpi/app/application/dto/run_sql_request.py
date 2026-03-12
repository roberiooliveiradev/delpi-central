# app/application/dto/run_sql_request.py
from dataclasses import dataclass


@dataclass
class RunSqlRequest:
    sql: str