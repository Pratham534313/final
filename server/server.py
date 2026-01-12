from flask import Flask, request
from flask_socketio import SocketIO, emit
import sqlite3, os

# ================= APP =================
app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    transports=["websocket"]
)

# ================= DB =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    con = get_db()
    cur = con.cursor()

    # ---- create table if not exists ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.commit()
    con.close()
    print("✅ Database ready")


init_db()

# ================= USER ↔ SOCKET =================
users = {}  # username -> socket id

# ================= SOCKET EVENTS =================

@socketio.on("login")
def login(data):
    username = data["username"]
    users[username] = request.sid
    emit("login_success", {"username": username})
    print(f"✅ {username} logged in")


@socketio.on("disconnect")
def disconnect():
    for user, sid in list(users.items()):
        if sid == request.sid:
            del users[user]
            print(f"❌ {user} disconnected")
            break


# ---------- TEXT MESSAGE ----------
@socketio.on("private_message")
def handle_private_message(data):
    sender = data["sender"]
    receiver = data["receiver"]
    message = data["message"]

    print("📩 MESSAGE:", data)

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO messages (sender, receiver, message)
        VALUES (?, ?, ?)
    """, (sender, receiver, message))
    con.commit()
    con.close()

    # send to receiver
    if receiver in users:
        emit("message", data, to=users[receiver])

    # echo to sender
    if sender in users:
        emit("message", data, to=users[sender])


# ---------- IMAGE MESSAGE ----------
@socketio.on("image")
def handle_image(data):
    sender = data["sender"]
    receiver = data["receiver"]
    image = data["image"]

    print("🖼 IMAGE RECEIVED")

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO messages (sender, receiver, image)
        VALUES (?, ?, ?)
    """, (sender, receiver, image))
    con.commit()
    con.close()

    # send to receiver
    if receiver in users:
        emit("image", data, to=users[receiver])

    # echo to sender
    if sender in users:
        emit("image", data, to=users[sender])


# ---------- LOAD OLD MESSAGES ----------
@socketio.on("load_messages")
def load_messages(data):
    me = data["me"]
    other = data["other"]

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT sender, receiver, message, image
        FROM messages
        WHERE (sender=? AND receiver=?)
           OR (sender=? AND receiver=?)
        ORDER BY id ASC
    """, (me, other, other, me))

    rows = cur.fetchall()
    con.close()

    emit("old_messages", rows)


# ---------- TYPING ----------
@socketio.on("typing")
def handle_typing(data):
    receiver = data["receiver"]
    if receiver in users:
        emit("typing", data, to=users[receiver])


# ================= RUN =================
if __name__ == "__main__":
    print("🚀 Server running on http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
