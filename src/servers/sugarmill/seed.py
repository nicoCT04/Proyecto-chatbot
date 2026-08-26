from __future__ import annotations

import random
from pathlib import Path
from typing import Any

SQL_DIR = Path(__file__).parent / "sql"

SEASONS = ["2021-2022", "2022-2023", "2023-2024", "2024-2025"]
SEASON_WEATHER = {
    "2021-2022": 1.00,
    "2022-2023": 1.03,
    "2023-2024": 0.93,
    "2024-2025": 1.05,
}

VARIETIES = ["CG02-163", "CG02-163", "CG02-163", "CG02-163",
             "CP72-2086", "CP72-2086", "CG98-78", "CP73-1547", "CG00-102"]

PRODUCERS = [
    ("P-01", "Finca La Esperanza", "Santa Lucía Cotzumalguapa"),
    ("P-02", "Finca El Naranjo", "Escuintla"),
    ("P-03", "Cooperativa Costa Sur", "Tiquisate"),
    ("P-04", "Finca Santa Ana", "Masagua"),
    ("P-05", "Finca El Baúl", "Siquinalá"),
    ("P-06", "Finca Tululá", "La Gomera"),
]

FIELD_COUNT = 15


def generate() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(42)

    producers = [{"id": pid, "name": name, "municipality": municipality}
                 for pid, name, municipality in PRODUCERS]

    fields = []
    for index in range(1, FIELD_COUNT + 1):
        base_pol = round(rng.uniform(13.0, 15.0), 1)
        peak_pol = round(base_pol + rng.uniform(0.1, 0.6), 1)
        weeks_to_peak = rng.choice([-1, 0, 0, 1, 1, 2, 3, 4, 5])
        purity = rng.uniform(0.83, 0.87)
        fields.append({
            "id": f"F-{index:02d}",
            "producer_id": rng.choice(PRODUCERS)[0],
            "variety": rng.choice(VARIETIES),
            "hectares": round(rng.uniform(25, 120), 1),
            "planting_date": f"{rng.choice([2023, 2024])}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            "base_pol": base_pol,
            "peak_pol": peak_pol,
            "weeks_to_peak": weeks_to_peak,
            "brix": round(base_pol / purity, 1),
            "yield_tons_per_ha": round(rng.uniform(90, 125), 1),
            "status": "ready" if weeks_to_peak <= 1 else "standing",
        })

    zafras = []
    record_id = 1
    for field in fields:
        for season in SEASONS:
            weather = SEASON_WEATHER[season]
            tch = round(field["yield_tons_per_ha"] * weather * rng.uniform(0.96, 1.04), 1)
            tons_cane = round(field["hectares"] * tch, 1)
            rendimiento = round(rng.uniform(102, 116) * weather, 1)
            sugar_tons = round(tons_cane * rendimiento / 1000, 1)
            pol_avg = round(rng.uniform(13.0, 15.0), 2)
            purity = rng.uniform(0.83, 0.87)
            zafras.append({
                "id": record_id,
                "field_id": field["id"],
                "season": season,
                "tons_cane": tons_cane,
                "pol_avg": pol_avg,
                "brix_avg": round(pol_avg / purity, 2),
                "rendimiento": rendimiento,
                "sugar_tons": sugar_tons,
                "tch": tch,
                "tah": round(sugar_tons / field["hectares"], 2),
            })
            record_id += 1

    return producers, fields, zafras


def _sql_value(value: Any) -> str:
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)


def _table_file(filename: str, table: str, columns: list[str],
                keys: list[str], rows: list[dict[str, Any]]) -> None:
    definition = ",\n".join(f"    {column}" for column in columns)
    values = ",\n".join(
        "(" + ", ".join(_sql_value(row[key]) for key in keys) + ")" for row in rows)
    text = (
        f"CREATE TABLE IF NOT EXISTS {table} (\n{definition}\n);\n\n"
        f"INSERT OR IGNORE INTO {table} ({', '.join(keys)}) VALUES\n{values};\n"
    )
    (SQL_DIR / filename).write_text(text, encoding="utf-8")


def _schema_file(filename: str, table: str, columns: list[str]) -> None:
    definition = ",\n".join(f"    {column}" for column in columns)
    text = f"CREATE TABLE IF NOT EXISTS {table} (\n{definition}\n);\n"
    (SQL_DIR / filename).write_text(text, encoding="utf-8")


def write_sql_files() -> None:
    producers, fields, zafras = generate()
    SQL_DIR.mkdir(exist_ok=True)
    _table_file("01_producers.sql", "producers",
                ["id TEXT PRIMARY KEY", "name TEXT", "municipality TEXT"],
                ["id", "name", "municipality"], producers)
    _table_file("02_fields.sql", "fields",
                ["id TEXT PRIMARY KEY", "producer_id TEXT", "variety TEXT",
                 "hectares REAL", "planting_date TEXT", "base_pol REAL",
                 "peak_pol REAL", "weeks_to_peak INTEGER", "brix REAL",
                 "yield_tons_per_ha REAL", "status TEXT"],
                ["id", "producer_id", "variety", "hectares", "planting_date",
                 "base_pol", "peak_pol", "weeks_to_peak", "brix",
                 "yield_tons_per_ha", "status"], fields)
    _table_file("03_zafras.sql", "zafras",
                ["id INTEGER PRIMARY KEY", "field_id TEXT", "season TEXT",
                 "tons_cane REAL", "pol_avg REAL", "brix_avg REAL",
                 "rendimiento REAL", "sugar_tons REAL", "tch REAL", "tah REAL"],
                ["id", "field_id", "season", "tons_cane", "pol_avg", "brix_avg",
                 "rendimiento", "sugar_tons", "tch", "tah"], zafras)
    _schema_file("04_lab_samples.sql", "lab_samples",
                 ["id INTEGER PRIMARY KEY AUTOINCREMENT", "field_id TEXT",
                  "pol REAL", "brix REAL", "purity REAL", "katc REAL",
                  "created_at TEXT"])


if __name__ == "__main__":
    write_sql_files()
    print(f"SQL files written to {SQL_DIR}")
