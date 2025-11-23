import random
from enum import Enum

class ItemType(Enum):
    WEAPON = "weapon"
    AMMO = "ammo"
    HORSE = "horse"
    HAT = "hat"
    RECEIPT = "receipt"
    TROPHY = "trophy"
    MISC = "misc"

class Item:
    def __init__(self, name, item_type, value, stats=None, description=""):
        self.name = name
        self.item_type = item_type
        self.value = value
        self.stats = stats or {}
        self.description = description

class Hat(Item):
    def __init__(self, name, value, charm_base, description=""):
        super().__init__(name, ItemType.HAT, value, {"charm": charm_base}, description)
        self.holes = 0
        self.charm_base = charm_base
    
    @property
    def charm(self):
        return self.charm_base + self.holes

# --- ITEM CATALOG ---
AVAILABLE_HATS = [
    Hat("Tattered Cap", 2.00, 1, "A sad, floppy thing."),
    Hat("Wide-Brim Felt", 15.00, 5, "Keeps the sun off and looks decent."),
    Hat("Sheriff's Stetson", 50.00, 10, "Commands respect."),
]

AVAILABLE_HORSES = [
    Item("Old Mule", ItemType.HORSE, 15.00, {"spd": 0}, "Slow, stubborn, but better than walking."),
    Item("Mustang", ItemType.HORSE, 50.00, {"spd": 10}, "Wild spirit, good speed."),
    Item("Thoroughbred", ItemType.HORSE, 120.00, {"spd": 25}, "Fast, elegant, expensive."),
]

AVAILABLE_WEAPONS = [
    Item("Rusty Revolver", ItemType.WEAPON, 5.00, {"acc": -5, "spd": -5}, "Prone to jamming."),
    Item("Iron Peacemaker", ItemType.WEAPON, 35.00, {"acc": 0, "spd": 0}, "Reliable standard issue."),
    Item("Pearl-Handled Colt", ItemType.WEAPON, 85.00, {"acc": 10, "spd": 5}, "Beautiful balance and precision."),
    Item("Sawed-Off Shotgun", ItemType.WEAPON, 60.00, {"acc": -10, "spd": 10, "dmg": 20}, "Devastating at close range."),
]

# --- LORE ITEMS (UNIQUE) ---
LORE_ITEMS = [
    Item("The Pale Rider", ItemType.HORSE, 500.00, {"spd": 40, "hp": 100}, "A ghostly white stallion that never tires."),
    Item("Billy's Revolver", ItemType.WEAPON, 300.00, {"acc": 15, "spd": 20}, "The legendary gun of a kid who never missed."),
    Item("Judge's Gavel", ItemType.WEAPON, 150.00, {"acc": 5, "spd": 5, "dmg": 15}, "A heavy mallet used to deliver justice... or blunt force trauma."),
    Item("Marshal's Star", ItemType.TROPHY, 200.00, {"reputation": 50}, "The badge of a fallen U.S. Marshal."),
    Item("Dead Man's Hand", ItemType.MISC, 100.00, {"luck": 20}, "A cursed set of cards: Aces and Eights.")
]

INJURY_EFFECTS = {
    "Broken Arm": {"acc": -15, "spd": 0, "desc": "Aim is shaky."},
    "Broken Leg": {"acc": 0, "spd": -15, "desc": "Can't move fast."},
    "Concussion": {"acc": -10, "spd": -10, "desc": "Head is spinning."},
    "Eye Injury": {"acc": -20, "spd": 0, "desc": "Depth perception gone."},
    "Cracked Ribs": {"acc": 0, "spd": -5, "desc": "Breathing hurts."},
    "Broken Hand (R)": {"acc": -20, "spd": 0, "desc": "Right hand useless."},
    "Broken Hand (L)": {"acc": -20, "spd": 0, "desc": "Left hand useless."}
}

