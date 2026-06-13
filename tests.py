from gamemaster import GameMaster
import random as rand

def make_random_actions(gamemaster_object):
    actions = {}

    for p_id in gamemaster_object.player_ids:
        priv_state = gamemaster_object.get_private_state(p_id)
        possible_actions = priv_state['actions']
        weights = [1 if x == 'watch' else 2 for x in possible_actions]
        action_made_idx = rand.choices(range(0, len(possible_actions)), weights = weights, k = 1)[0]
        action_made = possible_actions[action_made_idx]
        num_targets = priv_state['action_targets'][action_made]
        targets = rand.sample([x for x in gamemaster_object.player_ids if x != p_id], num_targets)

        actions.update({p_id : {'action' : action_made, 'targets' : targets}})

    return actions

g = GameMaster(list(range(0, 6)))
actions = make_random_actions(g)
print('perks')
print({p_id : g.get_private_state(p_id)['perks'] for p_id in g.player_ids})
print()
print('actions')
print(actions)
print()
print('results')
print(g.process_night_actions(actions))