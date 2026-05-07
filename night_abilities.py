# -*- coding: utf-8 -*-
"""
Created on Sun May  3 17:37:29 2026

@author: lachl
"""

VISITS = ['kill', 'track', 'shield']
PERKS = ['vigil', 'track', 'distract', 'shield', 'selfish', 'gaze', 'telepathy'
         , 'narcissist', 'static', 'forgery', 'pact', 'vindictive']
PERK_WEIGHTS = [1] * len(PERKS)

# helper functions; returns true if the target has the static perk and passes the luck check
is_static = lambda df, t : 'static' in list(df.loc[t, ['perk1', 'perk2', 'perk3']]) and rand.randint(0, 3) == 0
select_non_static = lambda np, t : [x for x in range(1,np+1) if x != t][rand.randint(0, np-2)]

import random as rand


def visit_abilities(actions, responses):
    # get the visits
    visits = parse_visits(actions)
    
    # get any forgeries
    # at some point, alter the forgeries response var too
    forgeries = actions[actions['action'] == 'forgery']
    if forgeries.shape[0] == 0:
        forgeries = None
    else:
        forgeries = forgeries.reset_index(drop=True).iloc[0] 
    
    # set the responses 
    responses = watch(actions, visits, responses, forgeries)
    responses = vigil(actions, visits, responses, forgeries)
    responses = track(actions, visits, responses, forgeries)
    responses = telepathy(actions, visits, responses, forgeries)
    
    return responses

    
def watch(actions, visits, responses, forgeries):
    watchers = actions[actions['action'] == 'watch'].index
    
    for w in watchers:
        if forgeries is not None:
            if forgeries['target_1'] == w:
                responses[w].set_result([forgeries['target_2']])
        elif rand.randint(0, 2) > 0: #unsuccessful
            responses[w].unsuccessful("couldn't make out who may have visited you, if anyone")
        else:
            visitors = get_visitors_to(actions, visits, w)
            visitors = swap_if_forged(w, visitors, forgeries)
            responses[w].set_result(visitors)
            
    return responses

            
def vigil(actions, visits, responses, forgeries):
    vigils = actions[actions['action'] == 'vigil'].index  
    
    for v in vigils:
        visitors = get_visitors_to(actions, visits, actions.loc[v, 'target_1'])
        visitors = swap_if_forged(v, visitors, forgeries)
        responses[v].set_result(visitors)
        
    return responses


def track(actions, visits, responses, forgeries):
    tracks = actions[actions['action'] == 'track'].index 
    
    for t in tracks:
        visited = get_visited(actions, visits, actions.loc[t, 'target_1'])
        visited = swap_if_forged(t, visited, forgeries)
        responses[t].set_result(visited)
        
    return responses


def telepathy(actions, visits, responses, forgeries):
    telepathies = actions[actions['action'] == 'telepathy'].index 
    
    for t in telepathies:
        visitors = get_visitors_to(actions, visits, t)
        visitors = swap_if_forged(t, visitors, forgeries)
        visitors = list_to_string(visitors)
        responses[actions.loc[t, 'target_1']].add_message(f'{visitors} visited {t} tonight.')
        
    return responses


def gaze(actions, responses):
    gazers = actions[actions['action'] == 'gaze'].index
    for g in gazers:
        target = actions.loc[g, 'target_1']
        target_perks = [x for x in list(actions.loc[target, ['perk1', 'perk2', 'perk3']]) if x is not None]
        
        # check for static
        if is_static(actions, target):
            num_target_perks = len(target_perks)
            target_perks = draw_perks(PERKS, num_target_perks)
            
        target_perks = list_to_string(target_perks)
        responses[g].set_result(target_perks)
        
    return responses
    
def shield_and_kill(actions, responses):
    #shields = list(set(list(actions[actions['action'] == 'shield']['target_1'])))
    shields = actions[actions['action'] == 'shield']['target_1']
    killed_player = actions[actions['action'] == 'kill']['target_1'].iloc[0]
    current_killer = actions[actions['action'] == 'kill'].index[0] #pretty shitty workaround? maybe? probably a bug waiting to happen

    if killed_player in list(shields):
        if 'relentless' in list(actions.loc[current_killer, ['perk1', 'perk2', 'perk3']]):
            responses[killed_player].was_killed()            
        else:   
            responses[killed_player].add_message('You were attacked, but shielded.')
            responses[current_killer].unsuccessful('they were shielded')
            killed_player = None
        
    else:
        responses[killed_player].was_killed()
        
    return responses, killed_player
    
def distract(actions, responses):
    distractor = actions[actions['action'] == 'distract']
    
    if distractor.shape[0] == 1:
        to_distract = distractor.iloc[0]['target_1']
        to_redirect_to = distractor.iloc[0]['target_2']
        actions.loc[to_distract, 'target_1'] = to_redirect_to
        
        responses[to_distract].add_message(f'Someone forced you to target {to_redirect_to}.')
        responses[to_distract].set_targets(to_redirect_to, responses[to_distract].target_2)
    
    return actions, responses

    
    """-------------------------
        PARSE VISITS/ACTIONS
    -------------------------"""


def parse_visits(actions):
    visits = actions[actions['action'].isin(VISITS)]['target_1'].reset_index()
    visits.columns = ['Visitor', 'Visited']
    return visits


def get_visitors_to(actions, visits, target):
    visited_target = visits[visits['Visited'] == target]
    output = swap_if_static(list(visited_target['Visitor']), actions)
    return output


def get_visited(actions, visits, target):
    targets_move = visits[visits['Visitor'] == target]
    output = swap_if_static(list(targets_move['Visited']), actions)
    return output


def swap_if_forged(target, visit_list, forgeries=None):
    if forgeries is None:
        return visit_list
    elif target != forgeries['target_1']:
        return visit_list
    else:
        return [forgeries['target_2']]
    
def swap_if_static(player_list, actions):
    for i, p in enumerate(player_list):
        if is_static(actions, p):
            player_list[i] = select_non_static(player_list, p)
    return player_list

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
    
def draw_perks(eligible, n):
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


    