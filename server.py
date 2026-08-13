import json
import time
from pathlib import Path

from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from flask import request

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.json"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
app.config["SECRET_KEY"] = "msn-conversinhas-brasil"
socketio = SocketIO(app, cors_allowed_origins="*")

# sid -> perfil
users = {}
# lista de mensagens (type: message | system | nudge)
history = []

STATUSES = ["online", "ausente", "ocupado"]
MAX_HISTORY = 2000


def now_ms():
    return int(time.time() * 1000)


# ---------------------------------------------------------------- persistência

def load_history():
    global history
    try:
        if HISTORY_FILE.exists():
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                history = data
    except Exception as exc:
        print("[server] Erro ao carregar histórico:", exc)


def save_history():
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        print("[server] Erro ao salvar histórico:", exc)


def add_history(entry):
    history.append(entry)
    if len(history) > MAX_HISTORY:
        del history[: len(history) - MAX_HISTORY]
    save_history()
    return entry


# ---------------------------------------------------------------- utilitários

def public_profile(sid):
    u = users[sid]
    return {
        "name": u["name"],
        "status": u["status"],
        "color": u["color"],
        "avatar": u["avatar"],
        "message": u["message"],
    }


def broadcast_users():
    socketio.emit(
        "users",
        [{**public_profile(sid), "sid": sid} for sid in users],
    )


def system_message(text):
    entry = add_history({"type": "system", "text": text, "time": now_ms()})
    socketio.emit("message", entry)
    return entry


# ---------------------------------------------------------------- eventos

@socketio.on("connect")
def on_connect():
    emit("welcome", {"history_count": len(history)})


@socketio.on("login")
def on_login(data):
    name = (data.get("name") or "").strip()[:24] or "Usuário"
    color = data.get("color") or "#2F5FAD"
    avatar = data.get("avatar")
    message = (data.get("message") or "").strip()[:80]
    status = data.get("status") if data.get("status") in STATUSES else "online"

    users[request.sid] = {
        "name": name,
        "status": status,
        "color": color,
        "avatar": avatar,
        "message": message,
    }

    emit("you", {**public_profile(request.sid), "sid": request.sid})
    emit("history", history)
    broadcast_users()
    system_message(f"{name} entrou no chat")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    if sid in users:
        name = users[sid]["name"]
        del users[sid]
        broadcast_users()
        system_message(f"{name} saiu do chat")


@socketio.on("message")
def on_message(data):
    sid = request.sid
    if sid not in users:
        return
    text = (data.get("text") or "").strip()
    if not text or len(text) > 1500:
        return

    entry = add_history(
        {
            "type": "message",
            "sender": users[sid]["name"],
            "color": users[sid]["color"],
            "text": text,
            "time": now_ms(),
            "sid": sid,
        }
    )
    socketio.emit("message", entry)


@socketio.on("update_profile")
def on_update_profile(data):
    sid = request.sid
    if sid not in users:
        return

    u = users[sid]

    if "name" in data:
        new_name = (data["name"] or "").strip()[:24]
        if new_name and new_name != u["name"]:
            old = u["name"]
            u["name"] = new_name
            socketio.emit(
                "user_renamed", {"old": old, "new": u["name"], "sid": sid}
            )
            system_message(f"{old} agora se chama {u['name']}")

    if "avatar" in data:
        u["avatar"] = data["avatar"] or None

    if "message" in data:
        u["message"] = (data["message"] or "").strip()[:80]

    if "color" in data:
        u["color"] = (data["color"] or "#2F5FAD")[:7]

    if "status" in data and data["status"] in STATUSES:
        u["status"] = data["status"]

    broadcast_users()
    emit("you", {**public_profile(sid), "sid": sid})


@socketio.on("nudge")
def on_nudge():
    sid = request.sid
    if sid not in users:
        return
    entry = add_history(
        {
            "type": "nudge",
            "sender": users[sid]["name"],
            "color": users[sid]["color"],
            "time": now_ms(),
            "sid": sid,
        }
    )
    socketio.emit("nudge", {"sender": users[sid]["name"], "sid": sid})
    socketio.emit("message", entry)


@socketio.on("typing")
def on_typing():
    sid = request.sid
    if sid not in users:
        return
    socketio.emit("typing", {"name": users[sid]["name"], "sid": sid})


# ---------------------------------------------------------------- páginas

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    load_history()
    print("[MSN Conversinhas] http://127.0.0.1:5000")
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
    
