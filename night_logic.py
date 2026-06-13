from defs import VISIT_PERKS, FIRST_ROUND_PERKS, PERKS
import random as rand

"""
parse(data): Parse the data dictionary into a dictionary of information to be
sent to each player, according to what happened during the night phase.

data (dict): a dictionary of actions made during the night and relevant player
    information
    {0: {
        'action' : str, 
        'targets' : [target_1, target_2], *len is variable based on num. targets
        'id' : player_id (should be removed)
        'perks' : [perk_name, ...] *len variable based on num. perks
        },
    ...    
    }

returns:
list[Result]: a list of result objects that provide the results
    of the last night phase to each player.
"""
def parse(data):
    data, compel_success, compeller = compel(data)
    visits = get_visits(data)

    forger = get_ids_from_action('forger', data)
    if len(forger) != 0:
        forger = forger + data[forger]['targets']
    else:
        forger = None

    statics = [p for p in data.keys() if 'static' in data[p]['perks']]

    results = {p_id : Result() for p_id in data}
    for p_id in results:
        results[p_id].set_action(data[p_id]['action'])
        results[p_id].set_targets(data[p_id]['targets'])

    # pre-emptively set the forger to unsuccessful (unlike the other perks)
    if forger is not None:
        results[forger[0]].unsuccessful(f'{forger[1]} did not investigate tonight')
    
    # set the success status of the compeller, if they exist
    if compel_success is not None:
        if not compel_success:
            results[compeller[0]].unsuccessful()
        else:
            results[compeller[1]].add_message(f'Something caused you to target {compeller[2]}.')

    results = watch(data, forger, results, statics, visits)
    results = vigil(data, forger, results, statics, visits)
    results = track(data, forger, results, statics, visits)
    results = telepathy(data, forger, results, statics, visits)
    results = infer(data, results, statics, visits)
    results = shield_and_freeze(data, results)
    results = gaze(data, results, statics)
    results = bounty(data, results)
    results = peer(data, results)

    return results

 
#---------#
# HELPERS #
#---------#

"""
broadcast(message, results): Broadcast a message to all player's notifications.

returns:
results
"""
def broadcast(message, results):
    for p in results:
        results[p].add_message(message)

    return results

"""
get_cursed(data): Get the cursed id

returns:
int: the player_id of the cursed player.
"""
def get_cursed(data):
    return get_ids_from_action('freeze', data)[0]

"""
get_visits(data): Get visits made during the night phase.

returns:
list[tuple]: two-tuples where element 0 is the visitor, and element 1 is the visited.
"""
def get_visits(data):
    visits = []
    for p in data:
        if data[p]['action'] in VISIT_PERKS:
            for t in data[p]['targets']:
                visits.append((p, t))

    return visits


"""
get_ids_from_action(action, data): Get the ids of each player that made the given action.

action (str): the action made.

returns:
list[int]: the player_ids that made the given action last night.
"""
def get_ids_from_action(action, data):
    return [x for x in data if data[x]['action'] == action]


"""
get_visited(p, visits): Get the visits made by player p, based on the visits list.

returns:
list[int]: the player_ids that player p visited last night.
"""
def get_visited(p, visits):
    return [x[1] for x in visits if x[0] == p]


"""
get_visitors(p, visits): Get the visits made to player p, based on the visits list.

returns:
list[int]: the player_ids that player p was visited by last night.
"""
def get_visitors(p, visits):
    return [x[0] for x in visits if x[1] == p]


"""
handle_static(data, player_ids, statics): Handle static in the instance of player_ids being the form of information.

player_ids (list[int]): the player_ids as they would be provided to the action user, without static applied
statics (list[int]): each player that has the static perk.

returns:
list[int]: player_ids, adjusted for static.
"""
def handle_static(data, player_ids, statics):
    for i, p in enumerate(player_ids):
        if p in statics:
            player_ids[i] = rand.choice([x for x in data.keys() if x != p])
        
    return player_ids


