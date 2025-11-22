import random
from enum import Enum

class ItemType(Enum):
    WEAPON = "weapon"
    AMMO = "ammo"
    HORSE = "horse"
    MISC = "misc"

class Item:
    def __init__(self, name, item_type, value, stats=None):
        self.name = name
        self.item_type = item_type
        self.value = value
        self.stats = stats or {}

class PlayerState:
    def __init__(self, name):
        self.name = name
        
        # Core Stats
        self.cash = 25.00  # Starting cash
        self.honor = 0     # -100 to 100
        self.reputation = 0 # 0 to 100 (Fame/Infamy)
        self.bounty = 0.00
        
        # Survival Stats
        self.hp = 100
        self.max_hp = 100
        self.blood = 12
        self.max_blood = 12
        self.days_rent_paid = 30
        
        # Combat Stats (Base)
        self.acc_base = 30
        self.spd_base = 30
        self.luck_base = 30
        self.brawl_atk = 10
        self.brawl_def = 10
        
        # Inventory
        self.inventory = []
        self.equipped_weapon = Item("Rusty Revolver", ItemType.WEAPON, 5, {"acc": -5, "spd": 0})
        self.ammo = 12 # Loose rounds
        self.horse = None
        
        # Status
        self.injuries = []
        self.location = "Dusty Creek"
        self.alive = True
        self.conscious = True

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
            self.days_rent_paid += 30
            return True
        return False

class WorldState:
    def __init__(self):
        self.day = 1
        self.time_of_day = "Morning" # Morning, Noon, Evening, Night
        self.town_name = "Dusty Creek"
        self.weather = "Scorching Sun"
