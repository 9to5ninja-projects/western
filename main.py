import sys
import time
import random
import threading
from game_state import PlayerState, WorldState, Item, ItemType, AVAILABLE_HORSES, AVAILABLE_WEAPONS, AVAILABLE_HATS, LORE_ITEMS, Gang
from ui import render_hud, get_menu_choice, clear_screen, get_player_input
from duel_engine_v2 import DuelEngineV2, Combatant, Action, Orientation, ai_cheater, ai_honorable, ai_brawler
from shootout_engine import ShootoutEngine
from characters import NPC
from save_manager import save_game, load_game, save_exists
from visualizer import renderer, Actor
from game_utils import wait_for_user, options_to_buttons
from combat_runner import start_brawl, start_duel, loot_screen, handle_crime, process_gang_casualties
from story_events import check_story_events
from world_sim import generate_rival_gang, process_rival_gangs, update_world_simulation
from town_actions import visit_mayor, bail_member, visit_cantina

# Initialize Visualizer
# renderer = SceneRenderer() # Use global instance from visualizer.py



class GameController:
    def __init__(self):
        self.state = "MAIN_MENU"
        self.player = None
        self.world = None
        self.pending_world = None
        self.running = True
        renderer.init_window()

    def run(self):
        while self.running:
            try:
                if self.state == "MAIN_MENU": self.state_main_menu()
                elif self.state == "NEW_GAME": self.state_new_game()
                elif self.state == "LOAD_GAME": self.state_load_game()
                elif self.state == "TOWN_HUB": self.state_town_hub()
                elif self.state == "CANTINA": self.state_cantina()
                elif self.state == "STABLES": self.state_stables()
                elif self.state == "STORE": self.state_store()
                elif self.state == "SHERIFF": self.state_sheriff()
                elif self.state == "DOCTOR": self.state_doctor()
                elif self.state == "HOTEL": self.state_hotel()
                elif self.state == "TRAVEL": self.state_travel()
                elif self.state == "CAMP": self.state_camp()
                elif self.state == "MAYOR": self.state_mayor()
                elif self.state == "BANK": self.state_bank()
                elif self.state == "QUIT":
                    self.running = False
                    sys.exit()
                else:
                    print(f"Unknown state: {self.state}")
                    self.state = "MAIN_MENU"
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                wait_for_user("Error. Returning to Main Menu.")
                self.state = "MAIN_MENU"

    def state_main_menu(self):
        renderer.load_scene("title_screen")
        title_buttons = [{"label": "New Game", "key": "1"}, {"label": "Quit", "key": "Q"}]
        if save_exists(): title_buttons.insert(1, {"label": "Continue", "key": "2"})
        renderer.render(log_text=["Welcome to Western Legend", "Select an option..."], buttons=title_buttons)
        choice = get_player_input("\nChoice: ").upper()
        if choice == "1": self.state = "NEW_GAME"
        elif choice == "2" and save_exists(): self.state = "LOAD_GAME"
        elif choice == "Q": self.state = "QUIT"

    def state_new_game(self):
        clear_screen()
        renderer.load_scene("character_creation")
        name = renderer.get_text_input("Enter your name:")
        if not name: name = "The Stranger"
        renderer.render(log_text=[f"Name: {name}", "Select Dominant Hand..."], buttons=[{"label": "Right", "key": "1"}, {"label": "Left", "key": "2"}])
        hand = "left" if get_player_input("Choice: ") == "2" else "right"
        towns = ["Dusty Creek", "Shinbone", "Brimstone"]
        renderer.render(log_text=[f"Name: {name}", f"Hand: {hand}", "Select Town..."], buttons=[{"label": t, "key": str(i+1)} for i, t in enumerate(towns)])
        try: start_town = towns[int(get_player_input("Choice: "))-1]
        except: start_town = "Dusty Creek"
        
        self.player = PlayerState(name)
        self.player.dominant_hand = hand
        self.player.location = start_town
        self.player.cash = 12.50
        self.player.ammo = 6
        
        if self.pending_world:
            self.world = self.pending_world
            self.pending_world = None
            for t in self.world.towns.values():
                if t.player_is_mayor: t.player_is_mayor = False; t.mayor_status = "Dead"
            self.world.rumors.append(f"The legend of the previous drifter ended in {self.world.town_name}.")
        else:
            self.world = WorldState()
            for _ in range(random.randint(1, 2)): generate_rival_gang(self.world)
            for town in self.world.towns.values():
                town.mayor = NPC("Mayor"); town.mayor.location = town.name
                town.sheriff = NPC("Sheriff"); town.sheriff.location = town.name
                self.world.active_npcs.extend([town.mayor, town.sheriff])
        
        self.world.town_name = start_town
        print(f"\nWelcome, {name}. Your journey begins in {start_town}.")
        time.sleep(2)
        self.state = "TOWN_HUB"

    def state_load_game(self):
        self.player, self.world = load_game()
        if self.player and self.world:
            # MIGRATION LOGIC
            for town in self.world.towns.values():
                if not hasattr(town, "mayor") or town.mayor is None: town.mayor = NPC("Mayor"); town.mayor.location = town.name; self.world.active_npcs.append(town.mayor)
                if not hasattr(town, "sheriff") or town.sheriff is None: town.sheriff = NPC("Sheriff"); town.sheriff.location = town.name; self.world.active_npcs.append(town.sheriff)
                if not hasattr(town, "mayor_status"): town.mayor_status = "Alive"
                if not hasattr(town, "heat"): town.heat = 0
                if not hasattr(town, "base_lawfulness"): town.base_lawfulness = 50
                if not hasattr(town, "player_is_mayor"): town.player_is_mayor = False
                if not hasattr(town, "influence"): town.influence = 0
                if not hasattr(town, "treasury"): town.treasury = 1000.0
                if not hasattr(town, "rackets"): town.rackets = []
                if not hasattr(town, "jail"): town.jail = []
                if not hasattr(town, "gang_control"): town.gang_control = False
            if not hasattr(self.player, "bank_balance"): self.player.bank_balance = 0.00
            if not hasattr(self.player, "weeks_rent_paid"): self.player.weeks_rent_paid = 0
            if not hasattr(self.player, "healing_injuries"): self.player.healing_injuries = {}
            if not hasattr(self.player, "is_deputy"): self.player.is_deputy = False
            if not hasattr(self.player, "is_gang_leader"): self.player.is_gang_leader = False
            if not hasattr(self.player, "camp_established"): self.player.camp_established = False
            if not hasattr(self.player, "gang"): self.player.gang = []
            if not hasattr(self.player, "dominant_hand"): self.player.dominant_hand = "right"
            if not hasattr(self.player, "luck_base"): self.player.luck_base = 30
            if not hasattr(self.player, "stables_training_counts"): self.player.stables_training_counts = {}
            if not hasattr(self.player, "drunk_counter"): self.player.drunk_counter = 0
            if not hasattr(self.player, "charm_mod"): self.player.charm_mod = 0
            print(f"Welcome back, {self.player.name}.")
            time.sleep(1)
            self.state = "TOWN_HUB"
        else:
            print("Failed to load save.")
            time.sleep(1)
            self.state = "MAIN_MENU"

    def state_town_hub(self):
        if not self.player.alive:
            choice = handle_death(self.player, self.world)
            if choice == "1": self.pending_world = self.world; self.state = "NEW_GAME"
            elif choice == "2": self.pending_world = None; self.state = "NEW_GAME"
            else: self.state = "QUIT"
            return
        renderer.load_scene("town_street")
        renderer.clear_actors()
        renderer.add_actor(Actor("Player", "cowboy_male", 100, 300))
        render_hud(self.player, self.world)
        if self.player.location == "Wilderness Camp": self.state = "CAMP"; return
        
        options = {
            "1": "Cantina", "2": "Stables", "3": "General Store", "4": "Sheriff's Office",
            "5": "Doctor", "6": "Rent Room", "7": "Travel", "Q": "Quit Game"
        }
        if self.player.is_gang_leader: options["6"] = "Return to Camp"; options["4"] = "Sheriff (RISKY)"
        options["8"] = "Town Hall"; options["9"] = "Bank"
        
        renderer.render(player=self.player, world=self.world, log_text=[f"Day {self.world.week}", f"Loc: {self.player.location}"], buttons=options_to_buttons(options))
        choice = get_menu_choice(options)
        
        if choice == "1": self.state = "CANTINA"
        elif choice == "2": self.state = "STABLES"
        elif choice == "3": self.state = "STORE"
        elif choice == "4": self.state = "SHERIFF"
        elif choice == "5": self.state = "DOCTOR"
        elif choice == "6": self.state = "HOTEL"
        elif choice == "7": self.state = "TRAVEL"
        elif choice == "8": self.state = "MAYOR"
        elif choice == "9": self.state = "BANK"
        elif choice == "Q":
            renderer.render(
                log_text=["Save before quitting?", "Y: Save & Quit", "N: Quit without Saving"],
                buttons=[{"label": "Yes", "key": "Y"}, {"label": "No", "key": "N"}]
            )
            if get_player_input().upper() == "Y": 
                save_game(self.player, self.world)
            self.state = "QUIT"

    def state_cantina(self): visit_cantina(self.player, self.world); self.state = "TOWN_HUB"
    def state_stables(self): visit_stables(self.player, self.world); self.state = "TOWN_HUB"
    def state_store(self): visit_store(self.player, self.world); self.state = "TOWN_HUB"
    def state_sheriff(self): visit_sheriff(self.player, self.world); self.state = "TOWN_HUB"
    def state_doctor(self): visit_doctor(self.player, self.world); self.state = "TOWN_HUB"
    def state_hotel(self):
        if self.player.is_gang_leader:
            print("\nYou slip out of town."); self.player.location = "Wilderness Camp"; time.sleep(1); self.state = "CAMP"
        else:
            renderer.load_scene("hotel_room"); renderer.render(log_text=["A simple room."]); sleep(self.player, self.world); self.state = "TOWN_HUB"
    def state_travel(self): renderer.load_scene("wilderness"); renderer.render(log_text=["Checking map..."]); travel_menu(self.player, self.world); self.state = "TOWN_HUB"
    def state_camp(self): visit_camp(self.player, self.world); self.state = "TOWN_HUB"
    def state_mayor(self): renderer.load_scene("town_hall"); renderer.render(log_text=["Town Hall."]); visit_mayor(self.player, self.world); self.state = "TOWN_HUB"
    def state_bank(self): renderer.load_scene("bank_interior"); renderer.render(log_text=["The Bank."]); visit_bank(self.player, self.world); self.state = "TOWN_HUB"

