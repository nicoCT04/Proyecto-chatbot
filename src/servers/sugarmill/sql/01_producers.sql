-- Producers (fincas and cooperatives supplying the mill).

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
    ('P-06', 'Finca Tululá', 'La Gomera'),
    ('P-07', 'Finca San Diego', 'Escuintla'),
    ('P-08', 'Finca Bouganvilia', 'Nueva Concepción'),
    ('P-09', 'Cooperativa La Unión', 'La Democracia'),
    ('P-10', 'Finca Pantaleón', 'Siquinalá'),
    ('P-11', 'Finca Santa Teresa', 'Santa Lucía Cotzumalguapa'),
    ('P-12', 'Finca Las Margaritas', 'Tiquisate'),
    ('P-13', 'Finca El Carmen', 'Masagua'),
    ('P-14', 'Cooperativa Nuevo Amanecer', 'La Gomera'),
    ('P-15', 'Finca Buganvilias del Sur', 'Guanagazapa'),
    ('P-16', 'Finca San Rafael', 'Escuintla');
