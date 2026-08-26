CREATE TABLE IF NOT EXISTS producers (
    id TEXT PRIMARY KEY,
    name TEXT,
    municipality TEXT
);

INSERT OR IGNORE INTO producers (id, name, municipality) VALUES
('P-01', 'Finca La Esperanza', 'Santa Lucía Cotzumalguapa'),
('P-02', 'Finca El Naranjo', 'Escuintla'),
('P-03', 'Cooperativa Costa Sur', 'Tiquisate'),
('P-04', 'Finca Santa Ana', 'Masagua'),
('P-05', 'Finca El Baúl', 'Siquinalá'),
('P-06', 'Finca Tululá', 'La Gomera');
