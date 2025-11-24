import pickle
import os

SAVE_FILE = "savegame.pkl"

def save_game(player, world):
    data = {
        "player": player,
        "world": world
    }
    try:
        with open(SAVE_FILE, "wb") as f:
            pickle.dump(data, f)
        print("Game saved successfully.")
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False

def migrate_save_data(player, world):
    """
    Ensures loaded data is compatible with the current version.
    Adds missing attributes to objects from older saves.
    """
    # 1. Migrate NPCs (Nemesis System)
    all_npcs = []
    if hasattr(world, 'active_npcs'):
        all_npcs.extend(world.active_npcs)
    if hasattr(player, 'gang'):
        all_npcs.extend(player.gang)
    
    # Town Officials
    for town in world.towns.values():
        if town.sheriff: all_npcs.append(town.sheriff)
        if town.mayor: all_npcs.append(town.mayor)
        if hasattr(town, 'jail'):
            all_npcs.extend(town.jail)
            
    for npc in all_npcs:
        if not hasattr(npc, 'memories'): npc.memories = []
        if not hasattr(npc, 'scars'): npc.scars = []
        if not hasattr(npc, 'is_nemesis'): npc.is_nemesis = False
        if not hasattr(npc, 'vendetta_target'): npc.vendetta_target = None
        if not hasattr(npc, 'relationships'): npc.relationships = {}
        if not hasattr(npc, 'inventory'): npc.inventory = []
        
    # 2. Migrate Player (Camp/Gang)
    if not hasattr(player, 'camp_name'): player.camp_name = "Wilderness Camp"
    if not hasattr(player, 'camp_horses'): player.camp_horses = []
    if not hasattr(player, 'stables_training_counts'): player.stables_training_counts = {}
    
    # 3. Migrate World
    if not hasattr(world, 'rumors'): world.rumors = []

def load_game():
    if not os.path.exists(SAVE_FILE):
        return None, None
    
    try:
        with open(SAVE_FILE, "rb") as f:
            data = pickle.load(f)
            
        player = data["player"]
        world = data["world"]
        
        # Run migration to fix missing attributes
        migrate_save_data(player, world)
        
        return player, world
    except Exception as e:
        print(f"Error loading game: {e}")
        return None, None

def save_exists():
    return os.path.exists(SAVE_FILE)
