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
    renderer.load_scene("camp")
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
    
    update_world_simulation(world, player)
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
    while True:
        if not player.gang:
            wait_for_user(["You have no gang members."], player=player)
            return

        log_lines = ["=== GANG MANAGEMENT ==="]
        buttons = []
        
        for i, member in enumerate(player.gang):
            status = "Healthy"
            if member.hp < member.max_hp: status = "Wounded"
            if not member.alive: status = "Dead" # Should be cleaned up but just in case
            
            info = f"{member.name} ({member.archetype}) - {status}"
            log_lines.append(f"{i+1}. {info}")
            buttons.append({"label": member.name, "key": str(i+1)})
            
        buttons.append({"label": "Back", "key": "B"})
        
        renderer.render(log_text=log_lines, buttons=buttons, player=player)
        choice = renderer.get_input()
        
        if choice == "B":
            break
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(player.gang):
                member = player.gang[idx]
                manage_member(player, world, member)
        except ValueError:
            pass

def manage_member(player, world, member):
    while True:
        log_lines = [f"=== {member.name.upper()} ==="]
        log_lines.append(f"Archetype: {member.archetype}")
        log_lines.append(f"HP: {member.hp}/{member.max_hp}")
        log_lines.append(f"Stats: Acc {member.acc}, Spd {member.spd}, Def {member.brawl_def}")
        log_lines.append(f"Weapon: {member.weapon.name if member.weapon else 'None'}")
        log_lines.append(f"Hat: {member.hat.name if member.hat else 'None'}")
        log_lines.append(f"Wage: ${member.wage:.2f}/day")
        
        options = {
            "1": "Talk",
            "2": "Equip Weapon",
            "3": "Equip Hat",
            "4": "Promote (Train) - $50",
            "5": "Kick Out",
            "B": "Back"
        }
        
        renderer.render(log_text=log_lines, buttons=options_to_buttons(options), player=player)
        choice = renderer.get_input()
        
        if choice == "1":
            line = member.get_line()
            wait_for_user([f"{member.name}: '{line}'"], player=player)
            
        elif choice == "2":
            # Equip Weapon from Player Inventory
            weapons = [i for i in player.inventory if i.item_type == 1] # ItemType.WEAPON is 1? Need to check or import
            # Actually let's just check attribute or class name if ItemType isn't available here easily without import
            # But we can import ItemType.
            # Let's assume we can filter by checking if it has 'dmg' stat or similar.
            # Better: Import ItemType at top or use hasattr.
            # player.inventory contains Item objects.
            
            # Let's filter by checking if it has 'stats' and 'dmg' in stats
            weapons = [i for i in player.inventory if hasattr(i, 'item_type') and str(i.item_type) == "ItemType.WEAPON"]
            # Or just check if it has 'dmg' in stats
            weapons = [i for i in player.inventory if i.stats and 'dmg' in i.stats]
            
            if not weapons:
                wait_for_user(["You have no weapons in inventory."], player=player)
            else:
                w_buttons = []
                w_lines = ["Select weapon to give:"]
                for i, w in enumerate(weapons):
                    w_lines.append(f"{i+1}. {w.name}")
                    w_buttons.append({"label": w.name, "key": str(i+1)})
                w_buttons.append({"label": "Cancel", "key": "B"})
                
                renderer.render(log_text=w_lines, buttons=w_buttons, player=player)
                sel = renderer.get_input()
                if sel != "B":
                    try:
                        w_idx = int(sel) - 1
                        if 0 <= w_idx < len(weapons):
                            new_weapon = weapons[w_idx]
                            old_weapon = member.weapon
                            
                            member.weapon = new_weapon
                            player.inventory.remove(new_weapon)
                            
                            if old_weapon:
                                player.inventory.append(old_weapon)
                                wait_for_user([f"Gave {new_weapon.name} to {member.name}.", f"Took back {old_weapon.name}."], player=player)
                            else:
                                wait_for_user([f"Gave {new_weapon.name} to {member.name}."], player=player)
                    except: pass

        elif choice == "3":
            # Equip Hat
            hats = [i for i in player.inventory if i.stats and ('def' in i.stats or 'style' in i.stats)]
            
            if not hats:
                wait_for_user(["You have no hats in inventory."], player=player)
            else:
                h_buttons = []
                h_lines = ["Select hat to give:"]
                for i, h in enumerate(hats):
                    h_lines.append(f"{i+1}. {h.name}")
                    h_buttons.append({"label": h.name, "key": str(i+1)})
                h_buttons.append({"label": "Cancel", "key": "B"})
                
                renderer.render(log_text=h_lines, buttons=h_buttons, player=player)
                sel = renderer.get_input()
                if sel != "B":
                    try:
                        h_idx = int(sel) - 1
                        if 0 <= h_idx < len(hats):
                            new_hat = hats[h_idx]
                            old_hat = member.hat
                            
                            member.hat = new_hat
                            player.inventory.remove(new_hat)
                            
                            if old_hat:
                                player.inventory.append(old_hat)
                                wait_for_user([f"Gave {new_hat.name} to {member.name}.", f"Took back {old_hat.name}."], player=player)
                            else:
                                wait_for_user([f"Gave {new_hat.name} to {member.name}."], player=player)
                    except: pass

        elif choice == "4":
            if player.cash >= 50:
                player.cash -= 50
                member.acc += 1
                member.spd += 1
                member.max_hp += 10
                member.hp += 10
                wait_for_user([f"Trained {member.name}.", "+1 Acc, +1 Spd, +10 HP"], player=player)
            else:
                wait_for_user(["Not enough cash ($50 required)."], player=player)

        elif choice == "5":
            renderer.render(log_text=[f"Kick {member.name} out of the gang?", "Y/N"], player=player)
            if renderer.get_input() == "Y":
                player.gang.remove(member)
                wait_for_user([f"{member.name} left the gang."], player=player)
                break
                
        elif choice == "B":
            break
