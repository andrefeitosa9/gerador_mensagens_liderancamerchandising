"""Módulo para conexão e execução de queries no SQL Server."""

from __future__ import annotations

from datetime import date

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
            print("OK: Conectado ao banco de dados")
            return True
        except Exception as e:
            print(f"ERRO: Falha ao conectar ao banco: {e}")
            return False

    def disconnect(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            print("OK: Conexao fechada")

    def query_rows(self, sql: str) -> list[dict]:
        if self.conn is None:
            ok = self.connect()
            if not ok:
                raise RuntimeError("Não foi possível conectar ao banco")

        cur = self.conn.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall()
        result: list[dict] = []
        for r in rows:
            result.append({cols[i]: r[i] for i in range(len(cols))})
        return result


def sql_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")
