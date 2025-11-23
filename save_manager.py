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

def load_game():
    if not os.path.exists(SAVE_FILE):
        return None, None
    
    try:
        with open(SAVE_FILE, "rb") as f:
            data = pickle.load(f)
        return data["player"], data["world"]
    except Exception as e:
        print(f"Error loading game: {e}")
        return None, None

def save_exists():
    return os.path.exists(SAVE_FILE)
