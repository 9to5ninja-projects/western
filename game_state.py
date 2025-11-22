import random
from enum import Enum

class ItemType(Enum):
    WEAPON = "weapon"
    AMMO = "ammo"
    HORSE = "horse"
    HAT = "hat"
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

class PlayerState:
    def __init__(self, name):
        self.name = name
        
        # Core Stats
        self.cash = 10.00  # Lower starting cash to force work
        self.honor = 0     # -100 to 100
        self.reputation = 0 # 0 to 100 (Fame/Infamy)
        self.bounty = 0.00
        
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
        # TODO: Calculate injury penalties
        return self.acc_base + mod

    def get_spd(self):
        mod = self.equipped_weapon.stats.get("spd", 0)
        return self.spd_base + mod

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


