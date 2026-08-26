CREATE TABLE IF NOT EXISTS lab_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id TEXT,
    pol REAL,
    brix REAL,
    purity REAL,
    katc REAL,
    created_at TEXT
);
