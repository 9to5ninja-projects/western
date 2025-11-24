import random
import time
from ui import render_hud, get_menu_choice
from visualizer import renderer
from game_utils import wait_for_user, options_to_buttons
from game_state import AVAILABLE_HORSES
from characters import NPC
from combat_runner import start_brawl, start_duel, process_gang_casualties
from shootout_engine import ShootoutEngine
from story_events import check_story_events
from world_sim import update_world_simulation
from save_manager import save_game
import sys

def visit_camp(player, world):
    while True:
        render_hud(player, world)
        
        # Gang Upkeep
        total_wage = 0
        for m in player.gang:
            base_wage = m.wage
            discount = min(0.5, player.charm * 0.1)
            final_wage = base_wage * (1.0 - discount)
            total_wage += final_wage
            
        camp_name = getattr(player, "camp_name", "Wilderness Camp")
        
        log_lines = [f"=== {camp_name.upper()} ==="]
        log_lines.append(f"Gang Members: {len(player.gang)}")
        log_lines.append(f"Daily Upkeep: ${total_wage:.2f}")
        
        options = {
            "1": "Rest by Campfire (Free, Slow Heal)",
            "2": "Camp Stables (Manage Horses)",
            "3": "Manage Gang",
            "4": "Plan Heist",
            "5": "Rename Camp",
            "6": "Break Camp (Travel)",
            "Q": "Quit Game"
        }
        
        renderer.render(
            player=player,
            world=world,
            log_text=log_lines,
            buttons=options_to_buttons(options)
        )
        
        choice = renderer.get_input()
        
        if choice == "1":
            rest_at_camp(player, world, total_wage)
            
        elif choice == "2":
            camp_stables(player, world)
            
        elif choice == "3":
            manage_gang(player, world)
            
        elif choice == "4":
            from crime_actions import plan_heist
            plan_heist(player, world)
            
        elif choice == "5":
            new_name = renderer.get_text_input("Enter Camp Name:", player=player)
            if new_name:
                player.camp_name = new_name
                
        elif choice == "6":
            # Travel
            return "TRAVEL"
            
        elif choice == "Q":
            renderer.render(
                log_text=["Save before quitting?", "Y: Save & Quit", "N: Quit without Saving"],
                buttons=[{"label": "Yes", "key": "Y"}, {"label": "No", "key": "N"}],
                player=player
            )
            if renderer.get_input() == "Y":
                save_game(player, world)
            sys.exit()
            
    # We need to handle the return to main loop or travel.
    # If we break the loop, we go back to main state machine.

def rest_at_camp(player, world, total_wage):
    print("\nYou sleep under the stars.")
    
    # Pay Upkeep
    weekly_cost = total_wage * 7
    if player.cash >= weekly_cost:
        player.cash -= weekly_cost
        msg = f"Paid gang wages: ${weekly_cost:.2f}"
    else:
        msg = "Couldn't pay full wages. Morale low."
        if player.gang and random.random() < 0.3:
            leaver = player.gang.pop()
            msg += f" {leaver.name} left!"
    
    world.week += 1
    world.time_of_day = "Morning"
    player.hp = min(player.max_hp, player.hp + 10)
    player.blood = min(player.max_blood, player.blood + 1)
    player.drunk_counter = 0
    
    update_world_simulation(world)
    check_story_events(player, world)
    
    renderer.render(log_text=["You feel rested.", msg], player=player)
    wait_for_user()

def camp_stables(player, world):
    if not hasattr(player, "camp_horses"):
        player.camp_horses = []
        
    while True:
        log_lines = ["=== CAMP STABLES ==="]
        log_lines.append(f"Current Horse: {player.horse.name if player.horse else 'None'}")
        log_lines.append("Stored Horses:")
        if not player.camp_horses:
            log_lines.append("- None")
        else:
            for h in player.camp_horses:
                log_lines.append(f"- {h.name} (Spd: {h.stats.get('spd', '?')})")
                
        options = {
            "1": "Store Current Horse",
            "2": "Retrieve Horse",
            "B": "Back"
        }
        
        renderer.render(log_text=log_lines, buttons=options_to_buttons(options), player=player)
        choice = renderer.get_input()
        
        if choice == "1":
            if player.horse:
                player.camp_horses.append(player.horse)
                player.horse = None
                wait_for_user(["Horse stored."], player=player)
            else:
                wait_for_user(["You have no horse to store."], player=player)
                
        elif choice == "2":
            if not player.camp_horses:
                wait_for_user(["No horses in stable."], player=player)
            else:
                # Select horse
                buttons = []
                for i, h in enumerate(player.camp_horses):
                    buttons.append({"label": h.name, "key": str(i+1)})
                buttons.append({"label": "Cancel", "key": "B"})
                
                renderer.render(log_text=["Select horse to retrieve:"], buttons=buttons, player=player)
                sub = renderer.get_input()
                
                if sub != "B":
                    try:
                        idx = int(sub) - 1
                        if 0 <= idx < len(player.camp_horses):
                            new_horse = player.camp_horses.pop(idx)
                            
                            # Swap if player has horse
                            if player.horse:
                                player.camp_horses.append(player.horse)
                                msg = f"Swapped {player.horse.name} for {new_horse.name}."
                            else:
                                msg = f"Retrieved {new_horse.name}."
                                
                            player.horse = new_horse
                            wait_for_user([msg], player=player)
                    except: pass
                    
        elif choice == "B":
            break

def manage_gang(player, world):
    # Placeholder for now
    wait_for_user(["Gang management coming soon."], player=player)