def handle_forger(forger, p, player_ids, results):
    if forger is not None:
        if forger[1] == p:
            player_ids = [forger[2]]
            results[forger[0]].successful('')

    return results, player_ids

def list_to_string(target_list, capitalize = True):
    if len(target_list) == 0:
        if capitalize:
            return 'No-one'
        else:
            return 'no-one'
    elif len(target_list) == 1:
        return str(target_list[0])
    else:
        target_list = [str(x) for x in target_list]
        s = ", ".join(target_list)
        s = s[::-1].replace(',', 'dna ', 1)[::-1] #swap last ',' for 'and'
        return s


#-------#
# PERKS #
#-------#

"""
bounty
"""
def bounty(data, results):
    bounties = get_ids_from_action('bounty', data)

    for b in bounties:
        target = data[b]['targets'][0]
        results = broadcast(f'A bounty has been set on {target}.', results)

    return results


"""
compel
"""
def compel(data):
    compeller = get_ids_from_action('compel', data)
    if len(compeller) == 0:
        return data, None, [None, None, None]
    else:
        compeller = compeller[0]
        compeller_target_1 = data[compeller]['targets'][0]
        compeller_target_2 = data[compeller]['targets'][1]

        if len(data[compeller_target_1]['targets']) == 0:
            return data, False, [compeller, compeller_target_1, compeller_target_2]
        else:
            data[compeller_target_1]['targets'][0] = compeller_target_2
            return data, True, [compeller, compeller_target_1, compeller_target_2]
        

"""
gaze
"""
def gaze(data, results, statics):
    gazers = get_ids_from_action('gaze', data)

    for g in gazers:
        target = data[g]['targets'][0]
        # handle statics
        if target in statics and rand.randint(0, 3) == 0:
            false_perks = []
            for i in range(0, len(data[target]['perks'])): # this logic doesn't replicate how perks are actually given out. it probably should.
                if i == 0:
                    false_perks.append(rand.choice(FIRST_ROUND_PERKS))
                else:
                    false_perks.append(rand.choice([x for x in PERKS if x not in false_perks]))

            results[g].set_outcome(false_perks)
        
        else:
            results[g].set_outcome(data[target]['perks'])

    return results


"""
infer
"""
def infer(data, results, statics, visits):
    inferences = get_ids_from_action('infer', data)

    for i in inferences:
        # handle statics first
        target_static = (data[i]['targets'][0] in statics or data[i]['targets'][1] in statics) and rand.randint(0, 3) == 0
        no_visit = not ((data[i]['targets'][0], data[i]['targets'][1]) in visits or (data[i]['targets'][1], data[i]['targets'][0]) in visits)

        if target_static or no_visit:
            results[i].set_outcome('No visit occured')
        else:
            results[i].set_outcome('A visit occured')
            
    return results     


"""
peer
"""
def peer(data, results):
    # only edge case to deal with currently is if the cursed player has static;
    cursed = get_cursed(data)
    cursed_has_static = 'static' in data[cursed]['perks']
    peers = get_ids_from_action('peer', data)

    for p in peers:
        target = data[p]['targets'][0]
        
        if rand.randint(0, 1) > 0: # Can't confirm whether or not player is cursed;
            # but if cursed player has static and passes they'll be confirmed as not cursed:
            if target == cursed and cursed_has_static and rand.randint(0, 3) == 0:
                results[p].set_outcome(True) # p will be told target is confirmed not cursed
            else:
                results[p].set_outcome(False) # p will be told target is unconfirmed
        else:
            if target == cursed:
                results[p].set_outcome(False) # p will be told target is unconfirmed
            else:
                results[p].set_outcome(True) # p will be told target is confirmed.
        
    return results
            


