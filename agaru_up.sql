CREATE TABLE IF NOT EXISTS videos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,                     
    tags       TEXT,                              
    location   TEXT,                              
    baseUrl    TEXT,                              
    movieId    TEXT UNIQUE,
    createdAt  TEXT DEFAULT (datetime('now')),
    updatedAt  TEXT DEFAULT (datetime('now'))
);

INSERT INTO videos (title, tags, location, baseUrl, movieId)
VALUES (
    '過去一アガった瞬間！！',
    '大阪駅,tag2,tag3',
    'camera1',
    'https://example.com/agaru-up-videos',
    'uuid-example-1'
);
