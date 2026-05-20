from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import random
import string
import json

app = FastAPI()


# ==============================
# Room / Backend Logic
# ==============================

class Room:
    def __init__(self, code, host_name):
        self.code = code
        self.host = host_name
        self.players = [host_name]
        self.state = "lobby"
        self.chat_log = []
        self.connections = []  # active websockets

        self.game_master = None  # placeholder

    async def broadcast(self):
        """Send full state to all players"""
        state = self.get_state()

        for conn in self.connections:
            await conn.send_text(json.dumps({
                "type": "state",
                "data": state
            }))

    def get_state(self):
        """Return public state (filter later per player)"""
        return {
            "code": self.code,
            "players": self.players,
            "host": self.host,
            "state": self.state,
            "chat": self.chat_log,
        }

    async def add_player(self, name, websocket):
        if self.state != "lobby":
            return False

        self.players.append(name)
        self.connections.append(websocket)
        self.chat_log.append(("SYSTEM", f"{name} joined"))

        await self.broadcast()
        return True

    async def add_message(self, player, message):
        self.chat_log.append((player, message))
        await self.broadcast()

    async def start_game(self, player):
        if player != self.host:
            return

        self.state = "in_game"
        self.chat_log.append(("SYSTEM", "Game started"))

        await self.broadcast()


class RoomManager:
    def __init__(self):
        self.rooms = {}

    def create_room(self, host_name):
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        room = Room(code, host_name)
        self.rooms[code] = room
        return room

    def get_room(self, code):
        return self.rooms.get(code)


ROOM_MANAGER = RoomManager()


# ==============================
# HTTP Endpoint (serve frontend)
# ==============================

@app.get("/")
def get():
    with open("index.html") as f:
        return HTMLResponse(f.read())


# ==============================
# WebSocket Endpoint
# ==============================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    player_name = None
    room = None

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            # ----------------------
            # CREATE ROOM
            # ----------------------
            if msg["type"] == "create":
                player_name = msg["name"]
                room = ROOM_MANAGER.create_room(player_name)
                room.connections.append(websocket)

                await room.broadcast()

            # ----------------------
            # JOIN ROOM
            # ----------------------
            elif msg["type"] == "join":
                player_name = msg["name"]
                room = ROOM_MANAGER.get_room(msg["code"])

                if room:
                    success = await room.add_player(player_name, websocket)
                    if not success:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Game already started"
                        }))

            # ----------------------
            # CHAT
            # ----------------------
            elif msg["type"] == "chat":
                await room.add_message(player_name, msg["message"])

            # ----------------------
            # START GAME
            # ----------------------
            elif msg["type"] == "start":
                await room.start_game(player_name)

            # ----------------------
            # ACTION (placeholder)
            # ----------------------
            elif msg["type"] == "action":
                await room.add_message(player_name, f"[ACTION] {msg['action']}")

    except WebSocketDisconnect:
        if room and websocket in room.connections:
            room.connections.remove(websocket)