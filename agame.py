# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 11:22:52 2026

@author: lachl
"""

"""
todos:
    
"""

from player import Player, ResponseNight
from defs import PERKS, PERK_WEIGHTS, UNIQUE_PERKS, VISIT_PERKS, FIRST_ROUND_PERKS

import pandas as pd
import random as rand
from itertools import chain
import sys
from night_abilities import distract, shield_and_kill, gaze, visit_abilities

# to-dos
#           - need to go through and make sure perks that are implemented are actually implemented everywhere
#           - loads of perks to implement
#           - actual UI


class GameMaster:
    def __init__(self, num_players):
        # init players & killer
        self.num_players = num_players
        self.players = {i : Player(i, num_players) for i in range(1, num_players + 1)} 
        self.current_killer = rand.randint(1, num_players)
        self.players[self.current_killer].set_killer(True)
        self.players_perks = {i : [] for i in range(1, num_players + 1)}
        
        self.give_perks(1, first_round = True)
        
        # set up point scoring
        self.points_df = pd.DataFrame([[0.0, 0.0] for i in range(1, num_players + 1)])
        self.points_df.columns = ['Points', 'Bonus Points']
        self.points_df.index += 1
        
        for time_phase in range(0, 9):
            if time_phase in [3, 6]:
                self.give_perks(2)
            killed_player = self.night_phase(time_phase)
            self.day_phase(killed_player, time_phase)
        
        
        """---------------------
            DAY/NIGHT PHASES
        ---------------------"""
        
    
    def night_phase(self, time_phase):
        self.broadcast(f'Night {time_phase}.')
        # not storing as self as this should have no utility outside of the night phase
        responses = {i : ResponseNight() for i in self.players}  
        actions = self.get_actions_made()
        
        # set the responses variables pertaining to actions here
        for i in responses:
            responses[i].set_action(actions.loc[i, 'action'])
            responses[i].set_targets(actions.loc[i, 'target_1'], actions.loc[i, 'target_2'])
        
        # deal with stuff that alters the fundamental actions,
        # distracts
        actions, responses = distract(actions, responses)
        # next, kill/shield abilities
        responses, killed_player = shield_and_kill(actions, responses)
        # social abilities
        responses = gaze(actions, responses)
        # visitation related abilities; a few of these exist, so bundled into one function
        responses = visit_abilities(actions, responses)
        # send out responses
        for i in self.players:
            self.players[i].get_response(responses[i])
        
        return killed_player
    

    def day_phase(self, killed_player, time_phase):
        self.broadcast(f'Day {time_phase + 1}.')
        if killed_player is not None:
            self.broadcast(f'{killed_player} was killed.')
        else:
            self.broadcast("No-one was killed.")
        responses = {i : self.players[i].send_day_response() for i in self.players if i != killed_player}
        responses = pd.DataFrame(responses).T

        bounty_exists = False
        if responses[~responses['bounty_target'].isna()].shape[0] > 0:
            #bounty logic.
            bounty_exists = True
            bounty_params = responses[~responses['bounty_target'].isna()][['bounty_target', 'bounty_days']]
            bounty_setter = bounty_params.index[0]
            bounty_target = bounty_params['bounty_target'].loc[bounty_setter]
            bounty_days = bounty_params['bounty_days'].loc[bounty_setter]
        
        # give points to anyone who voted for the killer
        correct_voters = responses[responses['vote'] == self.current_killer].index
        self.points_df.loc[correct_voters, 'Points'] += 1

        # give bonus points to any narcissists
        votes_per_narcissist = responses[responses['vote'].isin(responses[responses['narcissist']].index)].groupby('vote').size()
        self.points_df.loc[votes_per_narcissist.index, 'Bonus Points'] += votes_per_narcissist/2
         
        # figure out who was voted for, or handle if it was no-one
        vote_past_threshold = responses.groupby('vote').size() >= self.num_players/2
        vote_past_threshold = vote_past_threshold[vote_past_threshold]
        
        if len(vote_past_threshold) == 0:
            voted_player = -1
            self.broadcast('Not enough votes for one player.')
        elif len(vote_past_threshold) == 2:
            voted_player = -1
            self.broadcast('Votes split.')
        else:
            voted_player = vote_past_threshold.index[0]
        
        # if it's the second day of the bounty, give points where req'd.
        if bounty_exists and bounty_days == 1:
            if killed_player == bounty_target:
                self.broadcast(f'Bounty target {bounty_target} was killed; killer and bounty setter get 2 bonus points.')
                self.points_df.loc[[bounty_setter, self.current_killer], 'Bonus Points'] += 2
            elif voted_player == bounty_target:
                self.broadcast(f'Bounty target {bounty_target} was voted for; bounty setter gets 1 bonus point.')
                self.points_df.loc[bounty_setter, 'Bonus Points'] += 1
            else:
                self.broadcast(f'Bounty not completed; bounty setter loses 1 bonus point.')
                self.points_df.loc[bounty_setter, 'Bonus Points'] -= 1

        # if the killer wasn't found, give points to killer and bonus points to selfish
        if voted_player != self.current_killer:
            if voted_player > 0:
                self.broadcast(f'{voted_player} was not the killer.')
            
            # give points to killer and bonus points to selfish.
            self.points_df.loc[self.current_killer, 'Points'] += 1
            
            selfish = responses[responses['selfish']].index
            self.points_df.loc[selfish, 'Bonus Points'] += responses.loc[selfish, 'vote'] == self.current_killer
        
        # if the killer was found, change killer
        else:
            self.broadcast(f'{voted_player} was the killer.') 
            self.players[self.current_killer].set_killer(False)
            self.current_killer = rand.randint(1, self.num_players)
            self.players[self.current_killer].set_killer(True)
            
        if killed_player is not None:
            self.players[killed_player].set_alive(True)
            self.broadcast(f'{killed_player} has been exhumed.')

        if bounty_exists and bounty_days == 2:
            self.broadcast(f'Bounty set on {bounty_target}. Killer & bounty setter will gain 2 bonus points if they are killed. Bounty setter will gain 1 bonus point if they are voted out tomorrow.')

        # iterate days_remaining on any relevant perks
        for p in self.players:
            self.players[p].day_has_passed()
        
        self.broadcast(f'End of day {time_phase + 1}')        
            
            
    def get_actions_made(self):
        action_data = {}
        for i in self.players:
            action_data.update(
                {i : self.players[i].perks + [None] * (3 - len(self.players[i].perks)) + self.players[i].make_action()}
            )
            
        actions = pd.DataFrame(action_data, index = ['perk1', 'perk2', 'perk3', 'action', 'target_1', 'target_2']).T
        return actions
    
    
    def give_perks(self, num_perks_each, first_round = False):
        """
        Get a random perk from the list of perks. Will not return perks that
        are unique and have already been given out, or that the player already
        has.

        Parameters
        ----------
        num_perks : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        master_perk_list = FIRST_ROUND_PERKS if first_round else PERKS

        # get a list of perks that are eligible to give out (all perks - unique perks that are currently being held)
        current_perks = list(chain.from_iterable(self.players_perks.values()))
        banned_perks = [x for x in current_perks if (x in UNIQUE_PERKS) or (current_perks.count(x) > int(self.num_players/3))]
        one_from_ban = UNIQUE_PERKS + [x for x in master_perk_list if current_perks.count(x) == int(self.num_players/3) - 1]
        globally_eligible_perks = [x for x in master_perk_list if x not in banned_perks]
        result = [None] * self.num_players
        
        # randomly select a player
        players = list(range(1, self.num_players + 1))
        rand.shuffle(players)
        
        for p in players:
            # grab two eligible perks
            eligible_perks = [x for x in globally_eligible_perks if x not in self.players_perks[p]]
            perks_to_give = self.draw_perks(eligible_perks, num_perks_each)
            result[p-1] = perks_to_give
            
            # redefine ineligible perks
            new_bans = [x for x in perks_to_give if x in one_from_ban]
            banned_perks += new_bans
            globally_eligible_perks = [x for x in master_perk_list if x not in banned_perks]
    
        # give the players their perks
        for i in players:
            given_perk = self.players[i].give_perk(result[i-1])
            self.players_perks[i].append(given_perk)
            self.players[i].tell_player_their_perks()
        
    
    def draw_perks(self, eligible, n):
        """
        Helper function to draw n distinct eligible perks, based on weights.

        Parameters
        ----------
        eligible : list(string)
            The list of eligible perks
        n : int
            The number of perks to draw

        Returns
        -------
        perks : list(string)
            A list of len n with the perks.

        """
        perks = []
        num_drawn = 0
        while num_drawn < n:
            eligible_idxs = [i for i, x in enumerate(PERKS) if x in eligible]
            eligible_weights = [x for i, x in enumerate(PERK_WEIGHTS) if i in eligible_idxs]
            drawn_perk = rand.choices(eligible, weights=eligible_weights)[0]
            perks.append(drawn_perk)
            eligible = [x for x in eligible if x != drawn_perk]
            num_drawn += 1
            
        return perks
        
    
    def broadcast(self, message):
        """
        Broadcast a message to all players.

        Parameters
        ----------
        message : Str
            The message to be broadcast.
        """
        for i in self.players:
            self.players[i].send_message(message)
            

if __name__ == "__main__":
    print('Hello!')
    GameMaster(4)