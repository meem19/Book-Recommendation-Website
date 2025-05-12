CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    profile_pic VARCHAR(10) DEFAULT 'male',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE read_book (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_title VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'read',
    rating INTEGER,
    review TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE user_preference (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);
