from flask import Flask
from flask_socketio import SocketIO, emit
import sqlite3, os
from flask import request

app = Flask(__name__)
socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    async_mode="eventlet",
                    transports=["websocket"])

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

# ---------- USER ↔ SOCKET MAP ----------
users = {}  # username -> socket id

# ---------- SOCKET EVENTS ----------


@socketio.on("login")
def login(data):
    username = data["username"]
    users[username] = request.sid  # 🔥 MAIN LINE
    emit("login_success", {"username": username})
    print(f"✅ {username} logged in")


@socketio.on("disconnect")
def disconnect():
    # user logout cleanup
    for user, sid in list(users.items()):
        if sid == request.sid:
            del users[user]
            print(f"❌ {user} disconnected")
            break


@socketio.on("message")
def handle_message(data):
    print("📩 MESSAGE RECEIVED:", data)  # 👈 ADD

    socketio.emit("message", data)


@socketio.on("private_message")
def handle_private_message(data):
    print("📩 FROM ANDROID:", data)
    print("👥 ONLINE USERS:", users)

    sender = data["sender"]
    receiver = data["receiver"]
    message = data["message"]

    # ---- save to DB ----
    con = get_db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
        (sender, receiver, message))
    con.commit()
    con.close()

    # ---- send only to receiver ----
    if receiver in users:
        emit("message", data, to=users[receiver])

    # ---- optional: echo back to sender ----
    if sender in users:
        emit("message", data, to=users[sender])


@socketio.on("load_messages")
def load_messages(data):
    me = data["me"]
    other = data["other"]

    con = get_db()
    cur = con.cursor()
    cur.execute(
        """
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
    print("⌨️ TYPING:", data)  # 👈 ADD
    receiver = data["receiver"]
    if receiver in users:
        emit("typing", data, to=users[receiver])


@socketio.on("image")
def handle_image(data):
    # data = { sender, receiver, image }
    socketio.emit("image", data)


if __name__ == "__main__":
    print("🚀 Server running on http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
