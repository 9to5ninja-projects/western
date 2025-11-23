import random
from game_state import Item, ItemType, Hat, AVAILABLE_WEAPONS, AVAILABLE_HATS

FIRST_NAMES = ["Bill", "Ben", "Jed", "Calamity", "Wild", "Kid", "Red", "Slim", "Shorty", "Tex", "Buffalo", "Dirty", "Ugly", "Mad", "Blind", "Silent", "Fast"]
LAST_NAMES = ["Hickok", "Cassidy", "Earp", "Holiday", "James", "Bonney", "Oakley", "Starr", "Bass", "Slade", "Ringo", "Dalton", "Ford", "West"]

TRAITS = {
    "Sharpshooter": {"desc": "Deadly with a gun.", "acc": 15, "cost": 5.0},
    "Brute": {"desc": "Tough as nails.", "hp": 20, "brawl_atk": 5, "cost": 3.0},
    "Quick": {"desc": "Fastest hand in the west.", "spd": 15, "cost": 5.0},
    "Greedy": {"desc": "Wants a bigger cut.", "cost": 10.0}, # Higher upfront cost
    "Loyal": {"desc": "Will fight to the death.", "cost": 0.0},
    "Drunkard": {"desc": "Unpredictable.", "acc": -5, "hp": 10, "cost": -2.0},
    "Safecracker": {"desc": "Good with locks.", "cost": 10.0}, # Special utility
    "Scout": {"desc": "Knows the land.", "cost": 5.0} # Travel speed bonus?
}

ARCHETYPES = {
    "Drunkard": {
        "cash": (0.5, 5.0), 
        "wpn": "Rusty Revolver", 
        "hat": "Tattered Cap",
        "skill": 0,
        "lines": ["*Hic*", "You lookin' at me?", "Gimme a drink..."],
        "traits": ["Drunkard"]
    },
    "Cowboy": {
        "cash": (5.0, 20.0), 
        "wpn": "Iron Peacemaker", 
        "hat": "Wide-Brim Felt",
        "skill": 3,
        "lines": ["Howdy.", "Move along.", "Nice day for a ride."],
        "traits": ["Loyal", "Scout", "Quick"]
    },
    "Outlaw": {
        "cash": (10.0, 50.0), 
        "wpn": "Pearl-Handled Colt", 
        "hat": "Sheriff's Stetson", 
        "skill": 6,
        "lines": ["Your money or your life.", "You got a death wish?", "Draw."],
        "traits": ["Sharpshooter", "Brute", "Greedy", "Safecracker"]
    },
    "Sheriff": {
        "cash": (20.0, 40.0), 
        "wpn": "Iron Peacemaker", 
        "hat": "Sheriff's Stetson", 
        "skill": 8,
        "lines": ["I am the law.", "Drop it!", "You're coming with me."],
        "traits": ["Sharpshooter", "Brute"]
    },
    "Mayor": {
        "cash": (100.0, 500.0),
        "wpn": "Pearl-Handled Colt", # For show
        "hat": "Wide-Brim Felt", # Fancy
        "skill": -2, # Not a fighter
        "lines": ["I run this town.", "Everything has a price.", "Do you know who I am?"],
        "traits": ["Greedy", "Loyal"] # Loyal to money?
    }
}

MAYOR_PERSONALITIES = {
    "Corrupt": {"desc": "Takes bribes easily.", "bribe_cost_mod": 0.5, "lawfulness_mod": -20},
    "Idealist": {"desc": "Cannot be bribed.", "bribe_cost_mod": 999.0, "lawfulness_mod": 20},
    "Cowardly": {"desc": "Easy to intimidate.", "intimidate_diff": -20, "lawfulness_mod": -10},
    "Tyrant": {"desc": "High taxes, heavy guard.", "tax_mod": 2.0, "lawfulness_mod": 30}
}

SHERIFF_PERSONALITIES = {
    "Corrupt": {"desc": "Looks the other way.", "bounty_hunt_chance": 0.1},
    "Lawful": {"desc": "Relentless pursuit.", "bounty_hunt_chance": 0.8},
    "Drunkard": {"desc": "Often at the saloon.", "bounty_hunt_chance": 0.2, "acc_mod": -10},
    "Gunslinger": {"desc": "Deadly in a duel.", "acc_mod": 20, "spd_mod": 20}
}

