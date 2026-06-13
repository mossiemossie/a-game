from perks import Freeze, Watch, Vigil, Track, Compel, Shield, Selfish, Gaze, Telepathy, Narcissism, Static, Forger, Pact, Vindictive, Bounty, Relentless, Peer, Infer


class Player:
    def __init__(self, identity, player_ids):
        self.identity = identity
        self.cursed = False
        self.frozen = False
        self.player_ids = player_ids

        self.freeze = Freeze(identity, player_ids)
        self.watch = Watch(identity, player_ids)
        self.perks = {'freeze' : self.freeze, 'watch' : self.watch}

    def get_actions(self):
        if self.cursed:
            return ['freeze']
        else:
            return [x for x in self.perks if self.perks[x].is_action() and x != 'freeze']
        
    def get_action_targets(self):
        if self.cursed:
            return {'freeze' : 1}
        else:
            return {str(x) : self.perks[x].get_num_targets() for x in self.get_actions()}

    def get_action_charges(self):
        if self.cursed:
            return {'freeze' : None}
        else:
            return {str(x) : self.perks[x].get_num_charges() for x in self.get_actions()}   

    def get_additional_perks(self):
        pass

    def get_perks(self):
        return [x for x in self.perks.keys() if x not in ['freeze', 'watch']]
    
    def get_relevant_day_information(self):
        # get any information about the player that is relevant in calculating the day phase
        return {
            'id' : self.identity,
            'perks' : list(self.perks.keys()),
        }

    def get_relevant_night_information(self):
        # get any information about the player that is relevant in calculating the night phase
        return {
            'id' : self.identity,
            'perks' : list(self.perks.keys()),
        }

    def give_perk(self, perk_name):
        self.perks.update({perk_name : self.load_perk_from_string(perk_name, self.identity, self.player_ids)})

    def load_perk_from_string(self, perk_name, identity, player_ids):
        match perk_name:
            case 'vigil':
                return Vigil(identity, player_ids)
            case 'track':
                return Track(identity, player_ids)
            case 'compel':
                return Compel(identity, player_ids)
            case 'shield':
                return Shield(identity, player_ids)
            case 'selfish':
                return Selfish(identity, player_ids)
            case 'gaze':
                return Gaze(identity, player_ids)
            case 'telepathy':
                return Telepathy(identity, player_ids)
            case 'narcissism':
                return Narcissism(identity, player_ids)
            case 'static':
                return Static(identity, player_ids)
            case 'forger':
                return Forger(identity, player_ids)
            case 'pact':
                return Pact(identity, player_ids)
            case 'vindictive':
                return Vindictive(identity, player_ids)
            case 'bounty':
                return Bounty(identity, player_ids)
            case 'relentless':
                return Relentless(identity, player_ids)
            case 'peer':
                return Peer(identity, player_ids)
            case 'infer':
                return Infer(identity, player_ids)
            case _:
                raise ValueError('OH NO!')
            
    def parse_night_result(self, result):
        used_perk = self.perks[result.action]
        return used_perk.process_night_result(result)
    
    def get_private_state(self):
        # IMPLEMENT NEXT
        private_state = {
            'actions' : self.get_actions(),
            'action_targets' : self.get_action_targets(),
            'action_charges' : self.get_action_charges(),
            'perks' : self.get_perks(),
            'cursed' : self.cursed,
            'frozen' : self.frozen
        }
        return private_state

    def set_cursed(self, cursed_value):
        self.cursed = cursed_value

    def set_frozen(self, frozen_value):
        self.frozen = frozen_value