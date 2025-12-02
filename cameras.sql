CREATE TABLE IF NOT EXISTS cameras (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    latitude   REAL NOT NULL,
    longitude  REAL NOT NULL,
    url        TEXT NOT NULL,
    createdAt  TEXT DEFAULT (datetime('now')),
    updatedAt  TEXT DEFAULT (datetime('now'))
);