# main_menu replaced by GameController


def new_game(existing_world=None):
    clear_screen()
    renderer.load_scene("character_creation")
    
    # Name Entry
    name = renderer.get_text_input("Enter your name:")
    if not name: name = "The Stranger"
    
    # Dominant Hand
    hand_buttons = [
        {"label": "Right Handed", "key": "1"},
        {"label": "Left Handed", "key": "2"}
    ]
    renderer.render(
        log_text=[f"Name: {name}", "Select Dominant Hand..."],
        buttons=hand_buttons
    )
    
    hand_choice = get_player_input("Choice: ")
    hand = "left" if hand_choice == "2" else "right"
    
    # Starting Town
    towns = ["Dusty Creek", "Shinbone", "Brimstone"]
    town_buttons = [{"label": t, "key": str(i+1)} for i, t in enumerate(towns)]
    
    renderer.render(
        log_text=[f"Name: {name}", f"Hand: {hand.title()}", "Select Starting Town..."],
        buttons=town_buttons
    )
    
    t_choice = get_player_input("Choice: ")
    try:
        start_town = towns[int(t_choice)-1]
    except:
        start_town = "Dusty Creek"
        
    player = PlayerState(name)
    player.dominant_hand = hand
    player.location = start_town
    player.cash = 12.50
    player.ammo = 6
    
    if existing_world:
        world = existing_world
        # Reset player specific world flags
        for t in world.towns.values():
            if t.player_is_mayor:
                t.player_is_mayor = False
                t.mayor_status = "Dead" # Previous mayor (player) died
        
        world.rumors.append(f"The legend of the previous drifter ended in {world.town_name}.")
    else:
        world = WorldState()
        # Generate Rival Gangs
        for _ in range(random.randint(1, 2)):
            generate_rival_gang(world)
            
        # Initialize Town Officials
        for town in world.towns.values():
            town.mayor = NPC("Mayor")
            town.mayor.location = town.name
            town.sheriff = NPC("Sheriff")
            town.sheriff.location = town.name
            world.active_npcs.append(town.mayor)
            world.active_npcs.append(town.sheriff)
        
    world.town_name = start_town
    
    print(f"\nWelcome, {name}. Your journey begins in {start_town}.")
    time.sleep(2)
    return player, world

# game_loop replaced by GameController


