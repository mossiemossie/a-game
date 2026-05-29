from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import random as rand
import string
import json
import asyncio 
import time 
from gamemaster import GameMaster


app = FastAPI()


# ==============================
# Room / Backend Logic
# ==============================

class Room:
    def __init__(self, code, host_name):
        self.code = code
        self.host = host_name
        self.players = [host_name] # list of player names (strings)
        self.state = "lobby"
        self.chat_log = []
        self.connections = {} # mapping from player id to websocket
        self.player_dict = {} # mapping from player id to player name
        self.phase = 'day'
        self.phase_end_time = None
        self.timer_task = None

        self.game_master = None  # placeholder

    async def broadcast(self):
        """Send full state to all players"""
        # no don't fucking do that omg
        state = self.get_state()

        for conn in self.connections:
            await self.connections[conn].send_text(json.dumps({
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
            "phase": self.phase,
            "phase_end_time": self.phase_end_time
        }

    async def game_loop(self):
        days = [d for d in range(1, 11)]
        phases = ['transition', 'night', 'transition', 'day']
        while True:
            for d in days:
                for p in phases:
                    t = 5 if p == 'transition' else 30
                    if self.phase == 'night':
                        self.game_master.process_player_actions()

                    self.phase = p  
                    self.phase_end_time = time.time() + t
                    await self.broadcast()
                    await asyncio.sleep(t)
            

    async def add_player(self, name, websocket):
        if self.state != "lobby":
            return False

        self.players.append(name)
        connection_num = len(self.connections)
        self.connections.update({connection_num : websocket})
        self.chat_log.append(("SYSTEM", f"{name} joined"))

        await self.broadcast()
        return True

    async def add_message(self, player, message):
        self.chat_log.append((player, message))
        await self.broadcast()

    async def start_game(self, player):
        if player != self.host:
            return
        
        # rearrange the numbers in the self.connections dictionary
        
        order = list(range(0, len(self.players)))
        rand.shuffle(order)
        new_connections_dict = {i : self.connections[c] for i, c in enumerate(order)}
        self.connections = new_connections_dict
        self.player_dict = {i : self.players[p] for i, p in enumerate(order)}
        self.players = [f'{i}: {self.player_dict[i]}' for i in range(0, len(self.players))]

        self.game_master = GameMaster(self.player_dict)

        self.state = "in_game"
        self.chat_log.append(("SYSTEM", "Game started"))

        self.timer_task = asyncio.create_task(self.game_loop())

        await self.broadcast()


class RoomManager:
    def __init__(self):
        self.rooms = {}

    def create_room(self, host_name):
        code = ''.join(rand.choices(string.ascii_uppercase, k=4))
        room = Room(code, host_name)
        self.rooms[code] = room
        return room

    def get_room(self, code):
        return self.rooms.get(code)


ROOM_MANAGER = RoomManager()


class PlayerAction: #this will maybe be the action that gets sent to the gamemaster? dunno hey.
    def __init__(self):
        pass

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
                print(f'NAME IS {player_name}')
                if player_name == '':
                    await websocket.send_text(json.dumps({
                        "type" : "error",
                        "message" : "Enter a name"
                    }))

                room = ROOM_MANAGER.create_room(player_name)
                room.connections.update({len(room.connections) : websocket})

                await room.broadcast()

            # ----------------------
            # JOIN ROOM
            # ----------------------
            elif msg["type"] == "join":
                player_name = msg["name"]
                if player_name == '':
                    await websocket.send_text(json.dumps({
                        "type" : "error",
                        "message" : "Enter a name"
                    }))

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
        if room and websocket in room.connections.values():
            room.connections.pop([k for k, v in room.connections.items() if v == websocket][0])