"""
shield and freeze
"""
def shield_and_freeze(data, results):
    shielders = get_ids_from_action('shield', data)
    shielded = [data[s]['targets'][0] for s in shielders]
    cursed = get_cursed(data)
    cursed_is_relentless = 'relentless' in data[cursed]['perks']
    frozen = data[cursed]['targets'][0]

    # case 1: player was shielded, but cursed player was relentless.

    # case 2: player was shielded and cursed player was not relentless.

    # case 3: player was not shielded

    if frozen in shielded:
        successful_shielder = shielders[shielded.index(frozen)]
        unsuccessful_shielders = [x for x in shielders if x is not successful_shielder]

        if cursed_is_relentless:
            results[successful_shielder].unsuccessful('failed')
            results[frozen].was_frozen()
            results = broadcast(f'{frozen} was frozen.', results)
        else:
            results[cursed].unsuccessful('they were shielded')
            results = broadcast('Nobody was frozen.', results)

        for u in unsuccessful_shielders:
            results[u].unsuccessful('they were not attacked')

    else:
        for s in shielders:
            results[s].unsuccessful('they were not attacked')
        
        results[frozen].was_frozen()
        results = broadcast(f'{frozen} was frozen.', results)

    return results


"""
telepathy
"""
def telepathy(data, forger, results, statics, visits):
    telepaths = get_ids_from_action('telepathy', data)

    for t in telepaths:
        visitors = get_visitors(t, visits)
        visitors = handle_static(data, visitors, statics)
        results, visitors = handle_forger(forger, t, visitors, results)
        print(data[t]['targets'][0])
        results[data[t]['targets'][0]].add_message(f'{list_to_string(visitors)} visited {t} tonight.') #this needs fixing probably, visitors will show up as a list.

    return results


"""
track
"""
def track(data, forger, results, statics, visits):
    trackers = get_ids_from_action('track', data)
    
    for t in trackers:
        visited = get_visited(data[t]['targets'][0], visits)
        visited = handle_static(data, visited, statics)
        results, visited = handle_forger(forger, t, visited, results)
        results[t].set_outcome(visited)

    return results


"""
vigil
"""
def vigil(data, forger, results, statics, visits):
    vigils = get_ids_from_action('vigil', data)
    
    for v in vigils:
        visitors = get_visitors(data[v]['targets'][0], visits)
        visitors = [x for x in visitors if x != v]
        visitors = handle_static(data, visitors, statics)
        results, visitors = handle_forger(forger, v, visitors, results)
        results[v].set_outcome(visitors)

    return results

            
"""
watch
"""
def watch(data, forger, results, statics, visits):
    watchers = get_ids_from_action('watch', data)

    for w in watchers:
        if forger is not None: #handle forger differently here, because it should bypass the luck check on watch & static.
            if forger[1] == w:
                results[w].set_outcome([forger[2]])
            
        elif rand.randint(0, 1) > 0: # unsuccessful
            results[w].unsuccessful("couldn't make out who may have visited you, if anyone")
        
        else:
            visitors = get_visitors(w, visits)
            visitors = handle_static(data, visitors, statics)
            results[w].set_outcome(visitors)

    return results




class Result:
    def __init__(self):
        self.action = None
        self.target_1 = None
        self.target_2 = None 
        self.messages = []
        self.success = True 
        self.frozen = False 
        self.outcome = None      # the data to be communicated to the player; either str describing reason for failure, or the information expected.

    def set_action(self, action):
        self.action = action 

    def set_targets(self, targets):
        if len(targets) == 0:
            return 
        self.target_1 = targets[0]
        if len(targets) == 2:
            self.target_2 = targets[1]

    def add_message(self, message):
        self.messages.append(message)
    
    def unsuccessful(self, outcome):
        self.success = False 
        self.set_outcome(outcome) 

    def successful(self, outcome):
        self.success = True
        self.set_outcome(outcome)

    def was_frozen(self):
        self.frozen = True 

    def set_outcome(self, outcome):
        self.outcome = outcome

    def __str__(self):
        return f'Action = {self.action}, successful = {self.success}, messages = {self.messages}, frozen = {self.frozen}, outcome = {self.outcome}'