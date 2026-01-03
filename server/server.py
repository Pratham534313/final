from flask import Flask
from flask_socketio import SocketIO, emit
import sqlite3, os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ---------- DB ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT
        )
    """)
    con.commit()
    con.close()

init_db()

# ---------- SOCKET EVENTS ----------

@socketio.on("login")
def login(data):
    emit("login_success", {"username": data["username"]})

@socketio.on("message")
def handle_message(data):
    con = get_db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
        (data["sender"], data["receiver"], data["message"])
    )
    con.commit()
    con.close()

    socketio.emit("message", data)

@socketio.on("load_messages")
def load_messages(data):
    me = data["me"]
    other = data["other"]

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT sender, receiver, message FROM messages
        WHERE (sender=? AND receiver=?)
           OR (sender=? AND receiver=?)
        ORDER BY id ASC
    """, (me, other, other, me))
    rows = cur.fetchall()
    con.close()

    emit("old_messages", rows)

@socketio.on("typing")
def handle_typing(data):
    socketio.emit("typing", data)

if __name__ == "__main__":
    print("🚀 Server running on http://127.0.0.1:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
