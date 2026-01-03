import sqlite3
import os

# 🔥 ABSOLUTE DB PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# USERS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    online INTEGER DEFAULT 0,
    last_seen TEXT
)
""")

# MESSAGES TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    timestamp TEXT,
    status TEXT
)
""")

con.commit()
con.close()

print("✅ Database initialized")
print("📁 DB PATH:", DB_PATH)
