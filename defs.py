"""
To-dos:
- make sure names are unique
- get the name and player_id linked in the chat
- once stuff is working to a reasonable degree, i DEFINITELY need to go through and 
    spend a decent amount of time cleaning shit up.
- make the numbers start at 1 because people don't start from 0 irl like computers do.
- make it so that if you don't elect to freeze someone, you freeze a random player.
Structure:

agame.py - [DEPRECATED] contains Gamemaster object - central controller for game logic.
Contains logic for day and day perks, and logic for night

gamemaster.py - replacement for agame.py, since much of the logic in agame.py is centered around text-based interaction.

night_abilities.py - contains functions w/ logic for night abilities

player.py - contains Player and NightResponse objects
    Player object - centralizes player-based regarding interacting w/ player
        and also giving and using perks.
    NightResponse objects - basically a struct for telling the player object
        what happened last night, from night_abilities/agame.

perks.py - contains Perk parent object and all Perk objects.
    Note, the perk objects don't contain the logic of how they are used in the game,
        just how they are allowed to be used by players. The perk name is passed by
        the player up to the Gamemaster object, which then parses what the perk actually
        does in the context of the game.

        
To fully implement a perk, it needs:
- to be defined as a lower case string in the global variables herein (PERKS at least, and any others that may be relevant)
- to have its logic defined somewhere in agame.py or night_abilities.py (depending)
- to have a perk object defined in perks.py, with a __str__ function which matches to its definition in this file
- to be imported in player.py
- to be loaded in player.py under Player.load_perks().


This file is a global source for certain global static variables.

"""

# All available perks
PERKS = ['vigil', 'track', 'compel', 'shield', 'selfish', 'gaze', 
         'telepathy', 'narcissism', 'static', 'forger', 'pact', 'vindictive', 
         'bounty', 'relentless', 'peer', 'infer']

# Weights of each given perk; currently just set to 1.
PERK_WEIGHTS = [1] * len(PERKS)

# All perks that can be selected in the first round
FIRST_ROUND_PERKS = ['vigil', 'track', 'shield', 'telepathy', 'bounty', 'peer',
                     'infer']

# All perks that are unique (only one player can have these perks)
UNIQUE_PERKS = ['compel', 'forger']

# All perks that count as visitations
VISIT_PERKS = ['kill', 'track', 'vigil', 'shield', 'gaze']

