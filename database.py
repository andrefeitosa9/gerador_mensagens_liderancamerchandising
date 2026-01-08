"""Módulo para conexão e execução de queries no SQL Server."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pyodbc

from config import DB_CONFIG


class Database:
    def __init__(self) -> None:
        self.connection_string = (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        self.conn: pyodbc.Connection | None = None

    def connect(self) -> bool:
        try:
            self.conn = pyodbc.connect(self.connection_string)
            print("✓ Conectado ao banco de dados")
            return True
        except Exception as e:
            print(f"✗ Erro ao conectar ao banco: {e}")
            return False

    def disconnect(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            print("✓ Conexão fechada")

    def query_df(self, sql: str) -> pd.DataFrame:
        if self.conn is None:
            ok = self.connect()
            if not ok:
                raise RuntimeError("Não foi possível conectar ao banco")

        return pd.read_sql(sql, self.conn)


def sql_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")
