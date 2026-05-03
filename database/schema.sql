CREATE TABLE IF NOT EXISTS measurements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    co2_ppm     INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity    REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_measurements_ts ON measurements(timestamp);

CREATE TABLE IF NOT EXISTS thresholds (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    co2_warning   INTEGER NOT NULL DEFAULT 800,
    co2_critical  INTEGER NOT NULL DEFAULT 1200,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO thresholds (id, co2_warning, co2_critical) VALUES (1, 800, 1200);

CREATE TABLE IF NOT EXISTS room_occupancy (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    person_count INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_occupancy_ts ON room_occupancy(timestamp);
