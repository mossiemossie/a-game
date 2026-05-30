import random as rand

# paranoia perk?

class Perk:
    def __init__(self, identity, player_ids):
        self.identity = identity
        self.player_ids = player_ids
        self.has_target_1 = False
        self.has_target_2 = False  
        self.banned_target_1 = [identity]
        self.banned_target_2 = []
        self.targets_must_be_distinct = False 
        self.passive = False
        self.charges = None  
        self.remaining_days = None  
        self.active = True 
        self.target = None

        # verbeages
        self.verb_past = None
        self.verb_present = None
        self.preposition = None

    def get_messages(self, result):
        if result.success:
            # no targets
            if not self.has_target_1: 
                return [f'You {self.verb_past}.']
            # one target 
            elif not self.has_target_2: 
                return [f'You {self.verb_past} {result.target_1}.']
            # two targets
            else:
                return [f'You {self.verb_past} {result.target_1} {self.preposition} {result.target_2}']
        
        else:
            if not self.has_target_1:
                return [f'You attempted to {self.verb_present}, but {result.result}.']
            elif not self.has_target_2:
                return [f'You attempted to {self.verb_present} {result.target_1}, but {result.result}.']
            else:
                return [f'You attempted to {self.verb_present} {result.target_1} {self.preposition} {result.target_2}, but {result.result}']


    def process_night_result(self, result):
        if self.charges is not None:
            self.charges -= 1
        if self.remaining_days is not None:
            self.remaining_days -= 1

        return self.get_messages(self, result)
        
        


    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return 'perk'
    

class Freeze(Perk):
    # Freeze a given player for the next day. The cursed perk.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True 
        self.verb_past = 'froze'
        self.verb_present = 'freeze'
    
    def __str__(self):
        return 'freeze'
    

class Watch(Perk):
    # 1 in 3 chance to identify who visits you. Default perk.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.verb_past = 'watched'
        self.verb_present = 'watch'

    def __str__(self):
        return 'watch'
    

class Vigil(Perk):
    # See who visits target_1.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.verb_present = 'watch over'
        self.verb_past = 'watched over'
        self.charges = 2

    def get_messages(self, result):
        messages = super().get_messages(result)
        if result.success:
            messages.append(f'{list_to_string(result.result)} visited {result.target_1}')
        return messages

    def __str__(self):
        return 'vigil'
    

class Track(Perk):
    # See who target_1 visits.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.verb_present = 'track'
        self.verb_past = 'tracked'
        self.charges = 2

    def get_messages(self, result):
        messages = super().get_messages(result)
        if result.success:
            messages.append(f'{result.target_1} visited {list_to_string(result.result)}.')
        return messages
        
    def __str__(self):
        return 'track'
    

class Compel(Perk):
    # Force target_1 to target target_2. Unique.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.has_target_2 = True
        self.verb_present = 'compel'
        self.verb_past = 'compelled'
        self.preposition = 'to target'
        self.targets_must_be_distinct = True
        self.charges = 3

    def __str__(self):
        return 'compel'
    

class Shield(Perk):
    # Shield target_1 from being frozen tonight.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.verb_present = 'shield'
        self.verb_past = 'shielded'
        self.charges = 5

    def __str__(self):
        return 'shield'
    

class Selfish(Perk):
    # Gain a bonus point if you vote for the killer, but they are not found. Passive
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.passive = True

    def __str__(self):
        return 'selfish'
    

class Gaze(Perk):
    # Discover what perks target_1 has.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.verb_present = 'gaze upon'
        self.verb_past = 'gazed upon'
        self.charges = 1

    def get_messages(self, result):
        messages = super().get_messages(result)
        if result.success:
            messages.append(f'{result.target_1} has the perks {list_to_string(result.result)}.')
        return messages
    
    def __str__(self):
        return 'gaze'
    

class Telepathy(Perk):
    # target_1 will be told who visits you tonight.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.verb_present = 'communicate to'
        self.verb_past = 'communicated to'
        self.charges = 3

    def __str__(self):
        return 'telepathy'
    

class Narcissism(Perk):
    # Gain half a bonus point for each vote you receive. Passive.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.passive = True  

    def __str__(self):
        return 'narcissism'
    

class Static(Perk):
    # Perks targeting you have a 1 in 4 chance of returning false info. Passive.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.passive = True

    def __str__(self):
        return 'static'
    

class Forger(Perk):
    # If target_1 uses an investigative ability, they will be told target_2 was the perpretrator. Bypasses luck checks. Unique.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.has_target_2 = True 
        self.verb_present = 'mislead'
        self.verb_past = 'misled'
        self.preposition = 'into seeing'
        self.targets_must_be_distinct = True 
        self.charges = 2

    def __str__(self):
        return 'forger'
    

class Pact(Perk):
    # For three days, gain a bonus point if a random player is not voted for; lose a bonus point if they are.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.target = rand.choice([x for x in self.player_ids if x != identity])
        self.passive = True
        self.remaining_days = 3

    def __str__(self):
        return 'pact'
    

class Vindictive(Perk):
    # For three days, gain a bonus point if a random player is voted for; lose a bonus point if they aren't by the end.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.target = rand.choice([x for x in self.player_ids if x != identity])
        self.passive = True 
        self.remaining_days = 3

    def __str__(self):
        return 'vindictive'
    

class Bounty(Perk):
    # Set a bounty on a random player; if they are frozen within two day phases, you and the cursed get 2 bonus points.
    # If they are voted out, you get a bonus point. If they are not frozen or voted, you lose a bonus point
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True
        self.verb_past = 'set a bounty on'
        self.verb_present = 'set a bounty on'
        self.remaining_days = 2
        self.charges = 1
        self.active = False

    def __str__(self):
        return 'bounty'
    

class Relentless(Perk):
    # Freeze bypasses shielding.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.passive = True 

    def __str__(self):
        return 'relentless'
    

class Peer(Perk):
    # If target_1 is not cursed, you have a 1 in 2 chance of confirming they aren't.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True 
        self.verb_past = 'peered at'
        self.verb_present = 'peer at'
        self.charges = 4

    def get_messages(self, result):
        messages = super().get_messages(result)
        if result.success:
            messages.append(f'{result.target_1} {"is not" if result.result else "could possibly be"} cursed.')

        return messages
        
    def __str__(self):
        return 'peer'
    

class Infer(Perk):
    # Learn if a visitation occurred between target_1 and target_2.
    def __init__(self, identity, player_ids):
        super().__init__(identity, player_ids)
        self.has_target_1 = True 
        self.has_target_2 = True 
        self.verb_past = 'looked for visits between'
        self.verb_present = 'look for visits between'
        self.preposition = 'and'
        self.charges = 5
        
    def get_messages(self, result):
        messages = super().get_messages(result)
        if result.success:
            messages.append(f'A visit occurred between {result.target_1} and {result.target_2}.')


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