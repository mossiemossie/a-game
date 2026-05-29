"""
For reference:
a game_master object is loaded in main.py (from here.)

It is initiated in the function start_game in main.py.

From there, we will make a call from main.py to gamemaster in the game_loop function.

Will have to make functions in main.py which handle how information flows through main.py from the UI to the gamemaster object.

Currently, broadcast exists as one function that does that in one direction.

Actions go through to websocket_endpoint in main.py and end up right at the bottom of the function. What we'll do there, eventually,
is get that to store what it is the player did, and then when the daypart changes, send all that information over here, to calculate
what should be happening on a player-by-player basis.

What i'll do first here, is get this to load in relevant player objects (& as such perk objects as well).

Then, I'll figure out how we can send information about the players up the chain.

Then 

"""

from player import Player

class GameMaster:
    def __init__(self, player_dict):
        self.num_players = len(player_dict)
        self.players = {i : Player(i, self.num_players) for i in player_dict.keys()}
        self.test = 0


    def get_player_state(self, player_id):
        # returns the state of the given player; this includes
        # - what perks they have
        # - what actions they have (subset of perks)
        # - whether they are the killer
        # - 
        pass

    def process_player_actions(self, actions):
        pass


    def iterate_a_number(self):
        self.test += 1

    def get_a_number(self):
        return self.test