def travel_menu(player, world):
    while True:
        render_hud(player, world)
        print(f"\n=== TRAVEL FROM {world.town_name.upper()} ===")
        
        # Get neighbors
        neighbors = world.map.get(world.town_name, {})
        
        opts = {}
        destinations = list(neighbors.keys())
        for i, dest in enumerate(destinations):
            dist = neighbors[dest]
            
            # Calculate Time
            speed = player.horse.stats.get("spd", 5) if player.horse else 2 # Walking speed is slow
            if speed <= 0: speed = 2 # Fallback to walking speed if horse is invalid
            weeks = max(1, round(dist / (speed * 5))) # Rough calc
            
            method = f"Ride {player.horse.name}" if player.horse else "Walk"
            opts[str(i+1)] = f"{dest} ({dist} miles) - {method}: ~{weeks} Weeks"
            
        opts["B"] = "Back"
        
        # Render Travel Menu
        travel_buttons = []
        for i, dest in enumerate(destinations):
            dist = neighbors[dest]
            speed = player.horse.stats.get("spd", 5) if player.horse else 2
            if speed <= 0: speed = 2
            weeks = max(1, round(dist / (speed * 5)))
            label = f"{dest} ({weeks}w)"
            travel_buttons.append({"label": label, "key": str(i+1)})
            
        travel_buttons.append({"label": "Back", "key": "B"})
        
        renderer.render(
            stats_text=[f"Town: {world.town_name}", f"Horse: {player.horse.name if player.horse else 'None'}"],
            log_text=["Where to next?"],
            buttons=travel_buttons
        )
        
        choice = get_menu_choice(opts)
        
        if choice == "B":
            break
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(destinations):
                dest = destinations[idx]
                dist = neighbors[dest]
                speed = player.horse.stats.get("spd", 5) if player.horse else 2
                if speed <= 0: speed = 2
                weeks = max(1, round(dist / (speed * 5)))
                
                renderer.render(log_text=[f"Departing for {dest}...", f"Estimated time: {weeks} weeks."], player=player)
                time.sleep(1)
                
                # Travel Event Loop?
                for w in range(weeks):
                    renderer.render(log_text=[f"Week {w+1} on the trail..."], player=player)
                    time.sleep(0.5)
                    world.week += 1
                    update_world_simulation(world)
                    # Random Event Chance
                    if random.random() < 0.2:
                        # Check for Rival Gang Ambush
                        ambush = False
                        for g in world.rival_gangs:
                            if g.active and g.hideout in [world.town_name, dest] and random.random() < 0.3:
                                
                                enemies = [g.leader] + g.members[:random.randint(2, 4)]
                                player_team = [player] + player.gang
                                
                                renderer.render(
                                    log_text=[f"AMBUSH! {g.name} blocks the road!", f"Leader: {g.leader.name}", "'This is our territory.'", "Fight? (Y/N)"],
                                    player=player,
                                    buttons=[{"label": "Fight", "key": "Y"}, {"label": "Pay Toll", "key": "N"}]
                                )
                                
                                fight_choice = renderer.get_input()
                                
                                if fight_choice == "Y":
                                    engine = ShootoutEngine(player_team, enemies)
                                    while True:
                                        engine.render()
                                        if not engine.run_turn(): break
                                        time.sleep(1)
                                    
                                    process_gang_casualties(player, world)
                                    
                                    # Check Gang Status
                                    if not g.leader.alive:
                                        g.active = False
                                        world.rumors.append(f"{player.name} destroyed {g.name}!")
                                        player.reputation += 20
                                        wait_for_user([f"You killed {g.leader.name}!", "Gang destroyed."], player=player)
                                    
                                    # Remove dead members
                                    g.members = [m for m in g.members if m.alive]
                                    
                                else:
                                    player.cash = max(0, player.cash - 20)
                                    wait_for_user(["You pay a toll ($20) and flee."], player=player)
                                
                                ambush = True
                                break
                        
                        if not ambush:
                            npc = NPC("Outlaw" if random.random() < 0.3 else "Cowboy")
                            
                            log_lines = ["You encounter a stranger.", f"{npc.name} ({npc.archetype})", f"'{npc.get_line()}'"]
                            
                            if npc.archetype == "Outlaw":
                                log_lines.append("Fight? (Y/N)")
                                renderer.render(
                                    log_text=log_lines, 
                                    player=player,
                                    buttons=[{"label": "Fight", "key": "Y"}, {"label": "Ignore", "key": "N"}]
                                )
                                
                                if renderer.get_input() == "Y":
                                    start_duel(player, world, npc)
                            else:
                                wait_for_user(log_lines, player=player)
                
                world.town_name = dest
                wait_for_user([f"Arrived in {dest}."], player=player)
                player.drunk_counter = 0 # Sober up after travel
                
                check_story_events(player, world)
                break
        except ValueError:
            pass



def handle_death(player, world):
    print("\n\n YOU HAVE DIED.")
    print(f" Name: {player.name}")
    print(f" Cash: ${player.cash:.2f}")
    print(f" Honor: {player.honor}")
    
    print("\n=== LEGACY ===")
    print("1. New Drifter (Inherit World State)")
    print("2. New World (Full Reset)")
    print("Q. Quit")
    
    choice = input("Choice: ").upper()
    return choice

def visit_doctor(player, world):
    while True:
        # clear_screen()
        # print("DOCTOR")
        
        log_lines = ["The Doctor is in."]
        options = {}
        buttons = []
        
        # Heal HP
        heal_cost = 0
        if player.hp < player.max_hp:
            heal_cost = (player.max_hp - player.hp) * 0.1
            lbl = f"Heal Wounds (${heal_cost:.2f})"
            options["1"] = lbl
            buttons.append({"label": lbl, "key": "1"})
        else:
            log_lines.append("You are healthy.")

        # Treat Injuries
        injury_cost = 0
        injury_to_treat = None
        
        if player.injuries:
            # Just treat the first one for simplicity in this menu loop
            inj = player.injuries[0]
            injury_to_treat = inj
            
            if "Broken Hand" in inj:
                injury_cost = 25.00
                lbl = f"Cast {inj} (${injury_cost:.2f})"
            else:
                injury_cost = 15.00
                lbl = f"Treat {inj} (${injury_cost:.2f})"
            
            options["2"] = lbl
            buttons.append({"label": lbl, "key": "2"})
            
        options["B"] = "Back"
        buttons.append({"label": "Back", "key": "B"})
        
        renderer.render(
            stats_text=[f"Cash: ${player.cash:.2f}", f"HP: {player.hp}/{player.max_hp}"],
            log_text=log_lines,
            buttons=buttons
        )
        
        choice = renderer.get_input()
        
        if choice == "1" and player.hp < player.max_hp:
            if player.cash >= heal_cost:
                player.cash -= heal_cost
                player.hp = player.max_hp
                player.blood = player.max_blood
                print("Healed.")
                renderer.render(log_text=["Healed to full health."])
                # time.sleep(1)
            else:
                print("Not enough cash.")
                renderer.render(log_text=["Not enough cash."])
                # time.sleep(1)
                
        elif choice == "2" and injury_to_treat:
            if player.cash >= injury_cost:
                player.cash -= injury_cost
                
                if "Broken Hand" in injury_to_treat:
                    duration = random.randint(6, 8)
                    player.healing_injuries[injury_to_treat] = duration
                    player.injuries.remove(injury_to_treat)
                    print("Hand casted.")
                    renderer.render(log_text=["Hand casted. It will heal in time."])
                else:
                    player.injuries.remove(injury_to_treat)
                    print("Treated.")
                    renderer.render(log_text=["Injury treated."])
                # time.sleep(1)
            else:
                print("Not enough cash.")
                renderer.render(log_text=["Not enough cash."])
                # time.sleep(1)
                
        elif choice == "B":
            break

