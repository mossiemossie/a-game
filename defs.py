"""
Structure:

agame.py - contains Gamemaster object - central controller for game logic.
Contains logic for day and day perks, and logic for night

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


This file should eventually be a central source for global variables, because i'm a piece of shit.

"""