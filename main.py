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
        self.notification_log = {}

        # mapping from player id to websocket
        self.connections = {} 

        # mapping from player id to player name
        self.player_id_to_name = {} 
        self.player_name_to_id = {}

        # mapping from player id to last action taken
        # read and then wiped at the end of each night phase
        # updated every time an action is made.
        self.actions = {} 

        self.phase = 'day'
        self.phase_end_time = None
        self.timer_task = None

        self.game_master = None  # placeholder

    async def broadcast(self):
        """Send full state to all players"""
        state = self.get_public_state()

        for player_id in self.connections:
            private_state = self.game_master.get_private_state(player_id)
            state.update(private_state)
            state.update(
                {
                    "actions" : ['Watch', 'Shield', 'Triangulate'], #temp
                    "action_targets" : 
                    {
                        "Watch" : 0,
                        "Shield" : 1,
                        "Triangulate" : 2
                    }
                }
            )

            await self.connections[player_id].send_text(json.dumps({
                "type": "state",
                "data": state
            }))

    def get_public_state(self):
        """Return public state"""
        return {
            "code": self.code,
            "players": self.players,
            "host": self.host,
            "state": self.state,
            "chat": self.chat_log,
            "phase": self.phase,
            "phase_end_time": self.phase_end_time,
        }

    async def game_loop(self):
        days = [d for d in range(1, 11)]
        phases = ['transition', 'night', 'transition', 'day']
        while True:
            for d in days:
                for p in phases:
                    t = 5 if p == 'transition' else 30
                    if self.phase == 'night': #night phase has ended, so read and then wipe the actions dict.
                        new_notifications = self.game_master.process_player_actions(self.actions)
                        for player_id in new_notifications:
                            self.notification_log[player_id].append(new_notifications[player_id])
                            
                        self.wipe_actions()
                        await self.broadcast()

                    self.phase = p  
                    self.phase_end_time = time.time() + t
                    await self.broadcast()
                    await asyncio.sleep(t)
            
    async def update_actions(self, name, msg):
        player_id = self.player_name_to_id[name]
        self.actions[player_id] = {'action' : msg['action'], 'targets' : msg['targets']}

    def wipe_actions(self):
        self.actions = {i : None for i in range(0, len(self.players))}
    

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
        
        # init our various dictionaries
        # rearrange the numbers in the self.connections dictionary
        
        order = list(range(0, len(self.players)))
        rand.shuffle(order)
        new_connections_dict = {i : self.connections[c] for i, c in enumerate(order)}
        self.connections = new_connections_dict

        self.player_id_to_name = {i : self.players[p] for i, p in enumerate(order)}
        self.player_name_to_id = {v:k for k,v in self.player_id_to_name.items()}
        self.players = [f'{i}: {self.player_id_to_name[i]}' for i in range(0, len(self.players))] #maybe a mistake

        self.actions = {i : None for i, _ in enumerate(order)}
        self.notification_log = {i : [] for i, _ in enumerate(order)}

        self.game_master = GameMaster(self.player_id_to_name)

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
                room.update_actions(player_name, msg)
                await room.add_message(player_name, f"[ACTION] {msg['action']}") #rmv later

    except WebSocketDisconnect:
        if room and websocket in room.connections.values():
            room.connections.pop([k for k, v in room.connections.items() if v == websocket][0])