def sleep(player, world):
    while True:
        log_lines = []
        buttons = []
        
        # Rent Status
        if player.weeks_rent_paid > 0:
            log_lines.append(f"Rent paid for {player.weeks_rent_paid} more weeks.")
            log_lines.append("Sleep until morning?")
            buttons.append({"label": "Sleep (1 Week)", "key": "1"})
        else:
            log_lines.append("You have no room rented.")
            log_lines.append("Rent a room for $5.00 / week?")
            buttons.append({"label": "Rent Room ($5)", "key": "1"})
            buttons.append({"label": "Sleep Outside (Free)", "key": "2"})
            
        buttons.append({"label": "Back", "key": "B"})
        
        renderer.render(
            player=player,
            log_text=log_lines,
            buttons=buttons
        )
        
        choice = renderer.get_input()
        
        if choice == "1":
            if player.weeks_rent_paid > 0:
                # Already rented, just sleep
                world.week += 1
                world.time_of_day = "Morning"
                player.hp = min(player.max_hp, player.hp + 20)
                player.blood = min(player.max_blood, player.blood + 2)
                player.weeks_rent_paid -= 1
                player.drunk_counter = 0 # Sober up
                
                update_world_simulation(world)
                process_healing(player)
                
                # Story Events
                check_story_events(player, world)
                
                renderer.render(log_text=["You rested well.", "HP and Blood recovered."], player=player)
                wait_for_user()
                
                # Ask to Save
                renderer.render(log_text=["Save Game? (Y/N)"], player=player)
                if renderer.get_input() == "Y":
                    save_game(player, world)
                return
            else:
                # Renting
                if player.cash >= 5.00:
                    player.cash -= 5.00
                    player.weeks_rent_paid = 4 # Pay for a month? Or just 1 week? Let's say 4 weeks for $5 is too cheap.
                    # Let's make it 1 week for $5.
                    player.weeks_rent_paid = 1
                    print("Room rented.")
                    # Loop back to show "Sleep" option now
                else:
                    renderer.render(log_text=["Not enough cash."], player=player)
                    wait_for_user()
                    
        elif choice == "2" and player.weeks_rent_paid == 0:
            # Sleep Outside
            world.week += 1
            world.time_of_day = "Morning"
            player.hp = min(player.max_hp, player.hp + 5) # Less healing
            player.drunk_counter = 0 # Sober up
            
            update_world_simulation(world)
            process_healing(player)
            
            renderer.render(log_text=["You slept in the dirt.", "It was rough."], player=player)
            wait_for_user()
            
            # Ask to Save
            renderer.render(log_text=["Save Game? (Y/N)"], player=player)
            if renderer.get_input() == "Y":
                save_game(player, world)
            return
            
        elif choice == "B":
            return

def process_healing(player):
    # Healing Injuries
    if player.healing_injuries:
        for inj in list(player.healing_injuries.keys()):
            player.healing_injuries[inj] -= 1
            if player.healing_injuries[inj] <= 0:
                del player.healing_injuries[inj]
                print(f"Your {inj} has fully healed!")
            else:
                print(f"{inj} is healing... ({player.healing_injuries[inj]} weeks left)")

def visit_stables(player, world):
    # Prepare horses
    horses_for_sale = list(AVAILABLE_HORSES)
    town = world.get_town()
    
    # Chance for Pale Rider in Rich or Ghost Towns
    if "Rich" in town.traits or "Ghost Town" in town.traits:
        if random.random() < 0.2: # 20% chance
            pale_rider = next((i for i in LORE_ITEMS if i.name == "The Pale Rider"), None)
            if pale_rider:
                # Check if player already has it
                if not (player.horse and player.horse.name == pale_rider.name):
                    horses_for_sale.append(pale_rider)

    while True:
        render_hud(player, world)
        print("\n=== LIVERY STABLES ===")
        
        options = {
            "1": "Buy Horse",
            "2": "Sell Current Horse",
            "3": "Work: Haul Hay (+$2, +1 Atk)",
            "4": "Work: Break Horses (+$3, +1 Def)",
            "5": "Steal Horse (RISKY)",
            "B": "Back"
        }
        
        renderer.render(
            stats_text=[f"Cash: ${player.cash:.2f}", f"Horse: {player.horse.name if player.horse else 'None'}"],
            log_text=["The smell of hay and manure greets you."],
            buttons=options_to_buttons(options)
        )
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            # print("\nAVAILABLE HORSES:")
            horse_buttons = []
            log_lines = ["AVAILABLE HORSES:"]
            for i, h in enumerate(horses_for_sale):
                is_lore = h in LORE_ITEMS
                prefix = "[LEGENDARY] " if is_lore else ""
                # print(f"{i+1}. {prefix}{h.name} (Spd: {h.stats.get('spd', 0)}, HP: {h.stats.get('hp', 0)}) - ${h.value:.2f}")
                log_lines.append(f"{i+1}. {prefix}{h.name} - ${h.value:.2f}")
                if is_lore:
                    # print(f"   \"{h.description}\"")
                    log_lines.append(f"   \"{h.description}\"")
                horse_buttons.append({"label": f"{h.name} (${h.value:.0f})", "key": str(i+1)})
            
            horse_buttons.append({"label": "Back", "key": "B"})
            
            renderer.render(
                log_text=log_lines + ["Select a horse to purchase..."],
                buttons=horse_buttons,
                player=player
            )
            
            try:
                # idx = int(input("Choice: ")) - 1
                inp = renderer.get_input()
                if inp == "B": continue
                
                idx = int(inp) - 1
                if 0 <= idx < len(horses_for_sale):
                    horse = horses_for_sale[idx]
                    if player.cash >= horse.value:
                        player.cash -= horse.value
                        player.horse = horse
                        print(f"You bought {horse.name}.")
                        renderer.render(log_text=[f"You bought {horse.name}."], player=player)
                        wait_for_user()
                    else:
                        print("Not enough cash.")
                        renderer.render(log_text=["Not enough cash."], player=player)
                        wait_for_user()
            except ValueError:
                pass
                
        elif choice == "2":
            if player.horse:
                val = player.horse.value * 0.5
                player.cash += val
                print(f"Sold {player.horse.name} for ${val:.2f}.")
                player.horse = None
                wait_for_user([f"Sold horse for ${val:.2f}."], player=player)
            else:
                print("You have no horse.")
                wait_for_user(["You have no horse."], player=player)
                
        elif choice == "3":
            # print("\nYou spend a week hauling heavy bales of hay.")
            log_lines = ["You spend a week hauling heavy bales of hay."]
            player.cash += 2.00
            
            # Training Cap Check
            t_name = world.town_name
            count = player.stables_training_counts.get(t_name, 0)
            
            if count < 10:
                player.brawl_atk += 1
                player.stables_training_counts[t_name] = count + 1
                log_lines.append("You feel stronger. (+1 Brawl Atk)")
            else:
                log_lines.append("You have learned all you can here.")
                log_lines.append("(Training limit reached for this town)")
                
            player.honor += 1
            world.week += 1
            player.drunk_counter = 0 # Sober up
            if player.weeks_rent_paid > 0:
                player.weeks_rent_paid -= 1
                log_lines.append("Rent paid for 1 week.")
                
            world.reduce_heat(5) # Good honest work reduces heat
            # print("You earned $2.00. People respect honest work. (+1 Honor)")
            log_lines.append("You earned $2.00. (+1 Honor)")
            
            check_story_events(player, world)
            
            wait_for_user(log_lines, player=player)
            # time.sleep(1.5)
            
        elif choice == "4":
            # print("\nYou spend a week getting thrown by wild mustangs.")
            log_lines = ["You spend a week getting thrown by wild mustangs."]
            player.cash += 3.00
            
            # Training Cap Check
            t_name = world.town_name
            count = player.stables_training_counts.get(t_name, 0)
            
            if count < 10:
                player.brawl_def += 1
                player.stables_training_counts[t_name] = count + 1
                log_lines.append("You feel tougher. (+1 Brawl Def, +5 Max HP)")
            else:
                log_lines.append("You have learned all you can here.")
                log_lines.append("(Training limit reached for this town)")
                
            player.honor += 1
            world.week += 1
            player.drunk_counter = 0 # Sober up
            if player.weeks_rent_paid > 0:
                player.weeks_rent_paid -= 1
                log_lines.append("Rent paid for 1 week.")
                
            world.reduce_heat(5)
            # print("You earned $3.00. (+1 Honor)")
            log_lines.append("You earned $3.00. (+1 Honor)")
            
            check_story_events(player, world)
            
            wait_for_user(log_lines, player=player)
            # time.sleep(1.5)
            
        elif choice == "5":
            # print("\nYou sneak into the stables at night...")
            renderer.render(log_text=["You sneak into the stables at night..."], player=player)
            time.sleep(1)
            
            # Stealth Check (Luck + Speed base?)
            stealth = player.luck_base + random.randint(0, 50)
            difficulty = 50 + (world.get_local_heat() / 2)
            
            if stealth > difficulty:
                # Success
                stolen_horse = random.choice(horses_for_sale) # Can steal from what's available
                player.horse = stolen_horse
                print(f"You successfully stole a {stolen_horse.name}!")
                player.honor -= 10
                world.add_heat(20)
                wait_for_user([f"You stole a {stolen_horse.name}!", "Dishonorable act."], player=player)
            else:
                # Caught
                print("Stablemaster: 'Hey! Get away from there!'")
                # print("He grabs a pitchfork!")
                
                renderer.render(log_text=["Stablemaster: 'Hey! Get away!'", "He attacks!", "Fight? (Y/N)"], player=player)
                # if input("Fight? (Y/N): ").upper() == "Y":
                if renderer.get_input() == "Y":
                    # Stablemaster is a tough brawler
                    sm = NPC("Cowboy")
                    sm.name = "Stablemaster"
                    sm.hp += 20
                    start_brawl(player, world, sm)
                    
                    if not sm.alive:
                        print("You killed the Stablemaster!")
                        player.honor -= 30
                        world.add_heat(50)
                        # Still get the horse?
                        stolen_horse = random.choice(horses_for_sale)
                        player.horse = stolen_horse
                        print(f"You take the {stolen_horse.name} and flee.")
                        wait_for_user(["You killed him.", f"You take the {stolen_horse.name} and flee."], player=player)
                else:
                    print("You run away empty-handed.")
                    world.add_heat(10)
                    wait_for_user(["You run away empty-handed."], player=player)
            # time.sleep(1.5)

        elif choice == "B":
            break

