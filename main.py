import sys
import time
import random
from game_state import PlayerState, WorldState, Item, ItemType
from ui import render_hud, get_menu_choice, clear_screen
from duel_engine_v2 import DuelEngineV2, Combatant, Action, ai_cheater, ai_honorable, ai_brawler

def main():
    # Initialize Game
    world = WorldState()
    player = PlayerState("The Stranger")
    
    # Starting Gear
    player.cash = 15.00
    player.ammo = 12
    
    while player.alive:
        render_hud(player, world)
        
        # Town Menu
        print("\n WHERE TO?")
        options = {
            "1": "Cantina (Drink, Rumors, Trouble)",
            "2": "Stables (Horses, Work)",
            "3": "General Store (Supplies)",
            "4": "Sheriff's Office (Bounties)",
            "5": "Doctor (Heal)",
            "6": "Rent Room (Sleep/Save)",
            "Q": "Quit Game"
        }
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            visit_cantina(player, world)
        elif choice == "2":
            visit_stables(player, world)
        elif choice == "3":
            visit_store(player, world)
        elif choice == "4":
            visit_sheriff(player, world)
        elif choice == "5":
            visit_doctor(player, world)
        elif choice == "6":
            sleep(player, world)
        elif choice == "Q":
            sys.exit()
            
    print("\n\n YOU HAVE DIED.")
    print(f" Name: {player.name}")
    print(f" Cash: ${player.cash:.2f}")
    print(f" Honor: {player.honor}")

def visit_cantina(player, world):
    clear_screen()
    print("\n=== THE RUSTY SPUR CANTINA ===")
    print("The air is thick with smoke and the smell of cheap whiskey.")
    print("A piano plays disjointedly in the corner.")
    
    options = {
        "1": "Buy a Drink ($0.50)",
        "2": "Listen for Rumors",
        "3": "Play Poker",
        "4": "Pick a Fight (BRAWL)",
        "5": "Challenge Someone (DUEL)",
        "B": "Back to Town"
    }
    
    choice = get_menu_choice(options)
    
    if choice == "1":
        if player.cash >= 0.50:
            player.cash -= 0.50
            print("\nYou down the whiskey. It burns.")
            player.hp = min(player.max_hp, player.hp + 5)
            input("Press Enter...")
        else:
            print("\nBartender: 'No money, no drink.'")
            input("Press Enter...")
            
    elif choice == "4":
        start_brawl(player)
        
    elif choice == "5":
        start_duel(player)

def start_brawl(player):
    print("\nYou shove a drunk patron. He shoves back!")
    input("FIGHT ON! (Press Enter)")
    
    # Create Combatants
    p1 = Combatant(player.name, -1, player)
    p2 = Combatant("Drunkard", 1)
    p2.brawl_atk = 8
    p2.brawl_def = 5
    p2.hp = 60
    
    engine = DuelEngineV2(p1, p2)
    
    # Simple Brawl Loop
    while p1.conscious and p2.conscious and p1.alive and p2.alive:
        engine.render()
        
        # Player Action
        print("\n[1] PUNCH   [2] BLOCK/WAIT")
        act = input("Action: ")
        p1_act = Action.PUNCH if act == "1" else Action.WAIT
        
        # AI Action
        p2_act = Action.PUNCH if random.random() > 0.3 else Action.WAIT
        
        engine.run_turn(p1_act, p2_act)
        time.sleep(1)
        
    engine.render()
    p1.sync_state() # Save HP loss back to player
    
    if p1.conscious:
        print("\nYOU WON THE BRAWL!")
        loot = random.randint(1, 5)
        player.cash += loot
        print(f"You found ${loot} on the floor.")
        player.reputation += 1
    else:
        print("\nYou were knocked out...")
        player.cash = max(0, player.cash - random.randint(1, 5))
        print("You wake up with less money.")
        
    input("Press Enter...")

def start_duel(player):
    print("\nYou challenge a gunman to a duel in the street!")
    input("WALK OUT (Press Enter)")
    
    p1 = Combatant(player.name, -1, player)
    p2 = Combatant("Gunman", 1)
    p2.acc = 40
    
    engine = DuelEngineV2(p1, p2)
    
    # Duel Loop
    turn_count = 0
    while p1.alive and p2.alive and turn_count < 20:
        engine.render()
        
        # Player Menu
        print("\n[1] PACE   [2] TURN   [3] DRAW   [4] SHOOT CENTER")
        print("[5] SHOOT HIGH [6] SHOOT LOW [7] RELOAD [8] DUCK")
        
        choice = input("Action: ")
        map_act = {
            "1": Action.PACE, "2": Action.TURN, "3": Action.DRAW,
            "4": Action.SHOOT_CENTER, "5": Action.SHOOT_HIGH,
            "6": Action.SHOOT_LOW, "7": Action.RELOAD, "8": Action.DUCK
        }
        p1_act = map_act.get(choice, Action.WAIT)
        
        # AI (Cheater or Honorable?)
        p2_act = ai_honorable(p2, p1, engine)
        
        engine.run_turn(p1_act, p2_act)
        turn_count += 1
        time.sleep(1.5)
        
    p1.sync_state()
    
    if p1.alive and not p2.alive:
        print("\nVICTORY!")
        player.honor -= 5 # Killing is bad? Or neutral?
        player.reputation += 10
        player.cash += 20
        print("You looted $20.")
    elif not p1.alive:
        print("\nDEFEAT.")
        
    input("Press Enter...")

def visit_stables(player, world):
    clear_screen()
    print("STABLES")
    print("1. Work (Bale Hay) +STR +$")
    input("Press Enter...")

def visit_store(player, world):
    clear_screen()
    print("STORE")
    input("Press Enter...")

def visit_sheriff(player, world):
    clear_screen()
    print("SHERIFF")
    input("Press Enter...")

def visit_doctor(player, world):
    clear_screen()
    print("DOCTOR")
    if player.hp < player.max_hp:
        cost = (player.max_hp - player.hp) * 0.1
        print(f"Heal to full for ${cost:.2f}?")
        if input("Y/N: ").upper() == "Y":
            if player.cash >= cost:
                player.cash -= cost
                player.hp = player.max_hp
                player.blood = player.max_blood
                print("Healed.")
    input("Press Enter...")

def sleep(player, world):
    world.day += 1
    world.time_of_day = "Morning"
    player.hp = min(player.max_hp, player.hp + 10)
    print("You slept well.")
    input("Press Enter...")

if __name__ == "__main__":
    main()
