CREATE TABLE IF NOT EXISTS videos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,                     
    tags       TEXT,                              
    location   TEXT,  
    cameraId   TEXT,
    baseUrl    TEXT,                              
    movieId    TEXT UNIQUE,
    createdAt  TEXT DEFAULT (datetime('now')),
    updatedAt  TEXT DEFAULT (datetime('now'))

    FOREIGN KEY (cameraId) REFERENCES cameras(id)
);