def visit_store(player, world, robbery=False):
    # Prepare inventory for this visit
    weapons_for_sale = list(AVAILABLE_WEAPONS)
    hats_for_sale = list(AVAILABLE_HATS)
    
    town = world.get_town()
    
    # Chance for Lore Items in specific towns
    if "Rich" in town.traits or "Lawless" in town.traits:
        # 30% chance to see a Lore Item
        if random.random() < 0.3:
            potential_lore = [i for i in LORE_ITEMS if i.item_type in [ItemType.WEAPON, ItemType.HAT]]
            if potential_lore:
                rare_item = random.choice(potential_lore)
                # Check if player already has it (unique)
                has_item = any(i.name == rare_item.name for i in player.inventory)
                if player.equipped_weapon.name == rare_item.name: has_item = True
                if player.hat and player.hat.name == rare_item.name: has_item = True
                
                if not has_item:
                    if rare_item.item_type == ItemType.WEAPON:
                        weapons_for_sale.append(rare_item)
                    elif rare_item.item_type == ItemType.HAT:
                        hats_for_sale.append(rare_item)

    while True:
        render_hud(player, world)
        print("\n=== GENERAL STORE ===")
        
        if robbery:
            print("You pull your gun on the shopkeeper!")
            renderer.render(log_text=["You pull your gun!", "Rob the register? (Y/N)"])
            # if input("Rob the register? (Y/N): ").upper() == "Y":
            if renderer.get_input() == "Y":
                loot = random.randint(10, 50)
                print(f"You grabbed ${loot:.2f}!")
                player.cash += loot
                world.add_heat(50)
                player.honor -= 20
                
                # Shopkeeper fights back?
                if random.random() < 0.5:
                    print("Shopkeeper grabs a shotgun!")
                    start_duel(player, world, NPC("Cowboy")) # Use Cowboy stats for shopkeeper
                
                # Flee
                print("You run out before the law arrives.")
                if player.is_gang_leader:
                    player.location = "Wilderness Camp"
                return
            else:
                return

        # Heat affects prices
        heat = world.get_local_heat()
        markup = 1.0 + (heat / 100.0)
        if markup > 1.0:
            print(f"Storekeeper: 'Prices are high for troublemakers like you.' (+{int((markup-1)*100)}%)")
            
        options = {
            "1": f"Buy Ammo (6 rounds) - ${2.00 * markup:.2f}",
            "2": f"Buy Bandages (Heal 10) - ${1.50 * markup:.2f}",
            "3": "Buy Weapons",
            "4": "Buy Hats",
            "B": "Back"
        }
        
        renderer.render(
            stats_text=[f"Cash: ${player.cash:.2f}", f"Ammo: {player.ammo}"],
            log_text=["Shelves lined with canned goods and ammo."],
            buttons=options_to_buttons(options)
        )
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            cost = 2.00 * markup
            if player.cash >= cost:
                player.cash -= cost
                player.ammo += 6
                print("Bought 6 rounds.")
            else:
                print("Not enough cash.")
                
        elif choice == "2":
            cost = 1.50 * markup
            if player.cash >= cost:
                player.cash -= cost
                player.hp = min(player.max_hp, player.hp + 10)
                print("Patched up.")
            else:
                print("Not enough cash.")
                
        elif choice == "3":
            print("\nWEAPONS:")
            weapon_buttons = []
            for i, w in enumerate(weapons_for_sale):
                cost = w.value * markup
                is_lore = w in LORE_ITEMS
                prefix = "[LEGENDARY] " if is_lore else ""
                print(f"{i+1}. {prefix}{w.name} (Acc: {w.stats.get('acc',0)}, Dmg: {w.stats.get('dmg',0)}) - ${cost:.2f}")
                if is_lore:
                    print(f"   \"{w.description}\"")
                weapon_buttons.append({"label": f"{w.name} (${cost:.2f})", "key": str(i+1)})

            renderer.render(log_text=["Select a weapon..."], buttons=weapon_buttons)
            try:
                # idx = int(input("Choice: ")) - 1
                idx = int(renderer.get_input()) - 1
                if 0 <= idx < len(weapons_for_sale):
                    w = weapons_for_sale[idx]
                    cost = w.value * markup
                    if player.cash >= cost:
                        player.cash -= cost
                        player.gun = w # Assuming player.gun is the equipped weapon
                        player.equipped_weapon = w # Update both just in case
                        print(f"Bought {w.name}.")
                    else:
                        print("Not enough cash.")
            except ValueError: pass

        elif choice == "4":
            print("\nHATS:")
            hat_buttons = []
            for i, h in enumerate(hats_for_sale):
                cost = h.value * markup
                is_lore = h in LORE_ITEMS
                prefix = "[LEGENDARY] " if is_lore else ""
                
                defense = h.stats.get('def', 0)
                style = h.stats.get('style', 0)
                if hasattr(h, 'charm_base'):
                    style = h.charm_base
                
                print(f"{i+1}. {prefix}{h.name} (Def: {defense}, Style: {style}) - ${cost:.2f}")
                if is_lore:
                    print(f"   \"{h.description}\"")
                hat_buttons.append({"label": f"{h.name} (${cost:.2f})", "key": str(i+1)})

            renderer.render(log_text=["Select a hat..."], buttons=hat_buttons)
            try:
                # idx = int(input("Choice: ")) - 1
                idx = int(renderer.get_input()) - 1
                if 0 <= idx < len(hats_for_sale):
                    h = hats_for_sale[idx]
                    cost = h.value * markup
                    if player.cash >= cost:
                        player.cash -= cost
                        player.hat = h
                        print(f"Bought {h.name}.")
                    else:
                        print("Not enough cash.")
            except ValueError: pass

        elif choice == "B":
            break