class PlayerState:
    def __init__(self, name):
        self.name = name
        
        # Core Stats
        self.cash = 10.00  # Lower starting cash to force work
        self.honor = 0     # -100 to 100
        self.reputation = 0 # 0 to 100 (Fame/Infamy)
        self.bounty = 0.00
        self.bank_balance = 0.00 # Safe storage
        
        # Survival Stats
        self.hp = 75 # Base 50 + (5 * 5 Def)
        self.blood = 12
        self.max_blood = 12
        self.weeks_rent_paid = 4
        
        # Combat Stats (Base)
        self.acc_base = 30
        self.spd_base = 30
        self.luck_base = 30
        self.brawl_atk = 5
        self.brawl_def = 5
        
        # Inventory
        self.inventory = []
        self.equipped_weapon = Item("Rusty Revolver", ItemType.WEAPON, 5, {"acc": -5, "spd": 0})
        self.hat = Hat("Tattered Cap", 2.00, 1, "A sad, floppy thing.")
        self.ammo = 12 # Loose rounds
        self.horse = None
        
        # Status
        self.injuries = []
        self.location = "Dusty Creek"
        self.alive = True
        self.conscious = True
        self.is_deputy = False
        
        # Gang Features
        self.gang = [] # List of NPC objects
        self.is_gang_leader = False
        self.camp_established = False
        
        # Handedness
        self.dominant_hand = "right" # "right" or "left"
        
        # Healing
        self.healing_injuries = {} # {injury_name: weeks_remaining}
        
        # Training Caps
        self.stables_training_counts = {} # {town_name: count}

    @property
    def max_hp(self):
        # 1 DEF = 5 HP. Base HP 50.
        return 50 + (self.brawl_def * 5)

    @property
    def charm(self):
        return self.hat.charm if self.hat else 0

    def get_acc(self):
        # Base + Weapon + Injuries
        mod = self.equipped_weapon.stats.get("acc", 0)
        
        injury_mod = 0
        for inj in self.injuries:
            effect = INJURY_EFFECTS.get(inj, {})
            injury_mod += effect.get("acc", 0)
            
        return self.acc_base + mod + injury_mod

    def get_spd(self):
        mod = self.equipped_weapon.stats.get("spd", 0)
        
        injury_mod = 0
        for inj in self.injuries:
            effect = INJURY_EFFECTS.get(inj, {})
            injury_mod += effect.get("spd", 0)
            
        return self.spd_base + mod + injury_mod

    def add_item(self, item):
        self.inventory.append(item)

    def pay_rent(self, amount):
        if self.cash >= amount:
            self.cash -= amount
            self.weeks_rent_paid += 4
            return True
        return False

class Town:
    def __init__(self, name, description, traits=None):
        self.name = name
        self.description = description
        self.traits = traits or []
        # Dynamic State
        self.heat = 0
        self.bounty = 0.0
        self.reputation = 0
        
        # Politics
        self.mayor_status = "Alive" # Alive, Dead, Bribed
        self.player_is_mayor = False
        self.influence = 0 # 0-100 (Player control)
        self.treasury = 1000.0 # Funds for wages/repairs
        
        # Territory Control
        self.rackets = [] # List of strings e.g. ["Protection", "Gambling"]
        self.jail = [] # List of Gang Member objects
        self.gang_control = False
        
        # Officials (NPC Objects)
        self.mayor = None
        self.sheriff = None
        
        # Base Lawfulness (Derived from traits)
        self.base_lawfulness = 50
        if "Lawless" in self.traits: self.base_lawfulness = 10
        if "Poor" in self.traits: self.base_lawfulness = 30
        if "Rich" in self.traits: self.base_lawfulness = 70
        if "Fortified" in self.traits: self.base_lawfulness = 90

    @property
    def lawfulness(self):
        if self.gang_control: return 0
        
        val = self.base_lawfulness
        if self.mayor_status == "Dead":
            val = int(val * 0.5) # Chaos reduces lawfulness
        return val

class Gang:
    def __init__(self, name, leader, hideout="Wilderness"):
        self.name = name
        self.leader = leader
        self.members = [] # List of NPC objects (excluding leader)
        self.hideout = hideout
        self.reputation = 0
        self.cash = 100.0
        self.active = True

class WorldState:
    def __init__(self):
        self.week = 1
        self.time_of_day = "Day" 
        self.town_name = "Dusty Creek"
        self.weather = "Scorching Sun"
        
        # Define Towns
        self.towns = {
            "Dusty Creek": Town("Dusty Creek", "A small, dusty settlement.", ["Tutorial", "Poor"]),
            "Shinbone": Town("Shinbone", "A bustling trade hub.", ["Trade Hub", "Rich"]),
            "Brimstone": Town("Brimstone", "A lawless mining camp.", ["Lawless", "Dangerous"]),
            "Silver Hollow": Town("Silver Hollow", "A fortified silver mining town.", ["Fortified", "Rich"]),
            "Dead Man's Drop": Town("Dead Man's Drop", "A ghost town inhabited by outlaws.", ["Ghost Town", "Lawless"])
        }
        
        # Graph: Town -> {Neighbor: Distance_Miles}
        self.map = {
            "Dusty Creek": {"Shinbone": 40, "Brimstone": 120},
            "Shinbone": {"Dusty Creek": 40, "Brimstone": 90, "Silver Hollow": 60},
            "Brimstone": {"Dusty Creek": 120, "Shinbone": 90, "Dead Man's Drop": 50},
            "Silver Hollow": {"Shinbone": 60, "Dead Man's Drop": 100},
            "Dead Man's Drop": {"Brimstone": 50, "Silver Hollow": 100}
        }
        
        # Dynamic World
        self.active_npcs = [] # List of persistent NPC objects roaming the world
        self.rumors = [] # List of strings
        self.rival_gangs = [] # List of Gang objects

    def get_town(self):
        return self.towns.get(self.town_name)

    def get_local_heat(self):
        return self.get_town().heat

    def add_heat(self, amount):
        t = self.get_town()
        if t: t.heat = min(100, t.heat + amount)

    def reduce_heat(self, amount):
        t = self.get_town()
        if t: t.heat = max(0, t.heat - amount)


