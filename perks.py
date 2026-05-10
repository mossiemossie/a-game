# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 13:44:26 2026

@author: lachl
"""

import random as rand


def list_to_string(target_list):
    if len(target_list) == 0:
        return 'No-one'
    elif len(target_list) == 1:
        return str(target_list[0])
    else:
        target_list = [str(x) for x in target_list]
        s = ", ".join(target_list)
        s = s[::-1].replace(',', 'dna ', 1)[::-1] #swap last ',' for 'and'
        return s

class Perk:
    def __init__(self, identity, num_players):
        """
        Init master class for perks. 
        By default, perks: 
            - have no targets or qualifiers, 
            - are not passives
            - cannot have target_1 be themselves
            - have self.charges = None (-> infinite charges)

        Parameters
        ----------
        identity : int
            The identity of the player using the perk; necessary to define banned targets.
        num_players : TYPE
            The number of players in the game.

        """
        self.identity = identity
        self.num_players = num_players
        self.has_target_1 = False
        self.verb_present_target_1 = None
        self.verb_past_target_1 = None
        self.has_target_2 = False
        self.verb_present_target_2 = None
        self.verb_past_target_2 = None
        self.banned_target_1 = [identity]
        self.banned_target_2 = []
        self.targets_must_be_distinct = False
        self.passive = False
        self.charges = None
        self.remaining_days = None
        self.activated = False #whether or not the perk has been activated by the user - at this point just for bounty
                                # this stops the situation where the bounty only gets activated on days 2,5,8
        
    def make_move(self):
        """
        Get the target of the perk from the user and return the perk name, target_1 and target_2.

        Returns
        -------
        list
            [Perk name, target_1, target_2]

        """
        if self.has_target_1:
            target_1 = self.query_user(self.verb_present_target_1, self.banned_target_1)
            if self.targets_must_be_distinct:
                self.banned_target_2.append(target_1)
        else:
            target_1 = None
        if self.has_target_2:
            target_2 = self.query_user(self.verb_present_target_2, self.banned_target_2)
            if self.targets_must_be_distinct:
                self.banned_target_2.remove(target_1)
        else:
            target_2 = None
            
        if self.charges is not None:
            self.charges -= 1
            
        return [self.__repr__(), target_1, target_2]
            
        return
            
    def query_user(self, verb, banned):
        """
        Query the user directly for the target.

        Parameters
        ----------
        verb : String
            How to describe the action to the user.
        banned : List(int)
            List of players that cannot be targeted by the action.

        Returns
        -------
        target : int
            The player to be targeted by the action.

        """
        possible_targets = [i for i in range(1, self.num_players + 1) if i not in banned]
        target = int(input(f'{self.identity}: Select target to {verb}: '))
        while target not in possible_targets:
            target = int(input(f'{self.identity}: Target not possible: '))
        
        return target
    
    def print_result(self, result):
        if result.success:
            if not self.has_target_1: # no targets
                print(f'{self.identity}: You {self.__str__()}ed.')
            elif not self.has_target_2: # only target 1
                print(f'{self.identity}: You {self.verb_past_target_1} {result.target_1}.')
            else:                       # target 1 and target 2.
                print(f'{self.identity}: You {self.verb_past_target_1} {result.target_1} {self.verb_past_target_2} {result.target_2}.')
        else:
            if not self.has_target_1:
                print(f'{self.identity}: You attempted to {self.__str__()}, but {result.result}.')
            elif not self.has_target_2:
                print(f'{self.identity}: You attempted to {self.verb_present_target_1} {result.target_1}, but {result.result}.')
            else:
                print(f'{self.identity}: You attempted to {self.verb_present_target_1} {result.target_1} {self.verb_past_target_2}, but {result.result}.')
        
            
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return 'perk'
    

class Kill(Perk):
    def __init__(self, identity, num_players):
        """
        Kill perk.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.verb_present_target_1 = 'kill'
        self.verb_past_target_1 = 'killed'
        
    def __str__(self):
        return 'kill'
        

class Watch(Perk):
    def __init__(self, identity, num_players):
        """
        Watch perk.
        
        Remain in place; you have a 1 in 3 chance of learning who visited you.
        Default perk, available to all players no matter what.
        """
        super().__init__(identity, num_players)
        self.odds = 1
        
    def make_move(self):
        """
        Can't remember why I did this. Oh yeah it's because it's an action 
        with no targets and the standard logic isn't set up for that.

        Returns
        -------
            ['watch', None, None]
        """
        return ['watch', None, None]
    
    def print_result(self, result):
        super().print_result(result)
        if result.success:
            print(f'{self.identity}: {list_to_string(result.result)} visited you.')

    def __str__(self):
        return 'watch'
    