def visit_sheriff(player, world):
    town = world.get_town()
    sheriff = town.sheriff
    
    # Check if Sheriff is dead
    if sheriff and not sheriff.alive:
        print("\n=== SHERIFF'S OFFICE ===")
        print("The Sheriff's desk is empty. The previous Sheriff was killed.")
        print("A temporary deputy is manning the desk.")
        
        # Spawn temporary sheriff for interaction
        sheriff = NPC("Sheriff")
        sheriff.name = "Deputy"
        sheriff.personality = "Lawful" # Deputies are strict
        
    if not sheriff:
        sheriff = NPC("Sheriff")
        town.sheriff = sheriff
        
    while True:
        render_hud(player, world)
        print("\n=== SHERIFF'S OFFICE ===")
        print(f"Sheriff: {sheriff.name}")
        print(f"Personality: {sheriff.personality} ({sheriff.personality_data.get('desc', '')})")
        
        heat = world.get_local_heat()
        if heat > 50:
            print(f"{sheriff.name}: 'I've got my eye on you, stranger.'")
        if heat > 80:
            print(f"{sheriff.name}: 'You're pushing your luck.'")
            
        options = {
            "1": "Check Bounties",
            "2": f"Pay off Bounty/Fines (Cost: ${heat * 2:.2f})",
            "B": "Back"
        }

        if not player.is_deputy:
            options["3"] = "Apply to be Deputy"
        else:
            options["3"] = "Report for Duty (Patrol)"
            
        if town.jail:
            options["4"] = "Bail Out Gang Member"
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            # Check Bounties
            print("\n=== WANTED POSTERS ===")
            wanted = [n for n in world.active_npcs if n.bounty > 0]
            
            # Add Gang Leaders/Members
            for g in world.rival_gangs:
                if not g.active: continue
                if g.leader.bounty > 0:
                    wanted.append(g.leader)
                for m in g.members:
                    if m.bounty > 0:
                        wanted.append(m)
            
            if not wanted:
                print("No active bounties.")
            else:
                for n in wanted:
                    loc = n.location if n.location else "Unknown"
                    # Check if it's a gang leader
                    gang_tag = ""
                    for g in world.rival_gangs:
                        if g.active and (n == g.leader or n in g.members):
                            gang_tag = f" ({g.name})"
                            break
                            
                    print(f"- {n.name}{gang_tag} (${n.bounty:.2f}) - Last seen: {loc}")
                    if n.rumor:
                        print(f"  '{n.rumor}'")
            input("Press Enter...")

        elif choice == "2":
            cost = heat * 2
            if sheriff.personality == "Corrupt":
                cost = cost * 0.5
                print(f"(Corrupt Discount: 50% off)")
                
            if cost > 0:
                print(f"{sheriff.name}: 'That'll clear your name around here. ${cost:.2f}.'")
                if input("Pay? (Y/N): ").upper() == "Y":
                    if player.cash >= cost:
                        player.cash -= cost
                        world.reduce_heat(100) # Clear all heat
                        print(f"{sheriff.name}: 'Alright. Keep your nose clean.'")
                    else:
                        print(f"{sheriff.name}: 'Come back when you have the money.'")
            else:
                print(f"{sheriff.name}: 'You're clean, son.'")

        elif choice == "3":
            if not player.is_deputy:
                if heat > 10:
                    print(f"{sheriff.name}: 'I don't hire troublemakers. Clean up your act.'")
                    time.sleep(1.5)
                elif player.honor < 5 and sheriff.personality == "Lawful":
                    print(f"{sheriff.name}: 'I need someone the people trust. You ain't it.'")
                    time.sleep(1.5)
                else:
                    print(f"{sheriff.name}: 'You look handy with a gun and got a good head on your shoulders.'")
                   
                    if input("Accept? (Y/N): ").upper() == "Y":
                        player.is_deputy = True
                        print("You are now a Deputy.")
                        time.sleep(1)
            else:
                patrol_town(player, world)
        
        elif choice == "4":
            bail_member(player, world)
                
        elif choice == "B":
            break

def patrol_town(player, world):
    town = world.get_town()
    sheriff = town.sheriff if town.sheriff else NPC("Sheriff")
    
    # print("\n=== TOWN PATROL ===")
    # print("You spend the week walking the streets, breaking up fights, and keeping watch.")
    log_lines = ["=== TOWN PATROL ===", "You spend the week walking the streets."]
    
    world.week += 1
    player.drunk_counter = 0 # Sober up
    if player.weeks_rent_paid > 0:
        player.weeks_rent_paid -= 1
        log_lines.append("Rent paid for 1 week.")
        
    player.cash += 5.00
    world.reduce_heat(10) # Deputies lower town heat
    
    check_story_events(player, world)
    
    # Random Event
    roll = random.random()
    if roll < 0.3:
        # print("You spot a drunkard harassing a lady.")
        log_lines.append("You spot a drunkard harassing a lady.")
        renderer.render(log_text=log_lines + ["Intervene? (Y/N)"], player=player)
        
        # if input("Intervene? (Y/N): ").upper() == "Y":
        if renderer.get_input() == "Y":
            start_brawl(player, world, NPC("Drunkard"))
            if player.alive and player.conscious:
                print(f"{sheriff.name}: 'Good work, Deputy.'")
                player.honor += 5
                wait_for_user([f"{sheriff.name}: 'Good work, Deputy.'"], player=player)
    elif roll < 0.5:
        # print("A gang of outlaws rides into town looking for trouble!")
        # print(f"{sheriff.name}: 'Deputy! With me!'")
        log_lines.append("A gang of outlaws rides into town!")
        log_lines.append(f"{sheriff.name}: 'Deputy! With me!'")
        
        # Setup Teams: Player + Sheriff vs Outlaws
        player_team = [player, sheriff]
        enemy_team = [NPC("Outlaw") for _ in range(random.randint(2, 3))]
        
        # print(f"Enemies: {len(enemy_team)}")
        # input("Start Shootout (Press Enter)")
        log_lines.append(f"Enemies: {len(enemy_team)}")
        wait_for_user(log_lines + ["Start Shootout"], player=player)
        
        engine = ShootoutEngine(player_team, enemy_team)
        while True:
            engine.render()
            if not engine.run_turn(): break
            time.sleep(1.5)
            
        if player.alive:
            print(f"{sheriff.name}: 'That's one less problem to worry about.'")
            player.reputation += 10
            player.cash += 20.00 # Bonus
            wait_for_user([f"{sheriff.name}: 'That's one less problem.'", "You earned $20.00 bonus."], player=player)
            
    else:
        # print("It was a quiet week.")
        log_lines.append("It was a quiet week.")
        wait_for_user(log_lines, player=player)
    
    # input("Press Enter...")