class NPC:
    def __init__(self, archetype_name="Cowboy"):
        self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        self.archetype = archetype_name
        data = ARCHETYPES.get(archetype_name, ARCHETYPES["Cowboy"])
        
        self.cash = round(random.uniform(*data["cash"]), 2)
        
        # Find weapon object or default
        self.weapon = next((w for w in AVAILABLE_WEAPONS if w.name == data["wpn"]), AVAILABLE_WEAPONS[0])
        
        # Find hat object or default
        base_hat = next((h for h in AVAILABLE_HATS if h.name == data["hat"]), AVAILABLE_HATS[0])
        # Clone hat so holes are unique
        self.hat = Hat(base_hat.name, base_hat.value, base_hat.charm_base, base_hat.description)
        if random.random() < 0.3:
            self.hat.holes = random.randint(1, 3) # Pre-damaged hats
            
        self.lines = data["lines"]
        
        # Assign Traits
        self.traits = []
        possible_traits = data.get("traits", [])
        if possible_traits and random.random() < 0.7: # 70% chance to have a trait
            self.traits.append(random.choice(possible_traits))
            
        # Combat Stats
        self.brawl_atk = 5 + data["skill"]
        self.brawl_def = 5 + data["skill"]
        self.acc = 30 + (data["skill"] * 5)
        self.spd = 30 + (data["skill"] * 5)
        self.hp = 50 + (self.brawl_def * 5)
        
        # Apply Traits
        self.recruit_cost = 10.0 # Base cost
        for t_name in self.traits:
            t_data = TRAITS.get(t_name, {})
            self.acc += t_data.get("acc", 0)
            self.spd += t_data.get("spd", 0)
            self.hp += t_data.get("hp", 0)
            self.brawl_atk += t_data.get("brawl_atk", 0)
            self.recruit_cost += t_data.get("cost", 0)
            
        self.max_hp = self.hp
        self.blood = 12
        self.max_blood = 12
        
        self.alive = True
        self.conscious = True
        
        # Personality & World Info
        self.quirk = random.choice([
            "Twitches constantly", "Spits when talking", "Polishes gun obsessively",
            "Laughs at nothing", "Stares intensely", "Whispers everything",
            "Chews tobacco loudly", "Plays with a coin", "Never blinks",
            "Scratches a scar", "Hums a funeral march"
        ])
        self.bounty = 0.0
        self.location = "Unknown" # Assigned by World Simulation
        self.rumor = "" # Current rumor about them
        
        # Economy & Alignment
        self.alignment = random.choice(["Lawful", "Neutral", "Chaotic"])
        self.wage = self.recruit_cost * 0.1 # Daily wage is 10% of recruit cost
        
        # Unique Personality (Mayor/Sheriff)
        self.personality = None
        self.personality_data = {}
        
        if self.archetype == "Mayor":
            self.personality = random.choice(list(MAYOR_PERSONALITIES.keys()))
            self.personality_data = MAYOR_PERSONALITIES[self.personality]
            self.lines.append(f"I am a {self.personality} man.")
            
        elif self.archetype == "Sheriff":
            self.personality = random.choice(list(SHERIFF_PERSONALITIES.keys()))
            self.personality_data = SHERIFF_PERSONALITIES[self.personality]
            # Apply stats
            self.acc += self.personality_data.get("acc_mod", 0)
            self.spd += self.personality_data.get("spd_mod", 0)
        
        # Inventory (Bank Receipts)
        self.inventory = []
        if random.random() < 0.2: # 20% chance to carry a bank receipt
            amount = round(random.uniform(10, 100), 2)
            origin = random.choice(["Dusty Creek", "Shinbone", "Brimstone", "Silver Hollow"])
            receipt = Item(f"Bank Draft (${amount})", ItemType.RECEIPT, amount, {"origin": origin})
            self.inventory.append(receipt)

    def get_line(self):
        return f"{random.choice(self.lines)} [{self.quirk}]"
