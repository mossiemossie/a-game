"""
gamemaster - handles game logic outside of main.py which is essentially an interface between the backend and the frontend.
defines/controls actions_df - actions_df collates information from the actions the players took, as well as information about the players
defines/controls votes_df - votes_df collates information from the votes the players made, as well as information about the players.
defines/controls points_df - details from points_df needs to be sent through to the state json

night_abilities - everything that gets done to actions_df since that's a lot of logic

day_abilities - everything that gets done to votes_df since that's a lot of logic

player.py - player objects that define what perks/actions each player has, as well as charges

perks.py - perk objects - defines parameters of the perks, and the text the player will be sent.
"""

from player import Player
import random as rand
from defs import PERKS, PERK_WEIGHTS, UNIQUE_PERKS, VISIT_PERKS, FIRST_ROUND_PERKS
from night_logic import parse

class GameMaster:
    def __init__(self, player_id_to_name):
        self.num_players = len(player_id_to_name)
        self.player_ids = list(player_id_to_name.keys())

        self.players = {i : Player(i, self.player_ids) for i in self.player_ids}
        self.current_cursed = rand.choice(self.player_ids)
        self.players[self.current_cursed].set_cursed(True)

        # give out initial perks
        shuffled_ids = self.player_ids.copy()
        rand.shuffle(shuffled_ids)
        perks_to_give = FIRST_ROUND_PERKS.copy()
        perks_given = []
        weights = [x for i, x in enumerate(PERK_WEIGHTS) if PERKS[i] in FIRST_ROUND_PERKS]
        
        for id in shuffled_ids:
            drawn_perk = rand.choices(perks_to_give, weights=weights)[0]
            if drawn_perk in UNIQUE_PERKS or perks_given.count(drawn_perk) > int(self.num_players/3):
                perks_to_give.remove(drawn_perk)

            self.players[id].give_perk(drawn_perk)
            perks_given.append(drawn_perk)

        self.points = {
            'points' : {i : 0 for i in self.player_ids},
            'bonus_points' : {i : 0 for i in self.player_ids}
        }

    def get_current_perks(self):
        perks = []
        for id in self.player_ids:
            perks.append(self.players[id].get_perks())
        return perks
    
    def get_private_state(self, player_id):
        return self.players[player_id].get_private_state()

    def process_night_actions(self, actions):
        """
        Presumed format of 'actions':
        { 0 :   {
            'action' : str (or None),
            'targets : [target_1, target_2] (len implies num targets)
                },
          1 :   {
        ... (for each player)
        ]

        The index of the action in the list implies the player.

        Returns a dict of the following format:
        { 
            0 : [messages to go to notifications],
            1 : ""
            ...
            frozen : player_id
        }
        """
        # add checking here - shouldn't be necessary but probably best for safety.

        for player_id in actions:
            if actions[player_id]['action'] is None:
                actions[player_id]['action'] = 'None'
            
            actions[player_id].update(self.players[player_id].get_relevant_night_information)

        night_results = parse(actions)
        new_messages = {}
        for player_id in night_results:
            new_messages.update({player_id : self.players[player_id].parse_night_response(night_results[player_id])})

        return new_messages
    