def visit_camp(player, world):
    while True:
        render_hud(player, world)
        print("\n=== WILDERNESS CAMP ===")
        
        # Gang Upkeep
        # Wages based on skill/traits, reduced by Charm
        total_wage = 0
        print(f"Gang Members: {len(player.gang)}")
        for m in player.gang:
            base_wage = m.wage
            # Charm Discount (10% per charm point, max 50%)
            discount = min(0.5, player.charm * 0.1)
            final_wage = base_wage * (1.0 - discount)
            total_wage += final_wage
            
            traits = ", ".join(m.traits) if m.traits else "None"
            print(f"- {m.name} ({m.archetype}) [{traits}] - Wage: ${final_wage:.2f}/day")
            
        print(f"Total Daily Upkeep: ${total_wage:.2f}")
            
        options = {
            "1": "Rest by Campfire (Free, Slow Heal)",
            "2": "Plan Heist",
            "3": "Travel to Town",
            "Q": "Quit Game"
        }
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            print("\nYou sleep under the stars.")
            
            # Pay Upkeep
            weekly_cost = total_wage * 7
            if player.cash >= weekly_cost:
                player.cash -= weekly_cost
                print(f"Paid gang wages: ${weekly_cost:.2f}")
            else:
                print("You couldn't pay the gang fully. Morale is low.")
                # Chance for members to leave?
                if player.gang and random.random() < 0.3:
                    leaver = player.gang.pop()
                    print(f"{leaver.name} left the gang due to lack of pay!")
            
            world.week += 1
            world.time_of_day = "Morning"
            player.hp = min(player.max_hp, player.hp + 10) # Less healing than bed
            player.blood = min(player.max_blood, player.blood + 1)
            player.drunk_counter = 0 # Sober up
            print("You feel rested, but your back aches.")
            time.sleep(1)
            
        elif choice == "2":
            plan_heist(player, world)
            
        elif choice == "3":
            travel_menu(player, world)
            if player.location != "Wilderness Camp": # If we traveled
                break
                
        elif choice == "Q":
            if input("Save before quitting? (Y/N): ").upper() == "Y":
                save_game(player, world)
            sys.exit()

def plan_heist(player, world):
    while True:
        clear_screen()
        print("\n=== CRIMINAL OPERATIONS ===")
        print("1. Bank Robbery (Target Specific Town)")
        print("2. Stagecoach Robbery (Req: 3+ Gang, Horses)")
        print("3. Train Robbery (Req: 5+ Gang, Horses, Dynamite/Safecracker)")
        print("B. Back")
        
        choice = input("Choice: ").upper()
        
        if choice == "1":
            plan_bank_robbery(player, world)
        elif choice == "2":
            rob_stagecoach(player, world)
        elif choice == "3":
            rob_train(player, world)
        elif choice == "B":
            break

def plan_bank_robbery(player, world):
    print("\n=== BANK ROBBERY TARGETS ===")
    
    # Dynamic Targets based on Map
    options = {}
    targets = []
    
    # Find nearby towns
    neighbors = world.map.get(world.town_name, {})
    # For simplicity, let's list ALL towns but travel time applies
    
    i = 1
    for t_name, t_data in world.towns.items():
        if t_name == "Dusty Creek": continue # Too poor/tutorial
        
        risk = "Medium"
        reward = "Medium"
        if "Rich" in t_data.traits: reward = "High"
        if "Poor" in t_data.traits: reward = "Low"
        if "Fortified" in t_data.traits: risk = "Extreme"
        if "Lawless" in t_data.traits: risk = "Low"
        
        options[str(i)] = f"Rob Bank in {t_name} ({risk} Risk, {reward} Reward)"
        targets.append(t_name)
        i += 1
        
    options["B"] = "Back"
    
    choice = get_menu_choice(options)
    
    if choice == "B":
        return
        
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(targets):
            target_town = targets[idx]
            print(f"\nRiding to {target_town} to rob the BANK!")
            time.sleep(1)
            player.location = target_town
            world.town_name = target_town
            rob_bank(player, world)
    except:
        pass

def rob_stagecoach(player, world):
    print("\n=== STAGECOACH ROBBERY ===")
    if len(player.gang) < 3:
        print("You need at least 3 gang members to stop a coach.")
        time.sleep(1.5)
        return
    if not player.horse:
        print("You need a horse to chase it down.")
        time.sleep(1.5)
        return
        
    print("You set up an ambush on the trade road...")
    time.sleep(1)
    
    # Chance to find one
    if random.random() < 0.7:
        print("A Wells Fargo coach approaches!")
        guards = [NPC("Cowboy") for _ in range(2)] # Shotgun messengers
        print(f"Guards: {len(guards)}")
        
        if input("Attack? (Y/N): ").upper() == "Y":
            player_team = [player] + player.gang
            engine = ShootoutEngine(player_team, guards)
            while True:
                engine.render()
                if not engine.run_turn(): break
                time.sleep(1)
            
            process_gang_casualties(player, world)
            
            if player.alive and not any(g.alive for g in guards):
                loot = random.randint(50, 150)
                print(f"You pry open the strongbox: ${loot:.2f}")
                player.cash += loot
                player.honor -= 10
                player.reputation += 5
                world.add_heat(20)
            else:
                print("The coach escaped!")
    else:
        print("No coaches came by today.")
    
    time.sleep(2)

def rob_train(player, world):
    print("\n=== TRAIN ROBBERY ===")
    if len(player.gang) < 5:
        print("You need a large crew (5+) to take a train.")
        time.sleep(1.5)
        return
    
    has_expert = any("Safecracker" in m.traits for m in player.gang)
    if not has_expert:
        print("You need a Safecracker to open the armored car.")
        time.sleep(1.5)
        return

    print("You ride alongside the Union Pacific Express!")
    print("This will be a tough fight.")
    
    if input("Board the train? (Y/N): ").upper() == "Y":
        # Train Guards are tough
        guards = [NPC("Sheriff") for _ in range(2)] + [NPC("Cowboy") for _ in range(4)]
        
        player_team = [player] + player.gang
        engine = ShootoutEngine(player_team, guards)
        while True:
            engine.render()
            if not engine.run_turn(): break
            time.sleep(1)
            
        process_gang_casualties(player, world)
        
        if player.alive and not any(g.alive for g in guards):
            loot = random.randint(500, 1500)
            print(f"The Safecracker blows the safe! LOOT: ${loot:.2f}")
            player.cash += loot
            player.honor -= 50
            player.reputation += 50
            world.add_heat(80)
            player.bounty += 100
        else:
            print("You were thrown off the train!")
            player.hp -= 20
            
    time.sleep(2)