class Vigil(Perk):
    def __init__(self, identity, num_players):
        """
        Vigil perk.
        
        See who visits your target_1.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.verb_present_target_1 = 'watch over'
        self.verb_past_target_1 = 'watched over'
        self.charges = 2
        
    def print_result(self, result):
        super().print_result(result)
        if result.success:
            print(f'{self.identity}: {list_to_string(result.result)} visited {result.target_1}.')
        
    def __str__(self):
        return 'vigil'
    
    
class Track(Perk):
    def __init__(self, identity, num_players):
        """
        Track perk.
        
        See who your target_1 visits. Counts as a visit.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.verb_present_target_1 = 'track'
        self.verb_past_target_1 = 'tracked'
        self.charges = 2
        
    def print_result(self, result):
        super().print_result(result)
        if result.success:
            print(f'{self.identity}: {result.target_1} visited {list_to_string(result.result)}.')
        
    def __str__(self):
        return 'track'
        
        
class Distract(Perk):
    def __init__(self, identity, num_players):
        """
        Distract perk.
        
        Force your target_1 to target your target_2 with their ability. 
        Unique.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.verb_present_target_1 = 'redirect'
        self.verb_past_target_1 = 'redirected'
        self.has_target_2 = True
        self.verb_present_target_2 = 'direct to'
        self.verb_past_target_2 = 'to target'
        self.targets_must_be_distinct = True
        self.charges = 3
        
    def __str__(self):
        return 'distract'


class Shield(Perk):
    def __init__(self, identity, num_players):
        """
        Shield perk.
        
        If your target_1 is attacked tonight, they will not be killed.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.verb_present_target_1 = 'shield'
        self.verb_past_target_1 = 'shielded'
        self.charges = 5
        
    def __str__(self):
        return 'shield'
    
    
class Selfish(Perk):
    def __init__(self, identity, num_players):
        """
        Selfish perk.

        If you vote for the killer but they are not found, receive a bonus
        point. Passive.
        """
        super().__init__(identity, num_players)
        self.passive = True
        
    def __str__(self):
        return 'selfish'
        

class Gaze(Perk):
    def __init__(self, identity, num_players):
        """
        Gaze perk
        
        Pick a player; discover their perks. Has two charges.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True 
        self.verb_present_target_1 = 'gaze upon'
        self.verb_past_target_1 = 'gazed upon'
        self.charges = 1
        
    def print_result(self, result):
        super().print_result(result)
        if result.success:
            print(f'{self.identity}: {result.target_1} has the perks {list_to_string(result.result)}.')
        
    def __str__(self):
        return 'gaze'
        
    
class Telepathy(Perk):
    def __init__(self, identity, num_players):
        """
        Telepathy perk

        Pick a player; they will be told who visits you at night.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.verb_present_target_1 = 'communicate to'
        self.verb_past_target_1 = 'communicated to'
        self.charges = 3
        
    def __str__(self):
        return 'telepathy'
    
    
class Narcissist(Perk):
    def __init__(self, identity, num_players):
        """
        Narcissist perk
        
        Get half a bonus point for each time someone votes for you.
        """
        super().__init__(identity, num_players)
        self.passive = True
        
    def __str__(self):
        return 'narcissist'

# ---- these aren't implemented yet ----
    
class Static(Perk):
    def __init__(self, identity, num_players):
        """
        Static perk

        Perks targeting you have a 1 in 4 chance of returning false information.
        """
        super().__init__(identity, num_players)
        self.passive = True
        
    def __str__(self):
        return 'static'
    
    
