from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "sugarmill.db"
SQL_DIR = Path(__file__).parent / "sql"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = connect()
    for script in sorted(SQL_DIR.glob("*.sql")):
        connection.executescript(script.read_text(encoding="utf-8"))
    connection.commit()
    connection.close()


def get_fields(status: str | None = None) -> list[dict[str, Any]]:
    connection = connect()
    if status:
        rows = connection.execute(
            "SELECT * FROM fields WHERE status = ? ORDER BY id", (status,)).fetchall()
    else:
        rows = connection.execute("SELECT * FROM fields ORDER BY id").fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_field(field_id: str) -> dict[str, Any]:
    connection = connect()
    row = connection.execute("SELECT * FROM fields WHERE id = ?", (field_id,)).fetchone()
    connection.close()
    if row is None:
        raise ValueError(f"field {field_id} not found")
    return dict(row)


def get_producer(producer_id: str) -> dict[str, Any]:
    connection = connect()
    row = connection.execute(
        "SELECT * FROM producers WHERE id = ?", (producer_id,)).fetchone()
    connection.close()
    if row is None:
        raise ValueError(f"producer {producer_id} not found")
    return dict(row)


def insert_lab_sample(field_id: str, pol: float, brix: float,
                      purity: float, katc: float) -> int:
    connection = connect()
    cursor = connection.execute(
        "INSERT INTO lab_samples (field_id, pol, brix, purity, katc, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (field_id, pol, brix, purity, katc,
         datetime.now().isoformat(timespec="seconds")))
    connection.commit()
    count = connection.execute("SELECT COUNT(*) FROM lab_samples").fetchone()[0]
    connection.close()
    return count


def get_lab_samples() -> list[dict[str, Any]]:
    connection = connect()
    rows = connection.execute("SELECT * FROM lab_samples ORDER BY id").fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_field_history(field_id: str) -> list[dict[str, Any]]:
    connection = connect()
    rows = connection.execute(
        "SELECT * FROM zafras WHERE field_id = ? ORDER BY season", (field_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_seasons() -> list[str]:
    connection = connect()
    rows = connection.execute(
        "SELECT DISTINCT season FROM zafras ORDER BY season").fetchall()
    connection.close()
    return [row["season"] for row in rows]


def get_season_summary(season: str) -> dict[str, Any]:
    connection = connect()
    row = connection.execute(
        "SELECT COUNT(*) AS fields, SUM(tons_cane) AS tons_cane, "
        "SUM(sugar_tons) AS sugar_tons, AVG(tch) AS tch, AVG(tah) AS tah, "
        "AVG(pol_avg) AS pol FROM zafras WHERE season = ?", (season,)).fetchone()
    connection.close()
    return dict(row)


def get_variety_performance() -> list[dict[str, Any]]:
    connection = connect()
    rows = connection.execute(
        "SELECT fields.variety AS variety, COUNT(*) AS records, "
        "AVG(zafras.tch) AS tch, AVG(zafras.tah) AS tah, "
        "AVG(zafras.rendimiento) AS rendimiento "
        "FROM zafras JOIN fields ON zafras.field_id = fields.id "
        "GROUP BY fields.variety ORDER BY tah DESC").fetchall()
    connection.close()
    return [dict(row) for row in rows]