def rob_bank(player, world):
    print("\n=== BANK ROBBERY ===")
    town = world.get_town()
    print(f"Target: {town.name}")
    print(f"Town Traits: {', '.join(town.traits)}")
    
    print("You kick open the doors!")
    
    # Guards
    base_guards = 2
    if "Fortified" in town.traits: base_guards += 3
    if "Lawless" in town.traits: base_guards -= 1
    
    guards = [NPC("Sheriff")] + [NPC("Cowboy") for _ in range(max(1, base_guards))]
    
    # Check for Rival Gang Control/Presence
    rival_gang_present = False
    for g in world.rival_gangs:
        if g.active and g.hideout == town.name:
            print(f"\nWARNING: This is {g.name} territory!")
            print("They are guarding the bank too.")
            rival_gang_present = True
            # Add gang members to defenders
            guards.extend(g.members[:3]) # Up to 3 members join the fight
            break
            
    print(f"Guards: {len(guards)}")
    
    # Setup Teams
    player_team = [player] + player.gang
    enemy_team = guards
    
    print("A shootout erupts!")
    input("Press Enter to fight...")
    
    engine = ShootoutEngine(player_team, enemy_team)
    
    # Run Shootout
    while True:
        engine.render()
        cont = engine.run_turn()
        time.sleep(1.5)
        if not cont:
            break
            
    engine.render()
    
    process_gang_casualties(player, world)
    
    # Check Outcome
    enemies_alive = any(e.alive for e in guards)
    
    if player.alive and not enemies_alive:
        base_loot = random.randint(100, 300)
        if "Rich" in town.traits: base_loot *= 2
        if "Poor" in town.traits: base_loot *= 0.5
        
        # Safecracker Bonus
        safecrackers = sum(1 for m in player.gang if "Safecracker" in m.traits and m.alive)
        if safecrackers > 0:
            bonus = base_loot * (0.2 * safecrackers)
            print(f"Safecracker bonus: +${bonus:.2f}")
            base_loot += bonus
            
        print(f"\nSUCCESS! You loot ${base_loot:.2f} from the vault!")
        player.cash += base_loot
        world.add_heat(100) # Max heat
        player.reputation += 50
        player.honor -= 50
        
        # Escape back to camp
        print("You ride off into the sunset before reinforcements arrive!")
        player.location = "Wilderness Camp"
        time.sleep(2)
        
    elif player.alive and enemies_alive:
        print("\nYou were forced to flee!")
        player.location = "Wilderness Camp"
        time.sleep(2)
        
    else:
        print("\nYou died in the shootout.")

def visit_bank(player, world):
    while True:
        render_hud(player, world)
        # print("\n=== FIRST NATIONAL BANK ===")
        
        # Check for receipts
        receipts = [i for i in player.inventory if i.item_type == ItemType.RECEIPT]
        
        options = {
            "1": "Deposit Cash (Safe Storage)",
            "2": "Withdraw Cash",
            "B": "Back"
        }
        
        if receipts:
            options["3"] = f"Cash Bank Drafts ({len(receipts)} available)"
            
        renderer.render(
            player=player,
            stats_text=[f"Bank Balance: ${player.bank_balance:.2f}", f"Cash on Hand: ${player.cash:.2f}"],
            log_text=["=== FIRST NATIONAL BANK ===", "Iron bars and stacks of cash."],
            buttons=options_to_buttons(options)
        )
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            # Deposit Cash
            # print("\n=== DEPOSIT CASH ===")
            # print(f"Current Balance: ${player.bank_balance:.2f}")
            # print(f"Cash on Hand: ${player.cash:.2f}")
            
            try:
                # amount = float(input("Amount to deposit: "))
                prompt = f"Deposit Amount (Max ${player.cash:.2f}):"
                inp = renderer.get_text_input(prompt, player=player)
                if not inp: continue
                
                amount = float(inp)
                if 0 < amount <= player.cash:
                    player.cash -= amount
                    player.bank_balance += amount
                    # print(f"Deposited ${amount:.2f}.")
                    wait_for_user([f"Deposited ${amount:.2f}."], player=player)
                else:
                    # print("Invalid amount.")
                    wait_for_user(["Invalid amount."], player=player)
            except:
                # print("Invalid input.")
                wait_for_user(["Invalid input."], player=player)
            # time.sleep(1)
            
        elif choice == "2":
            # Withdraw Cash
            # print("\n=== WITHDRAW CASH ===")
            # print(f"Current Balance: ${player.bank_balance:.2f}")
            
            try:
                # amount = float(input("Amount to withdraw: "))
                prompt = f"Withdraw Amount (Max ${player.bank_balance:.2f}):"
                inp = renderer.get_text_input(prompt, player=player)
                if not inp: continue
                
                amount = float(inp)
                if 0 < amount <= player.bank_balance:
                    player.bank_balance -= amount
                    player.cash += amount
                    # print(f"Withdrew ${amount:.2f}.")
                    wait_for_user([f"Withdrew ${amount:.2f}."], player=player)
                else:
                    # print("Invalid amount.")
                    wait_for_user(["Invalid amount."], player=player)
            except:
                # print("Invalid input.")
                wait_for_user(["Invalid input."], player=player)
            # time.sleep(1)
            
        elif choice == "3":
            # print("\n=== CASHING DRAFTS ===")
            draft_buttons = []
            log_lines = ["=== CASHING DRAFTS ==="]
            
            for i, r in enumerate(receipts):
                origin = r.stats.get("origin", "Unknown")
                # print(f"{i+1}. {r.name} from {origin}")
                lbl = f"{r.name} ({origin})"
                draft_buttons.append({"label": lbl, "key": str(i+1)})
                log_lines.append(f"{i+1}. {lbl}")
                
            draft_buttons.append({"label": "Back", "key": "B"})
            
            renderer.render(
                log_text=log_lines + ["Select draft to cash..."],
                buttons=draft_buttons,
                player=player
            )
                
            try:
                # idx = int(input("Select draft to cash (0 to cancel): ")) - 1
                inp = renderer.get_input()
                if inp == "B": continue
                
                idx = int(inp) - 1
                if 0 <= idx < len(receipts):
                    draft = receipts[idx]
                    origin = draft.stats.get("origin")
                    
                    # print(f"Teller examines the draft for ${draft.value:.2f}...")
                    renderer.render(log_text=[f"Teller examines draft for ${draft.value:.2f}..."], player=player)
                    time.sleep(1)
                    
                    if origin == world.town_name:
                        # Valid town, but is it your name? No.
                        # Fraud Check
                        # Difficulty based on Town Traits
                        difficulty = 50
                        town = world.get_town()
                        if "Rich" in town.traits: difficulty += 20
                        if "Lawless" in town.traits: difficulty -= 20
                        
                        # Player Skill
                        skill = player.charm * 10 + player.luck_base
                        
                        if skill + random.randint(0, 50) > difficulty:
                            # print("Teller: 'Everything seems in order.'")
                            # print(f"You receive ${draft.value:.2f}.")
                            player.cash += draft.value
                            player.inventory.remove(draft)
                            wait_for_user(["Teller: 'Everything seems in order.'", f"You receive ${draft.value:.2f}."], player=player)
                        else:
                            # print("Teller: 'Wait a minute... this isn't you!'")
                            # print("ALARM RAISED!")
                            world.add_heat(30)
                            player.bounty += 20
                            player.honor -= 5
                            
                            renderer.render(log_text=["Teller: 'Wait... this isn't you!'", "ALARM RAISED!", "Flee? (Y/N)"], player=player)
                            
                            # Fight or Flee?
                            # if input("Flee? (Y/N): ").upper() == "N":
                            if renderer.get_input() == "N":
                                start_duel(player, world, NPC("Sheriff"))
                            else:
                                # print("You run out of the bank!")
                                wait_for_user(["You run out of the bank!"], player=player)
                                time.sleep(1)
                                return
                    else:
                        # print(f"Teller: 'This is drawn on the {origin} branch. You must go there to cash it.'")
                        wait_for_user([f"Teller: 'This is drawn on {origin}.'", "You must go there to cash it."], player=player)
                        # time.sleep(1.5)
            except: pass
            
        elif choice == "B":
            break

if __name__ == '__main__':
    controller = GameController()
    controller.run()
