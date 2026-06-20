import sqlite3

def create_database():
    conn = sqlite3.connect("clinic.db")

    cursor = conn.cursor()

    cursor.execute("""
   CREATE TABLE IF NOT EXISTS patients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    token INTEGER NOT NULL,
    status TEXT DEFAULT 'waiting',
    priority TEXT DEFAULT 'Low',
    created_date TEXT,
    created_time TEXT,
    completed_time TEXT
)
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS settings(
    id INTEGER PRIMARY KEY,
    avg_time INTEGER DEFAULT 10
)
""")

    cursor.execute("""
INSERT OR IGNORE INTO settings(id,avg_time)
VALUES(1,10)
""")

    conn.commit()
    conn.close()

create_database()