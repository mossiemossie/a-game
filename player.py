# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 08:42:08 2026

@author: lachl
"""
from perks import Kill, Watch, Vigil, Track, Distract, Shield, Selfish, Gaze, \
    Telepathy, Narcissist, Static, Forgery, Pact, Vindictive, Bounty, \
        Relentless, Triangulate
    
import random as rand

from defs import PERKS, PERK_WEIGHTS, UNIQUE_PERKS, VISIT_PERKS, FIRST_ROUND_PERKS

from player_gui import PlayerWindow
from PyQt6.QtWidgets import QApplication
import sys




class Player:
    def __init__(self, identity, num_players):
        """
        Init class for the given player.

        Parameters
        ----------
        identity : int
            The identity of this player.
        num_players : TYPE 
            The number of players in the game.

        """
        # Define player parameters
        self.identity = identity
        self.alive = True
        self.killer = False
        self.num_players = num_players
        
        # define all perks
        self.load_perks(identity, num_players)
        
        # perks the player has
        self.perks = ['watch']
        # actions the player can make
        self.actions = ['watch']

        app = QApplication(sys.argv)
        window = PlayerWindow()
        window.show()
        sys.exit(app.exec()) 
        
        
    def load_perks(self, identity, num_players):
        # This might not be the prettiest way of doing this; BUT.
        # it's way easier to do this than it is to jump through hoops 
        # to get a perk object from a string and etc.
        self.kill = Kill(identity, num_players)
        self.watch = Watch(identity, num_players)
        self.vigil = Vigil(identity, num_players)
        self.track = Track(identity, num_players)
        self.distract = Distract(identity, num_players)
        self.shield = Shield(identity, num_players)
        self.selfish = Selfish(identity, num_players)
        self.gaze = Gaze(identity, num_players)
        self.telepathy = Telepathy(identity, num_players)
        self.narcissist = Narcissist(identity, num_players)
        self.static = Static(identity, num_players)
        self.forgery = Forgery(identity, num_players)
        self.pact = Pact(identity, num_players)
        self.vindictive = Vindictive(identity, num_players)
        self.bounty = Bounty(identity, num_players)
        self.relentless = Relentless(identity, num_players)
        self.triangulate = Triangulate(identity, num_players)
        
        self.str_to_perk = {
            'kill'          : self.kill,
            'watch'         : self.watch,
            'vigil'         : self.vigil,
            'track'         : self.track,
            'distract'      : self.distract,
            'shield'        : self.shield,
            'selfish'       : self.selfish,
            'gaze'          : self.gaze,
            'telepathy'     : self.telepathy,
            'narcissist'    : self.narcissist,
            'static'        : self.static,
            'forgery'       : self.forgery,
            'pact'          : self.pact,
            'vindictive'    : self.vindictive,
            'bounty'        : self.bounty,
            'relentless'    : self.relentless,
            'triangulate'   : self.triangulate
        }
        
        
    def give_perk(self, perk_names):
        """
        Function used in game master to give this player perks. Returns the perk
        that was chosen by the player.

        Parameters
        ----------
        perk_names : list(string)
            List of perks the player can select.

        Returns
        -------
        (string) the player's selected perk.

        """
        if len(perk_names) > 1:
            as_string = self.perk_list_to_string(perk_names)
            selected = input(f'Select a perk: {as_string}')
            
            while selected not in perk_names:
                selected = input(f'Invalid perk name. Select one of {as_string}')
                
        else:
            selected = perk_names[0]
            
        # give the perk
        self.perks.append(selected)
        if not self.str_to_perk[selected].passive:
            self.actions.append(selected)
            
        if selected == 'pact':
            print(f'{self.identity}: You have a pact with {self.pact.target}.')
        elif selected == 'vindictive':
            print(f'{self.identity}: You are vindictive towards {self.vindictive.target}.')
            
        return selected
    
    
    def tell_player_their_perks(self):
        self.send_message(f'Your perks are {self.perk_list_to_string(self.perks, delineator = "and")}.')
        
        
    def perk_list_to_string(self, perk_list, delineator = 'or'):
        delineator = delineator[::-1] + ' '
        
        if len(perk_list) == 1:
            return str(perk_list[0])
        else:
            s = ", ".join(perk_list)
            s = s[::-1].replace(',', delineator, 1)[::-1] #swap last ',' for 'and'
            return s
                    

    def set_killer(self, status):
        """
        Sets this player as the killer/not the killer.

        Parameters
        ----------
        status : Boolean
            Whether this player is the killer.
        """
        self.killer = status
        

    def set_alive(self, status):
        """
        Sets this player as alive/dead.

        Parameters
        ----------
        status : Boolean
            Whether this player is alive.
        """
        self.alive = status


    def make_action(self):
        """
        Parses the types of actions the player is able to make, prompts them
        for their choice and returns the result.

        Returns
        -------
        list[String, int, int]
            First item -> the name of the action being taken
            Second item -> the first target, or None if no target
            Third item -> the second target, or None if no target
        """
        
        if self.killer:
            return self.kill.make_move()
        
        print(f'{self.identity}: Select an action from the following: ')
        for a in self.actions:
            if self.str_to_perk[a].charges is None:
                print(a)
            else:
                print(f'{a} (Charges remaining: {self.str_to_perk[a].charges})')

        action = input()
        def check_valid_action(action):
            valid_action = action in self.actions
            if valid_action:
                valid_action = self.str_to_perk[action].charges != 0
            return valid_action

        while not check_valid_action(action): 
            action = input(f'{self.identity}: Please type a valid action: ')

        action = self.str_to_perk[action]
        return action.make_move()
            

    def send_message(self, result):
        """
        Prints messages from GameMaster about the results of the players night
        actions.
        """
        print(f'{self.identity}: {result}')
    
    
    def send_day_response(self):
        """
        Get votes from players, and the existence of any day-related perks. 

        Theoretically, the day-related perks bit could be handled in game-master, but I'd prefer not to, because 
            a.) game-master risks getting bloated if we just make it handle everything, and it's a small enough amount
                of data to send between objects that though this does some a lot of duplicated work, that 
                particular trade-off is reasonable when we're talking about doing it what, 100 times?
            b.) this allows us to handle the remaining days element herein and stops game-master from having to access
                perk variables through player variables, which isn't pretty at all.
        """
        voted_player = int(input(f'{self.identity}: Vote for who you think is the killer: '))
        while voted_player not in range(1, self.num_players+1): #need to stop people voting themselves
            voted_player = int(input(f'{self.identity}: Invalid input: '))
        
        pact_target = None
        if 'pact' in self.perks and self.pact.remaining_days > 0:
            pact_target = self.pact.target
                
        vindictive_target = None
        if 'vindictive' in self.perks and self.vindictive.remaining_days > 0:
            vindictive_target = self.vindictive.target

        return {
            'vote'              : voted_player, 
            'pact_target'       : pact_target, 
            'vindictive_target' : vindictive_target,
            'selfish'           : 'selfish' in self.perks,
            'narcissist'        : 'narcissist' in self.perks,
            'bounty_target'     : self.bounty.target if ('bounty' in self.perks and self.bounty.remaining_days > 0) else None,
            'bounty_days'       : self.bounty.remaining_days if 'bounty' in self.perks else None
        }
    
    
    def get_response(self, response):
        """
        Receive a response from game master about the results of the previous
        action.
        """
        if response.killed:
            print(f"{self.identity}: You were killed.")
            self.set_alive(False)
        for m in response.messages:
            print(f"{self.identity}: {m}")
        self.str_to_perk[response.action].print_result(response)

        if response.action == 'bounty':
            self.bounty.activated = True
            self.bounty.target = response.target_1
        
        
    def day_has_passed(self):
        for perk_name in ['pact', 'vindictive']:
            if perk_name in self.perks:
                if self.str_to_perk[perk_name].remaining_days > 0:
                    self.str_to_perk[perk_name].remaining_days -= 1
        
        if 'bounty' in self.perks and self.bounty.activated and self.bounty.remaining_days > 0:
            self.bounty.remaining_days -= 1
    

    def __str__(self):
        return 'Unimplemented'
    
    
class ResponseNight:
    def __init__(self):
        """
        Struct-like class; breaking some rules of OOP here but this is just
        so I have a single place to register data to send back to players
        that can be updated in the main game loop if and when it needs to.
        
        One response per night phase per player.
        
        self.action - the chosen action the player took tonight
        self.messages - any extra messages that should be sent to the player;
            the default message that their action gives them (i.e. you killed 3)
            isn't included and should be handled in here/perks.py
        self.success - if the action was successful
        self.unsuccessful_reason - the reason the action was unsuccessful
        self.killed - if the player was killed tonight
        self.result - the result of any action the player took (can be multiple
            types depending on the action and should be parsed in perks.py prolly),
            or the reason the action was unsuccessful if it was.
        """
        self.action = None
        self.target_1 = None
        self.target_2 = None
        self.messages = []
        self.success = True
        self.killed = False
        self.result = None
        
    def set_action(self, action):
        self.action = action
        
    def set_targets(self, target_1, target_2):
        self.target_1 = target_1
        self.target_2 = target_2
        
    def add_message(self, message):
        self.messages.append(message)
        
    def unsuccessful(self, reason):
        self.success = False
        self.result = reason
        
    def was_killed(self):
        self.killed = True
        
    def set_result(self, result):
        self.result = result
        
    def __str__(self):
        return f'Action = {self.action}, successful = {self.success}, messages = {self.messages}, killed = {self.killed}, result = {self.result}'