class Forgery(Perk):
    def __init__(self, identity, num_players):
        """
        Forgery perk

        Select two targets; if target 1 uses an investigative ability, they
        will be told that target 2 was the perpetrator. Bypasses the luck
        check for watch.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.verb_present_target_1 = 'mislead'
        self.verb_past_target_1 = 'misled'
        self.has_target_2 = True
        self.verb_present_target_2 = 'frame'
        self.verb_past_target_2 = 'into seeing'
        self.targets_must_be_distinct = True
        self.charges = 2
        
    def __str__(self):
        return 'forgery'
        
        
class Pact(Perk):
    def __init__(self, identity, num_players):
        """
        Pact perk
        
        For three days, gain a bonus point if [randomly selected player] is
        not voted out. Lose a bonus point if they are.
        """
        super().__init__(identity, num_players)
        self.target = [x for x in range(1, num_players+1) if x != identity][rand.randint(0, num_players - 2)]
        self.passive = True
        self.remaining_days = 3
        
    def __str__(self):
        return 'pact'
        
        
class Vindictive(Perk):
    def __init__(self, identity, num_players):
        """
        Vindictive perk
        
        For three days, gain a bonus point if [randomly selected player] is 
        voted out. Lose a bonus point if by the third the player hasn't been 
        voted out.
        """
        super().__init__(identity, num_players)
        self.target = [x for x in range(1, num_players+1) if x != identity][rand.randint(0, num_players - 2)]
        self.passive = True
        self.remaining_days = 3
        
    def __str__(self):
        return 'vindictive'
    
class Paranoid(Perk):
    def __init__(self, identity, num_players):
        """
        Paranoid perk

        If you are observed at night, you are notified of who observed you.

        Note: this seems crazy powerful? nerf it
        """
        super().__init__(identity, num_players)
        self.passive = True
    
    def __str__(self):
        return 'paranoid'
        
        
class Bounty(Perk):
    def __init__(self, identity, num_players):
        """
        Bounty perk
        
        Publically set a bounty on a random player. If they are killed within a day,
        you and the killer both get 2 bonus points. If they are voted out within a day,
        you get a bonus poin. If they are not killed or voted out, you lose one bonus point.
        """
        super().__init__(identity, num_players)
        self.target = None
        self.has_target_1 = True
        self.banned_target_1 = []
        self.verb_past_target_1 = 'set a bounty on'
        self.verb_present_target_1 = 'set a bounty on'
        self.remaining_days = 2 # as a scummy workaround, 2 = 1 day left, 1 = timer ran out and 0 = perk isn't really active anymore. Could and should probably implement this better
        self.activated = False
        self.charges = 1

    def __str__(self):
        return 'bounty'

        
class Relentless(Perk):
    def __init__(self, identity, num_players):
        """
        Relentless perk
        
        Kills bypass shield.
        """
        super().__init__(identity, num_players)
        self.passive = True 

    def __str__(self):
        return 'relentless'
        
        

class Peer(Perk):
    def __init__(self, identity, num_players):
        """
        Peer perk
        
        Choose a player; if they are not the killer, you have a 1 in 2 chance
        of confirming that they are not the killer. 
        """
        super().__init__(identity, num_players)

    def __str__(self):
        return 'peer'


class Compel(Perk):
    def __init__(self, identity, num_players):
        """
        Compel perk
        
        Force a player to target you with their ability.
        how will this interact with distract? i feel as though this should
        be over-ridden by distract.
        """
        super().__init__(identity, num_players)
    
    def __str__(self):
        return 'compel'


class Nosey(Perk):
    def __init__(self, identity, num_players):
        """
        Nosey perk
        
        Choose a target; read all whispers to and from that player in the next
        day phase.
        """
        super().__init__(identity, num_players)

    def __str__(self):
        return 'nosey'
        

class Triangulate(Perk): 
    def __init__(self, identity, num_players):
        """
        Triangulate perk (definitely come up with a better name)

        Choose two targets; learn if a visitation occurred between those two
        targets. 
        
        Note: The idea is to have some sort of investigative perk that I can
        give loads of charges to because it's not that powerful/is difficult to
        use effectively. If I can come up with more of these it's probably a 
        good thing.
        """
        super().__init__(identity, num_players)
        self.has_target_1 = True
        self.banned_target_1 = []
        self.verb_past_target_1 = 'watched'
        self.verb_present_target_1 = 'watch'
        self.has_target_2 = True
        self.banned_target_2 = []
        self.verb_past_target_2 = 'and'
        self.verb_present_target_2 = 'watch'
        self.targets_must_be_distinct = True

    def print_result(self, result):
        super().print_result(result)
        if result.success:
            print(f'{self.identity}: {"A" if result.result else "No"} visit occurred between {result.target_1} and {result.target_2}.')

    def __str__(self):
        return 'triangulate'
        
