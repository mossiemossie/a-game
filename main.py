from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import random as rand
import string
import json
import asyncio 
import time 
from gamemaster import GameMaster
import sys

app = FastAPI()


# ==============================
# Room / Backend Logic
# ==============================

class Room:
    def __init__(self, code, host_name, host_websocket):
        self.code = code
        self.host = host_name
        self.state = "lobby"
        self.chat_log = []
        self.phase = 'day'
        self.phase_end_time = None
        self.timer_task = None
        self.game_master = None  # placeholder
        self.players = {1 : PlayerData(1, host_name, host_websocket)}


    async def broadcast(self):
        """Send full state to all players"""
        state = self.get_public_state()

        for p_id in self.players:
            if self.game_master is not None:
                private_state = self.game_master.get_private_state(p_id)
                private_state.update(state)
                private_state.update({"notifications" : self.players[p_id].get_notifications()})
            else:
                # no room yet, so no private state; use a dummy here.
                private_state = {'notifications' : [], 'id' : p_id}
                private_state.update(state)

            await self.players[p_id].get_connection().send_text(json.dumps({
                "type": "state",
                "data": private_state
            }))


    def get_public_state(self):
        """Return public state"""
        return {
            "code": self.code,
            "players": self.get_player_json(),
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
                        new_notifications = self.game_master.process_night_actions(self.get_actions())
                        for p_id in new_notifications:
                            self.players[p_id].add_notifications(new_notifications[p_id])

                        self.wipe_actions()
                        await self.broadcast()

                    self.phase = p  
                    self.phase_end_time = time.time() + t
                    await self.broadcast()
                    await asyncio.sleep(t)


    def get_actions(self):
        return {p_id : self.players[p_id].get_action() for p_id in self.players}
    

    def get_connections(self):
        return [self.players[p].get_connection() for p in self.players]
    

    def get_player_json(self):
        return [self.players[p].get_json_chunk() for p in self.players]

            
    async def update_actions(self, websocket, msg):
        #player_id = self.player_name_to_id[name]
        #self.actions[player_id] = {'action' : msg['action'], 'targets' : msg['targets']}
        p_id = self.get_p_id_from_websocket(websocket)
        self.players[p_id].set_action(msg['action'], msg['targets'])


    def wipe_actions(self):
        for p_id in self.players:
            self.players[p_id].reset_action()
        #self.actions = {i : {'action' : 'nothing', 'targets' : None} for i in range(0, len(self.players))}
    

    async def add_player(self, name, websocket):
        if self.state != "lobby":
            return False

        self.players.update({len(self.players) + 1 : PlayerData(len(self.players) + 1, name, websocket)})
        self.chat_log.append(("SYSTEM", f"{name} joined"))

        await self.broadcast()
        return True
    

    async def add_message(self, websocket, message):
        p_id = self.get_p_id_from_websocket(websocket)
        self.chat_log.append((self.players[p_id].get_vis_name(), message))
        await self.broadcast()

    
    def get_p_id_from_websocket(self, websocket):
        return [x for x in self.players if self.players[x].get_connection() == websocket][0]


    async def start_game(self, player):
        if player != self.host:
            return
        
        # init our various dictionaries
        # rearrange the numbers in the self.connections dictionary
        
        order = list(range(1, len(self.players) + 1))
        rand.shuffle(order)
        self.players = {i : self.players[c] for i, c in enumerate(order)}
        
        for p_id in self.players:
            self.players[p_id].set_id(p_id)

        self.game_master = GameMaster(list(self.players.keys())) #change this!!!!!

        self.state = "in_game"
        self.chat_log.append(("SYSTEM", "Game started"))

        self.timer_task = asyncio.create_task(self.game_loop())

        await self.broadcast()


class PlayerData:
    def __init__(self, id, name, connection):
        self.id = id 
        self.notifications = []
        self.name = name
        self.connection = connection
        self.action = {'action' : 'nothing', 'targets' : None}

    def get_json_chunk(self):
        return {'id' : self.id, 'name' : self.name}
    
    def get_connection(self):
        return self.connection
    
    def get_notifications(self):
        return self.notifications
    
    def add_notifications(self, notifs):
        self.notifications.extend(notifs)

    def get_vis_name(self):
        return f'[{self.id}]: {self.name}'

    def set_id(self, id):
        self.id = id

    def get_action(self):
        return self.action

    def set_action(self, action, targets):
        self.action['action'] = action
        self.action['targets'] = targets

    def reset_action(self):
        self.action['action'] = 'nothing'
        self.action['targets'] = None



class RoomManager:
    def __init__(self):
        self.rooms = {}

    def create_room(self, host_name, host_websocket):
        #code = ''.join(rand.choices(string.ascii_uppercase, k=1))
        code = '' #temp
        room = Room(code, host_name, host_websocket)
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

                room = ROOM_MANAGER.create_room(player_name, websocket)

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
                await room.add_message(websocket, msg["message"])

            # ----------------------
            # START GAME
            # ----------------------
            elif msg["type"] == "start":
                await room.start_game(player_name)

            # ----------------------
            # ACTION (placeholder)
            # ----------------------
            elif msg["type"] == "action":
                await room.update_actions(websocket, msg)
                await room.add_message(websocket, f"[ACTION] {msg['action']}") #rmv later

    except WebSocketDisconnect:
        if room and websocket in room.get_connections():
            room.remove_connection(websocket) #is this even the way i want this to go?
            #room.connections.pop([k for k, v in room.connections.items() if v == websocket][0])