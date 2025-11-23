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

# Initialize Visualizer
# renderer = SceneRenderer() # Use global instance from visualizer.py

def options_to_buttons(options):
    buttons = []
    for key, value in options.items():
        # Simple truncation for button labels to avoid overflow
        label = value.split(" - ")[0] if " - " in value else value
        if len(label) > 20: label = label[:17] + "..."
        buttons.append({"label": label, "key": key})
    return buttons

def wait_for_user(prompt="Press Enter to continue...", player=None):
    if isinstance(prompt, list):
        log_text = prompt + ["(Press Enter)"]
    else:
        log_text = [prompt]

    renderer.render(
        log_text=log_text,
        buttons=[{"label": "Continue", "key": "ENTER"}],
        player=player
    )
    while True:
        key = renderer.get_input()
        if key in ["ENTER", "SPACE"]:
            break

def main_menu():
    # Start Visualizer Window
    renderer.init_window()
    renderer.load_scene("title_screen")
    
    # Define Title Screen Buttons
    title_buttons = [
        {"label": "New Game", "key": "1"},
        {"label": "Quit", "key": "Q"}
    ]
    if save_exists():
        title_buttons.insert(1, {"label": "Continue", "key": "2"})
        
    while True:
        renderer.render(
            log_text=["Welcome to Western Legend", "Select an option..."],
            buttons=title_buttons
        )
        
        clear_screen()
        print("=================================")
        print("   W E S T E R N   L E G E N D   ")
        print("=================================")
        print("1. New Game")
        if save_exists():
            print("2. Continue")
        print("Q. Quit")
        
        choice = get_player_input("\nChoice: ").upper()
        
        if choice == "1":
            player, world = new_game()
            game_loop(player, world)
        elif choice == "2" and save_exists():
            player, world = load_game()
            if player and world:
                # MIGRATION: Fix old saves
                from characters import NPC
                for town in world.towns.values():
                    if not hasattr(town, "mayor") or town.mayor is None:
                        town.mayor = NPC("Mayor")
                        town.mayor.location = town.name
                        if town.mayor not in world.active_npcs:
                            world.active_npcs.append(town.mayor)
                            
                    if not hasattr(town, "sheriff") or town.sheriff is None:
                        town.sheriff = NPC("Sheriff")
                        town.sheriff.location = town.name
                        if town.sheriff not in world.active_npcs:
                            world.active_npcs.append(town.sheriff)
                            
                    if not hasattr(town, "mayor_status"): town.mayor_status = "Alive"
                    if not hasattr(town, "heat"): town.heat = 0
                    if not hasattr(town, "base_lawfulness"): town.base_lawfulness = 50
                    if not hasattr(town, "player_is_mayor"): town.player_is_mayor = False
                    if not hasattr(town, "influence"): town.influence = 0
                    if not hasattr(town, "treasury"): town.treasury = 1000.0
                    if not hasattr(town, "rackets"): town.rackets = []
                    if not hasattr(town, "jail"): town.jail = []
                    if not hasattr(town, "gang_control"): town.gang_control = False

                # MIGRATION: Fix old player saves
                if not hasattr(player, "bank_balance"): player.bank_balance = 0.00
                if not hasattr(player, "weeks_rent_paid"): player.weeks_rent_paid = 0
                if not hasattr(player, "healing_injuries"): player.healing_injuries = {}
                if not hasattr(player, "is_deputy"): player.is_deputy = False
                if not hasattr(player, "is_gang_leader"): player.is_gang_leader = False
                if not hasattr(player, "camp_established"): player.camp_established = False
                if not hasattr(player, "gang"): player.gang = []
                if not hasattr(player, "dominant_hand"): player.dominant_hand = "right"
                if not hasattr(player, "luck_base"): player.luck_base = 30
                if not hasattr(player, "stables_training_counts"): player.stables_training_counts = {}

                print(f"Welcome back, {player.name}.")
                time.sleep(1)
                game_loop(player, world)
        elif choice == "Q":
            sys.exit()

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

def game_loop(player, world):
    # Game Loop
    while player.alive:
        # Update Visuals
        renderer.load_scene("town_street")
        renderer.clear_actors()
        renderer.add_actor(Actor("Player", "cowboy_male", 100, 300))
        
        # Update HUD with Visuals
        render_hud(player, world)
        
        # Town Menu
        if player.location == "Wilderness Camp":
            visit_camp(player, world)
            continue

        print(f"\n WHERE TO? ({world.town_name})")
        options = {
            "1": "Cantina (Drink, Rumors, Trouble)",
            "2": "Stables (Horses, Work)",
            "3": "General Store (Supplies)",
            "4": "Sheriff's Office (Bounties)",
            "5": "Doctor (Heal)",
            "6": "Rent Room (Sleep/Save)",
            "7": "Travel (Leave Town)",
            "Q": "Quit Game"
        }
        
        # Gang Leader Restrictions
        if player.is_gang_leader:
            options["6"] = "Return to Camp (Leave Town)"
            # Sheriff is dangerous
            options["4"] = "Sheriff's Office (RISKY)"
            
        # Mayor Option
        options["8"] = "Town Hall (Mayor)"
        options["9"] = "Bank (Deposit/Cash)"
        
        # Generate Buttons from Options
        town_buttons = options_to_buttons(options)
        
        renderer.render(
            player=player,
            world=world,
            log_text=[f"Day {world.week}", f"Location: {player.location}"],
            buttons=town_buttons
        )
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            renderer.load_scene("cantina_interior")
            renderer.render(log_text=["You enter the smoky cantina..."])
            visit_cantina(player, world)
        elif choice == "2":
            renderer.load_scene("stables")
            renderer.render(log_text=["The smell of hay and manure greets you."])
            visit_stables(player, world)
        elif choice == "3":
            renderer.load_scene("general_store")
            renderer.render(log_text=["Shelves lined with canned goods and ammo."])
            visit_store(player, world)
        elif choice == "4":
            renderer.load_scene("sheriff_office")
            renderer.render(log_text=["Wanted posters cover the walls."])
            visit_sheriff(player, world)
        elif choice == "5":
            renderer.load_scene("doctor_office")
            renderer.render(log_text=["It smells of rubbing alcohol and blood."])
            visit_doctor(player, world)
        elif choice == "6":
            if player.is_gang_leader:
                print("\nYou slip out of town and ride to your hideout.")
                player.location = "Wilderness Camp"
                time.sleep(1)
            else:
                renderer.load_scene("hotel_room")
                renderer.render(log_text=["A simple room to rest your head."])
                sleep(player, world)
        elif choice == "7":
            renderer.load_scene("wilderness")
            renderer.render(log_text=["Checking the map..."])
            travel_menu(player, world)
        elif choice == "8":
            renderer.load_scene("town_hall")
            renderer.render(log_text=["The seat of local power."])
            visit_mayor(player, world)
        elif choice == "9":
            renderer.load_scene("bank_interior")
            renderer.render(log_text=["Iron bars and stacks of cash."])
            visit_bank(player, world)
        elif choice == "Q":
            if get_player_input("Save before quitting? (Y/N): ").upper() == "Y":
                save_game(player, world)
            sys.exit()
            
    handle_death(player, world)

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
                break
        except ValueError:
            pass

def visit_cantina(player, world):
    while True:
        render_hud(player, world)
        print("\n=== THE RUSTY SPUR CANTINA ===")
        print("The air is thick with smoke and the smell of cheap whiskey.")
        
        # Random Trouble Check (10% chance on entry/loop)
        # Heat increases chance of trouble
        heat = world.get_local_heat()
        trouble_chance = 0.10 + (heat / 200.0) # 10% base + up to 50% at max heat
        
        if random.random() < trouble_chance:
            print("\n!!! TROUBLE !!!")
            
            if heat > 80:
                print("The Sheriff has found you!")
                npc = NPC("Sheriff")
            else:
                print("A drunkard spills his drink on you and swings!")
                npc = NPC("Drunkard")
                
            wait_for_user("Defend yourself!")
            
            if npc.archetype == "Sheriff":
                start_duel(player, world, npc)
            else:
                start_brawl(player, world, npc)
            continue

        options = {
            "1": "Buy a Drink ($0.50) - Heals 5 HP",
            "2": "Listen for Rumors",
            "3": "Pick a Fight (BRAWL)",
            "4": "Challenge Someone (DUEL)",
            "B": "Back to Town"
        }
        
        if not player.is_gang_leader:
             options["5"] = "Recruit Gunhand (Req: 20 Rep, $10)"
        else:
             options["5"] = "Recruit More Muscle ($10)"
        
        renderer.render(
            stats_text=[f"Cash: ${player.cash:.2f}", f"HP: {player.hp}/{player.max_hp}"],
            log_text=["The air is thick with smoke..."],
            buttons=options_to_buttons(options)
        )
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            if player.cash >= 0.50:
                player.cash -= 0.50
                player.hp = min(player.max_hp, player.hp + 5)
                wait_for_user(["You down the whiskey.", "It burns. (+5 HP)"], player=player)
            else:
                wait_for_user(["Bartender: 'No money, no drink.'"], player=player)
                
        elif choice == "2":
            # print("\n=== RUMORS ===")
            log_lines = ["=== RUMORS ==="]
            if not world.rumors:
                # print("It's quiet. Too quiet.")
                log_lines.append("It's quiet. Too quiet.")
            else:
                for r in world.rumors:
                    # print(f"- {r}")
                    log_lines.append(f"- {r}")
            
            # Mingle with Locals
            locals_here = [n for n in world.active_npcs if n.location == world.town_name]
            
            # Add Gang Members
            for g in world.rival_gangs:
                if g.active and g.hideout == world.town_name:
                    locals_here.append(g.leader)
                    locals_here.extend(g.members)
            
            buttons = []
            if locals_here:
                # print("\n=== NOTABLE PEOPLE ===")
                log_lines.append("=== NOTABLE PEOPLE ===")
                for i, n in enumerate(locals_here):
                    # Tag gang members
                    tag = ""
                    for g in world.rival_gangs:
                        if g.active and (n == g.leader or n in g.members):
                            tag = f" [{g.name}]"
                            break
                    # print(f"{i+1}. Talk to {n.name} ({n.archetype}){tag}")
                    lbl = f"Talk to {n.name}"
                    buttons.append({"label": lbl, "key": str(i+1)})
                
                # print("M. Mingle")
                buttons.append({"label": "Mingle", "key": "M"})
                
                renderer.render(
                    log_text=log_lines,
                    buttons=buttons
                )
                
                # sub = input("Choice: ").upper()
                sub = renderer.get_input()
                
                if sub == "M":
                    wait_for_user(["You mingle with the crowd.", "Nothing of interest happens."], player=player)
                else:
                    try:
                        idx = int(sub) - 1
                        if 0 <= idx < len(locals_here):
                            target = locals_here[idx]
                            # print(f"\nYou approach {target.name}.")
                            # print(f"{target.name}: '{target.get_line()}'")
                            
                            dialogue = [f"You approach {target.name}.", f"{target.name}: '{target.get_line()}'"]
                            
                            if target.bounty > 0:
                                # print(f"(Wanted: ${target.bounty:.2f})")
                                dialogue.append(f"(Wanted: ${target.bounty:.2f})")
                                renderer.render(log_text=dialogue + ["Attempt to arrest/kill? (Y/N)"])
                                
                                # if input("Attempt to arrest/kill? (Y/N): ").upper() == "Y":
                                if renderer.get_input() == "Y":
                                    start_duel(player, world, target)
                                    if player.alive and not target.alive:
                                        print(f"You collected the bounty of ${target.bounty:.2f}!")
                                        player.cash += target.bounty
                                        player.reputation += 10
                                        world.active_npcs.remove(target)
                            else:
                                renderer.render(log_text=dialogue)
                                wait_for_user()
                    except: pass
            else:
                renderer.render(log_text=log_lines)
                wait_for_user()
            
            # input("Press Enter...")
        
        elif choice == "3":
            npc = NPC("Drunkard")
            start_brawl(player, world, npc)
            
        elif choice == "4":
            npc = NPC("Cowboy")
            start_duel(player, world, npc)
            
        elif choice == "5":
            # Recruit Gang Member
            if player.reputation < 20:
                print("\nMercenary: 'I don't ride with nobodies. Come back when you have a name.'")
            elif player.cash < 10.00:
                print("\nMercenary: 'I need $10.00 upfront, boss.'")
            else:
                # Generate 3 candidates
                candidates = [NPC("Outlaw") for _ in range(3)]
                print("\n=== RECRUITMENT ===")
                for i, c in enumerate(candidates):
                    traits = ", ".join(c.traits) if c.traits else "None"
                    print(f"{i+1}. {c.name} - Cost: ${c.recruit_cost:.2f}")
                    print(f"   Traits: {traits}")
                    print(f"   Stats: Acc {c.acc}, Spd {c.spd}, HP {c.hp}")
                
                print("B. Cancel")
                
                sel = input("Choose recruit: ").upper()
                if sel in ["1", "2", "3"]:
                    idx = int(sel) - 1
                    recruit = candidates[idx]
                    
                    if player.cash >= recruit.recruit_cost:
                        player.cash -= recruit.recruit_cost
                        player.gang.append(recruit)
                        print(f"{recruit.name} joined your gang.")
                        
                        if not player.is_gang_leader:
                            print("\n!!! GANG FORMED !!!")
                            print("You have started a gang. You can no longer sleep safely in towns.")
                            print("You must now operate from a Wilderness Camp.")
                            player.is_gang_leader = True
                            player.camp_established = True
                            player.location = "Wilderness Camp" # Force move to camp
                            time.sleep(2)
                            return # Exit cantina loop to trigger main loop camp check
                    else:
                        print("Not enough cash for that one.")
                else:
                    pass

        elif choice == "B":
            break

def loot_screen(player, world, npc):
    while True:
        # clear_screen()
        # print(f"\n=== LOOTING {npc.name.upper()} ===")
        # print("Taking items is considered theft and dishonorable.")
        
        log_lines = [f"=== LOOTING {npc.name.upper()} ===", "Taking items is theft."]
        
        options = {}
        buttons = []
        
        if npc.cash > 0:
            lbl = f"Take Cash (${npc.cash:.2f})"
            options["1"] = lbl
            buttons.append({"label": lbl, "key": "1"})
            
        if npc.weapon:
            lbl = f"Take {npc.weapon.name}"
            options["2"] = lbl
            buttons.append({"label": lbl, "key": "2"})
            
        if npc.hat:
            lbl = f"Take {npc.hat.name}"
            options["3"] = lbl
            buttons.append({"label": lbl, "key": "3"})
        
        # Check for Receipts
        receipts = [i for i in npc.inventory if i.item_type == ItemType.RECEIPT]
        if receipts:
            lbl = f"Loot Drafts ({len(receipts)})"
            options["4"] = lbl
            buttons.append({"label": lbl, "key": "4"})

        # Check for Badge
        if npc.archetype == "Sheriff" or npc.name == "Sheriff":
            lbl = "Take Badge"
            options["5"] = lbl
            buttons.append({"label": lbl, "key": "5"})

        options["B"] = "Leave Body"
        buttons.append({"label": "Leave Body", "key": "B"})
        
        renderer.render(
            log_text=log_lines,
            buttons=buttons
        )
        
        choice = renderer.get_input()
        
        if choice == "1" and npc.cash > 0:
            player.cash += npc.cash
            print(f"You took ${npc.cash:.2f}.")
            npc.cash = 0
            player.honor -= 2
            world.add_heat(5)
            # time.sleep(1)
        elif choice == "2" and npc.weapon:
            player.add_item(npc.weapon)
            print(f"You took the {npc.weapon.name}.")
            npc.weapon = None
            player.honor -= 10
            world.add_heat(15)
            # time.sleep(1)
        elif choice == "3" and npc.hat:
            player.add_item(npc.hat)
            print(f"You took the {npc.hat.name}.")
            npc.hat = None
            player.honor -= 10
            world.add_heat(10)
            # time.sleep(1)
        elif choice == "4" and receipts:
            for r in receipts:
                player.add_item(r)
            print(f"You took {len(receipts)} bank drafts.")
            npc.inventory = [i for i in npc.inventory if i.item_type != ItemType.RECEIPT]
            player.honor -= 5
            world.add_heat(10)
        elif choice == "5" and (npc.archetype == "Sheriff" or npc.name == "Sheriff"):
            print("You took the Sheriff's Badge.")
            # Add badge item?
            player.honor -= 20
            world.add_heat(50)
            # Remove badge from npc logic if implemented
        elif choice == "B":
            print("You leave the body.")
            break

def start_brawl(player, world, npc=None):
    if not npc: npc = NPC("Drunkard")
    
    print(f"\nYou get into a scrap with {npc.name} ({npc.archetype})!")
    wait_for_user("FIGHT ON!")
    
    # Create Combatants
    p1 = Combatant(player.name, -1, player)
    p2 = Combatant(npc.name, 1)
    # Sync NPC stats to Combatant
    p2.brawl_atk = npc.brawl_atk
    p2.brawl_def = npc.brawl_def
    p2.hp = npc.hp
    p2.max_hp = npc.max_hp
    
    engine = DuelEngineV2(p1, p2)
    
    # Simple Brawl Loop
    while p1.conscious and p2.conscious and p1.alive and p2.alive:
        # engine.render()
        renderer.render_duel_state(engine, p1, p2)
        
        # Player Action
        # print("\n[1] JAB (Off-hand, Fast)   [2] HOOK (Dominant, Strong)")
        # print("[3] BLOCK (Counters Jab, Weak to Hook)")
        # act = input("Action: ")
        
        brawl_buttons = [
            {"label": "JAB (Fast)", "key": "1"},
            {"label": "HOOK (Strong)", "key": "2"},
            {"label": "BLOCK", "key": "3"}
        ]
        
        renderer.render(
            stats_text=[f"{p1.name}: {p1.hp}/{p1.max_hp}", f"{p2.name}: {p2.hp}/{p2.max_hp}"],
            log_text=engine.log[-5:] if engine.log else ["Brawl started!"],
            buttons=brawl_buttons
        )
        
        act = renderer.get_input()
        
        if act == "1": p1_act = Action.JAB
        elif act == "2": p1_act = Action.HOOK
        elif act == "3": p1_act = Action.BLOCK
        else: p1_act = Action.WAIT
        
        # AI Action
        roll = random.random()
        if roll < 0.33: p2_act = Action.JAB
        elif roll < 0.66: p2_act = Action.HOOK
        else: p2_act = Action.BLOCK
        
        engine.run_turn(p1_act, p2_act)
        # time.sleep(1)
        
    # engine.render()
    renderer.render_duel_state(engine, p1, p2)
    p1.sync_state() # Save HP loss back to player
    
    # Capture final combat log
    final_log = engine.log[-3:] if engine.log else []
    
    if p1.conscious:
        print("\nYOU WON THE BRAWL!")
        
        log_lines = final_log + ["", "YOU WON THE BRAWL!"]
        if not p2.alive and npc:
            npc.alive = False
            print("You beat them to death!")
            log_lines.append("You beat them to death!")
            player.honor -= 20
            world.add_heat(20)

        player.reputation += 1
        wait_for_user(log_lines, player=player)
        
        # Loot Chance
        renderer.render(
            log_text=["Loot them? (Y/N)"],
            buttons=[{"label": "Loot", "key": "Y"}, {"label": "Leave", "key": "N"}]
        )
        
        if renderer.get_input() == "Y":
            loot_screen(player, world, npc)
        
        # Crime Consequence
        town = world.get_town()
        sheriff_active = town and town.sheriff and town.sheriff.alive
        
        if not p2.alive and sheriff_active:
             wait_for_user(["The Sheriff steps in!", "He saw the whole thing."], player=player)
             handle_crime(player, world, "manslaughter")
        else:
            # Normal Disturbing Peace Check
            heat = world.get_local_heat()
            if random.randint(0, 100) < heat:
                wait_for_user("The Sheriff is approaching...", player=player)
                handle_crime(player, world, "disturbing the peace")
            
    else:
        print("\nYou were knocked out...")
        
        log_lines = final_log + ["", "You were knocked out..."]
        renderer.render(log_text=log_lines, player=player)
        time.sleep(2)
        loss = random.randint(1, 5)
        player.cash = max(0, player.cash - loss)
        print(f"You wake up with ${loss} less.")
        
        # Knockout Consequences
        world.week += 1
        if player.weeks_rent_paid > 0:
            player.weeks_rent_paid -= 1
            player.hp = min(player.max_hp, player.hp + 10) # Some recovery
            renderer.render(log_text=[f"You wake up in your room.", f"Lost ${loss}. Week passed."], player=player)
        else:
            player.hp = min(player.max_hp, player.hp + 5)
            renderer.render(log_text=[f"You wake up in the dirt.", f"Lost ${loss}. Week passed."], player=player)
            
        wait_for_user()
        return # End brawl function
        
    wait_for_user()

def start_duel(player, world, npc=None, is_sheriff=False):
    if not npc: 
        npc = NPC("Sheriff" if is_sheriff else "Outlaw")
        
    wait_for_user([f"You challenge {npc.name} ({npc.archetype}) to a duel!", "WALK OUT"], player=player)
    
    p1 = Combatant(player.name, -1, player)
    p2 = Combatant(npc.name, 1)
    p2.acc = npc.acc
    p2.spd = npc.spd
    p2.hp = npc.hp
    p2.max_hp = npc.max_hp
    # Give NPC their weapon
    # Note: Combatant doesn't fully support custom weapons yet in logic, but stats are passed
    
    engine = DuelEngineV2(p1, p2)
    
    # Duel Loop
    turn_count = 0
    while p1.alive and p2.alive and turn_count < 20:
        # engine.render()
        renderer.render_duel_state(engine, p1, p2)
        
        # Check if opponent surrendered in PREVIOUS turn
        if p2.is_surrendering:
            
            surrender_buttons = [
                {"label": "Accept Surrender", "key": "1"},
                {"label": "Demand Loot", "key": "2"},
                {"label": "Ignore & Attack", "key": "3"}
            ]
            renderer.render(
                log_text=[f"{p2.name} is asking for mercy!", "Choose fate..."],
                buttons=surrender_buttons
            )
            
            sub = renderer.get_input()
            if sub == "1":
                wait_for_user(["You lower your weapon."], player=player)
                p2.conscious = False # End loop gracefully
                break
            elif sub == "2":
                # Check if they agree?
                if random.random() < 0.8:
                    wait_for_user([f"You demand their valuables.", f"{p2.name}: 'Fine! Take it!'"], player=player)
                    loot_screen(player, world, npc)
                    p2.conscious = False
                    break
                else:
                    wait_for_user([f"You demand their valuables.", f"{p2.name}: 'Never!'"], player=player)
                    p2.is_surrendering = False # They fight on!
            elif sub == "3":
                wait_for_user(["You ignore their plea."], player=player)
                player.honor -= 5
                # Continue to action selection
        
        # Player Menu
        # print("\n[1] PACE   [2] TURN   [3] DRAW   [4] SHOOT CENTER")
        # print("[5] SHOOT HIGH [6] SHOOT LOW [7] RELOAD [8] DUCK")
        # print("[9] SURRENDER [0] STEP IN [J] JUMP")
        
        special = "[D] DUCK&SHOOT [R] RISE&SHOOT"
        if p1.orientation == Orientation.FACING_OPPONENT and engine.get_distance() <= 3:
            special += " [K] SAND"
        if engine.get_distance() <= 2:
            special += " [P] PUNCH"
        # print(special)
        
        # Define primary buttons for GUI (limited space)
        duel_buttons = [
            {"label": "SHOOT CENTER", "key": "4"},
            {"label": "DRAW / RELOAD", "key": "3/7"},
            {"label": "PACE / TURN", "key": "1/2"},
            {"label": "DUCK / JUMP", "key": "8/J"}
        ]
        
        log_lines = engine.log[-3:] if engine.log else ["Duel started."]
        log_lines.append("Actions: [1]Pace [2]Turn [3]Draw [4]Shoot")
        log_lines.append("         [5]High [6]Low [7]Reload [8]Duck")
        log_lines.append(f"Special: {special}")
        
        renderer.render(
            stats_text=[f"{p1.name}: {p1.hp} HP | {p1.ammo} Ammo", f"{p2.name}: {p2.hp} HP"],
            log_text=log_lines,
            buttons=duel_buttons
        )
        
        choice = renderer.get_input()
        
        map_act = {
            "1": Action.PACE, "2": Action.TURN, "3": Action.DRAW,
            "4": Action.SHOOT_CENTER, "5": Action.SHOOT_HIGH,
            "6": Action.SHOOT_LOW, "7": Action.RELOAD, "8": Action.DUCK,
            "9": Action.SURRENDER, "0": Action.STEP_IN, "J": Action.JUMP,
            "D": Action.DUCK_FIRE, "R": Action.STAND_FIRE, "K": Action.KICK_SAND,
            "P": Action.PUNCH
        }
        p1_act = map_act.get(choice, Action.WAIT)
        
        # AI (Cheater or Honorable?)
        p2_act = ai_honorable(p2, p1, engine)
        
        engine.run_turn(p1_act, p2_act)
        
        # Check if Player Surrendered and AI Accepted
        if p1.is_surrendering and p2_act == Action.WAIT:
            print(f"\n{p2.name} accepts your surrender.")
            renderer.render(log_text=[f"{p2.name} accepts your surrender."])
            p1.conscious = False # End loop
            # Consequences?
            loss = random.randint(5, 15)
            player.cash = max(0, player.cash - loss)
            print(f"They took ${loss} from you.")
            break
            
        turn_count += 1
        # time.sleep(1.5)
        
    p1.sync_state()
    renderer.render_duel_state(engine, p1, p2)
    
    # Capture final combat log
    final_log = engine.log[-3:] if engine.log else []
    
    # Check Surrender (Post-Loop)
    if p2.is_surrendering and p1.alive:
        print(f"\n{npc.name} has SURRENDERED!")
        
        surrender_buttons = [
            {"label": "Execute", "key": "1"},
            {"label": "Let go", "key": "2"}
        ]
        if player.is_gang_leader or player.is_deputy:
            surrender_buttons.append({"label": "Recruit", "key": "3"})
            
        renderer.render(
            log_text=final_log + [f"{npc.name} has SURRENDERED!", "Choose fate..."],
            buttons=surrender_buttons
        )
            
        choice = renderer.get_input()
        if choice == "1":
            print("You pull the trigger.")
            npc.alive = False
            player.honor -= 10
            world.add_heat(20)
        elif choice == "3" and (player.is_gang_leader or player.is_deputy):
            # Recruit Attempt
            # Difficulty based on alignment?
            diff = 50
            if npc.alignment == "Lawful" and player.is_gang_leader: diff += 30
            if npc.alignment == "Chaotic" and player.is_deputy: diff += 30
            
            roll = player.charm * 10 + random.randint(0, 50)
            if roll > diff:
                print(f"{npc.name}: 'Alright, I'm with you.'")
                if player.is_gang_leader:
                    player.gang.append(npc)
                    print("Joined Gang.")
                else:
                    print("Sheriff: 'I'll process him as a new deputy.'")
                    # Maybe add to a deputy list? For now just flavor.
            else:
                print(f"{npc.name}: 'I'd rather die!'")
        else:
            print("You let them run.")
            
    elif p1.alive and not p2.alive:
        print("\nVICTORY!")
        
        log_lines = final_log + ["", "VICTORY!"]
        if npc: npc.alive = False # Mark NPC as dead
        
        if is_sheriff or npc.archetype == "Sheriff":
            print("YOU KILLED THE SHERIFF! You are now a WANTED MAN.")
            log_lines.append("YOU KILLED THE SHERIFF!")
            log_lines.append("You are now a WANTED MAN.")
            player.bounty += 100.00
            player.honor -= 50
            world.add_heat(100)
        else:
            player.honor -= 5 
            player.reputation += 10
            
        wait_for_user(log_lines, player=player)
            
        if not (is_sheriff or npc.archetype == "Sheriff"):
            renderer.render(
                log_text=["Loot them? (Y/N)"],
                buttons=[{"label": "Loot", "key": "Y"}, {"label": "Leave", "key": "N"}]
            )
            if renderer.get_input() == "Y":
                loot_screen(player, world, npc)

    elif not p1.alive:
        print("\nDEFEAT.")
        renderer.render(log_text=final_log + ["", "DEFEAT."])
        
    wait_for_user()

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
    
    if choice == "1":
        new_player, new_world = new_game(existing_world=world)
        game_loop(new_player, new_world)
    elif choice == "2":
        new_player, new_world = new_game()
        game_loop(new_player, new_world)
    else:
        sys.exit()

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
                
                update_world_simulation(world)
                process_healing(player)
                
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
            if player.weeks_rent_paid > 0:
                player.weeks_rent_paid -= 1
                log_lines.append("Rent paid for 1 week.")
                
            world.reduce_heat(5) # Good honest work reduces heat
            # print("You earned $2.00. People respect honest work. (+1 Honor)")
            log_lines.append("You earned $2.00. (+1 Honor)")
            
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
            if player.weeks_rent_paid > 0:
                player.weeks_rent_paid -= 1
                log_lines.append("Rent paid for 1 week.")
                
            world.reduce_heat(5)
            # print("You earned $3.00. (+1 Honor)")
            log_lines.append("You earned $3.00. (+1 Honor)")
            
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
    if player.weeks_rent_paid > 0:
        player.weeks_rent_paid -= 1
        log_lines.append("Rent paid for 1 week.")
        
    player.cash += 5.00
    world.reduce_heat(10) # Deputies lower town heat
    
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

def handle_crime(player, world, crime_name):
    print(f"\nYOU ARE CAUGHT {crime_name.upper()}!")
    print("The Sheriff draws his gun.")
    
    renderer.render(
        log_text=[f"CAUGHT {crime_name.upper()}!", "Sheriff draws his gun.", "Surrender? (Y/N)"], 
        player=player,
        buttons=[{"label": "Surrender", "key": "Y"}, {"label": "Resist", "key": "N"}]
    )
    
    # if input("Surrender? (Y/N): ").upper() == "Y":
    if renderer.get_input() == "Y":
        if crime_name == "manslaughter":
            fine = 250.0
            jail_time = 52
            log_msg = ["Convicted of Manslaughter.", f"Jailed for {jail_time} weeks.", f"Fined ${fine:.2f}."]
        else:
            fine = world.get_local_heat() * 1.5
            jail_time = 1
            log_msg = ["Jailed for a week.", f"Fined ${fine:.2f}."]

        print(f"You are thrown in jail for {jail_time} week(s) and fined ${fine:.2f}.")
        
        # Payment Logic
        paid_in_full = False
        
        # 1. Pay from Cash
        if player.cash >= fine:
            player.cash -= fine
            paid_in_full = True
        else:
            fine -= player.cash
            player.cash = 0.0
            
            # 2. Pay from Bank
            if player.bank_balance >= fine:
                player.bank_balance -= fine
                paid_in_full = True
                log_msg.append("Bank account garnished.")
            else:
                fine -= player.bank_balance
                player.bank_balance = 0.0
                
                # 3. Work it off at Stables
                # Rate: $10/week
                labor_weeks = max(1, int(fine / 10))
                jail_time += labor_weeks
                log_msg.append("Unable to pay fine.")
                log_msg.append(f"Sentenced to {labor_weeks} weeks labor at Stables.")
        
        world.week += jail_time
        if player.weeks_rent_paid > 0:
            player.weeks_rent_paid = max(0, player.weeks_rent_paid - jail_time)
            
        world.reduce_heat(20)
        wait_for_user(log_msg, player=player)
    else:
        start_duel(player, world, is_sheriff=True)

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

def update_world_simulation(world):
    # 1. Spawn new NPCs if low
    if len(world.active_npcs) < 5:
        if random.random() < 0.5:
            new_npc = NPC(random.choice(["Outlaw", "Cowboy", "Sheriff"]))
            towns = list(world.towns.keys())
            new_npc.location = random.choice(towns)
            world.active_npcs.append(new_npc)
            
    # 2. Move NPCs / Generate Events
    world.rumors = [] # Clear old rumors
    for npc in world.active_npcs:
        if not npc.alive: continue
        
        # Move?
        if random.random() < 0.3:
            neighbors = list(world.map.get(npc.location, {}).keys())
            if neighbors:
                npc.location = random.choice(neighbors)
        
        # Event?
        if npc.archetype == "Outlaw" and random.random() < 0.4:
            # Crime!
            npc.bounty += random.randint(10, 50)
            npc.rumor = f"{npc.name} robbed a traveler near {npc.location}."
            world.rumors.append(npc.rumor)
            # Increase town heat?
            if npc.location in world.towns:
                world.towns[npc.location].heat = min(100, world.towns[npc.location].heat + 5)
                
        elif npc.archetype == "Sheriff" and random.random() < 0.3:
            npc.rumor = f"{npc.name} is hunting outlaws in {npc.location}."
            world.rumors.append(npc.rumor)
            
        else:
            # Just hanging out
            npc.rumor = f"{npc.name} was seen drinking in {npc.location}."
            world.rumors.append(npc.rumor)

    # 3. Generic Rumors
    generic_rumors = [
        "Gold was found in the hills near Brimstone.",
        "The railroad is coming... eventually.",
        "Indians were spotted on the ridge.",
        "A storm is brewing in the north."
    ]
    world.rumors.append(random.choice(generic_rumors))
    
    # 4. Rival Gangs
    process_rival_gangs(world)

def visit_mayor(player, world):
    town = world.get_town()
    while True:
        render_hud(player, world)
        print(f"\n=== TOWN HALL: {town.name.upper()} ===")
        
        if town.player_is_mayor:
            print("You sit at the Mayor's desk.")
            print(f"Town Influence: {town.influence}%")
            print(f"Town Treasury: High") # Placeholder
            
            options = {
                "1": "Collect Taxes (+$50, +Heat)",
                "2": "Hire Sheriff (Cost $50)",
                "3": "Host Gala (Cost $100, +Rep)",
                "B": "Back"
            }
            
            choice = get_menu_choice(options)
            if choice == "1":
                print("You squeeze the locals for cash.")
                player.cash += 50
                town.heat += 20
                town.influence -= 5
                time.sleep(1)
            elif choice == "B":
                break
            # TODO: Implement others
            
        elif town.mayor_status == "Dead":
            print("The Mayor's office is empty. The previous mayor was killed.")
            print("The town is in chaos.")
            
            options = {
                "1": "Declare Martial Law (Take Over)",
                "2": "Call for Special Election (Restore Order)",
                "B": "Back"
            }
            
            choice = get_menu_choice(options)
            if choice == "1":
                if player.reputation > 50 or len(player.gang) > 3:
                    print("You slam your gun on the desk. 'I'm in charge now.'")
                    town.player_is_mayor = True
                    town.mayor_status = "Alive" # You are the mayor
                    town.influence = 50
                else:
                    print("The townsfolk laugh you out of the office.")
                    time.sleep(1)
            elif choice == "2":
                print("You organize a town meeting to elect a new mayor.")
                if random.random() < 0.8:
                    new_mayor = NPC("Mayor")
                    town.mayor = new_mayor
                    town.mayor_status = "Alive"
                    print(f"The town has elected {new_mayor.name} as the new Mayor.")
                    print(f"Personality: {new_mayor.personality}")
                    player.reputation += 10
                    player.honor += 10
                else:
                    print("The meeting ends in a brawl! No mayor elected.")
                    start_brawl(player, world, NPC("Drunkard"))
                time.sleep(1)
            elif choice == "B":
                break
                
        else:
            # Use Persistent Mayor
            mayor = town.mayor
            if not mayor: # Fallback
                mayor = NPC("Mayor")
                town.mayor = mayor
                
            print(f"Mayor {mayor.name} looks up from his paperwork.")
            print(f"Personality: {mayor.personality} ({mayor.personality_data.get('desc', '')})")
            
            if town.mayor_status == "Bribed":
                print(f"{mayor.name}: 'I'm looking the other way, as agreed.'")
            else:
                print(f"{mayor.name}: '{mayor.get_line()}'")
                
            # Calculate Bribe Cost
            base_bribe = 50.0
            bribe_mod = mayor.personality_data.get("bribe_cost_mod", 1.0)
            bribe_cost = base_bribe * bribe_mod
            
            options = {}
            if bribe_cost < 500:
                options["1"] = f"Bribe (${bribe_cost:.2f}) - Ignore Crimes for 1 Week"
            else:
                options["1"] = "Bribe (Impossible)"
                
            options["2"] = "Intimidate (Req: High Rep/Gang)"
            options["3"] = "Kill Him"
            options["B"] = "Back"
            
            if player.reputation > 80 and not player.is_gang_leader:
                options["4"] = "Run for Mayor (Election)"
            
            if player.is_gang_leader:
                options["5"] = "Demand Protection (Racket)"
                options["6"] = "Attempt Takeover (War)"
            
            choice = get_menu_choice(options)
            
            if choice == "1":
                if bribe_cost >= 500:
                    print(f"{mayor.name}: 'I am a man of principle! Get out!'")
                elif player.cash >= bribe_cost:
                    player.cash -= bribe_cost
                    town.mayor_status = "Bribed"
                    print(f"{mayor.name}: 'A pleasure doing business.'")
                    town.heat = 0 # Reset heat temporarily
                else:
                    print(f"{mayor.name}: 'Get out, pauper.'")
                time.sleep(1)
                
            elif choice == "2":
                # Intimidate
                power = player.reputation + (len(player.gang) * 10)
                diff_mod = mayor.personality_data.get("intimidate_diff", 0)
                difficulty = 60 + diff_mod
                
                if power > difficulty:
                    print("You threaten the Mayor.")
                    print(f"{mayor.name}: 'Okay! Okay! Just don't hurt me!'")
                    town.mayor_status = "Bribed"
                    town.influence += 10
                else:
                    print(f"{mayor.name}: 'Guards! Remove this ruffian!'")
                    start_brawl(player, world, town.sheriff if town.sheriff else NPC("Sheriff"))
                time.sleep(1)
                
            elif choice == "3":
                print("You draw your weapon!")
                # Mayor has guards?
                guards = [town.sheriff if town.sheriff else NPC("Sheriff")]
                engine = ShootoutEngine([player] + player.gang, guards + [mayor])
                while True:
                    engine.render()
                    if not engine.run_turn(): break
                    time.sleep(1)
                
                process_gang_casualties(player, world)
                
                if player.alive:
                    if not mayor.alive:
                        print("The Mayor is dead.")
                        town.mayor_status = "Dead"
                        player.honor -= 50
                        world.add_heat(100)
                    else:
                        print("The Mayor escaped!")
                else:
                    print("You failed to kill the Mayor.")
                    
            elif choice == "4":
                print("You start your campaign...")
                # Simple check for now
                if random.random() < 0.7:
                    print("The people love you! You win the election!")
                    town.player_is_mayor = True
                else:
                    print("You lost the election.")
                time.sleep(1)
            
            elif choice == "5":
                demand_protection(player, world)
                
            elif choice == "6":
                attempt_takeover(player, world)
                
            elif choice == "B":
                break

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

def demand_protection(player, world):
    town = world.get_town()
    print(f"\n=== DEMAND PROTECTION: {town.name} ===")
    
    if len(player.gang) < 2:
        print("You need a gang to run a protection racket.")
        time.sleep(1)
        return

    # Calculate Intimidation
    intimidation = (len(player.gang) * 10) + player.reputation
    if player.is_gang_leader: intimidation += 20
    
    print(f"Gang Intimidation: {intimidation}")
    print(f"Town Lawfulness: {town.lawfulness}")
    
    if "Protection" in town.rackets:
        print("You are already running protection here.")
        time.sleep(1)
        return

    if intimidation > town.lawfulness:
        print("The Mayor crumbles under your threat.")
        print("'Fine! We'll pay! Just keep the violence down.'")
        town.rackets.append("Protection")
        player.reputation += 5
        player.honor -= 10
        print("Racket Established: Protection (Weekly Income)")
    else:
        print("The Mayor stands firm.")
        print("'We don't bow to thugs like you! Sheriff!'")
        world.add_heat(30)
        start_brawl(player, world, NPC("Sheriff"))

def attempt_takeover(player, world):
    town = world.get_town()
    print(f"\n=== TOWN TAKEOVER: {town.name} ===")
    
    if len(player.gang) < 3:
        print("You need a larger gang (3+) to take over a town.")
        time.sleep(1)
        return
        
    print("You are about to wage war for control of the streets.")
    print("Goal: Push the battle line and eliminate resistance.")
    
    if input("Begin Attack? (Y/N): ").upper() != "Y":
        return
        
    # Setup Teams
    # Player Team: Player + Gang
    player_team = [player] + player.gang
    
    # Enemy Team: Sheriff + Deputies + Armed Citizens
    defenders = 3 + (town.lawfulness // 20)
    if "Fortified" in town.traits: defenders += 2
    
    enemy_team = [NPC("Sheriff")] + [NPC("Cowboy") for _ in range(defenders)]
    
    print(f"Defenders: {len(enemy_team)}")
    
    engine = ShootoutEngine(player_team, enemy_team, mode="takeover")
    
    while True:
        engine.render()
        cont = engine.run_turn()
        time.sleep(1.5)
        if not cont:
            break
            
    engine.render()
    
    process_gang_casualties(player, world)
    
    # Check Victory
    # If player alive and enemies dead
    enemies_alive = any(e.alive for e in enemy_team)
    
    if player.alive and not enemies_alive:
        print("\nVICTORY! The town is yours!")
        town.player_is_mayor = True
        town.mayor_status = "Puppet"
        town.gang_control = True # Anarchy/Gang Rule
        town.rackets.append("Total Control")
        player.reputation += 50
        player.honor -= 50
        
        # Loot
        loot = 500
        if "Rich" in town.traits: loot = 1000
        if "Poor" in town.traits: loot = 100
        print(f"You seize the town treasury: ${loot}")
        player.cash += loot
        
    elif player.alive:
        print("\nThe attack failed! You retreat.")
        world.add_heat(50)
    else:
        print("\nYou died in the street war.")

def bail_member(player, world):
    town = world.get_town()
    print(f"\n=== TOWN JAIL: {town.name} ===")
    
    if not town.jail:
        print("The cells are empty.")
        time.sleep(1)
        return
        
    print("Inmates:")
    for i, member in enumerate(town.jail):
        print(f"{i+1}. {member.name} (Bail: $50.00)")
        
    print("B. Back")
    
    choice = input("Choice: ").upper()
    if choice == "B": return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(town.jail):
            member = town.jail[idx]
            if player.cash >= 50:
                player.cash -= 50
                town.jail.pop(idx)
                player.gang.append(member)
                print(f"You bailed out {member.name}.")
            else:
                print("Not enough cash.")
    except: pass

def process_gang_casualties(player, world):
    town = world.get_town()
    # Check for dead gang members
    # We need to iterate a copy because we might remove them
    for member in list(player.gang):
        if not member.alive:
            # 50% chance to be captured if in a town with a jail (Lawfulness > 0)
            if town.lawfulness > 0 and random.random() < 0.5:
                print(f"{member.name} was wounded and CAPTURED by the law!")
                member.alive = True # They survive
                member.hp = int(member.max_hp / 2) # Heal partially
                town.jail.append(member)
                player.gang.remove(member)
            else:
                print(f"{member.name} died in the shootout.")
                player.gang.remove(member)

def generate_rival_gang(world):
    # Gang Name Generator
    adjectives = ["Red", "Black", "Dead", "Wild", "Bloody", "Iron", "Night", "Dusty"]
    nouns = ["Sash", "Hand", "Riders", "Skulls", "Coyotes", "Vipers", "Ghosts", "Dogs"]
    
    leader = NPC("Outlaw")
    leader.traits.append("Leader") # Flavor trait
    leader.bounty = random.randint(100, 500)
    
    # Name format: "The [Adj] [Noun]" or "[Leader]'s Gang"
    if random.random() < 0.5:
        name = f"The {random.choice(adjectives)} {random.choice(nouns)}"
    else:
        name = f"{leader.name.split()[-1]}'s Gang"
        
    # Hideout
    towns = list(world.towns.keys())
    hideout = random.choice(towns)
    
    gang = Gang(name, leader, hideout)
    
    # Members
    for _ in range(random.randint(2, 5)):
        member = NPC("Outlaw")
        member.location = hideout
        gang.members.append(member)
        
    world.rival_gangs.append(gang)
    world.rumors.append(f"Rumor has it {name} has set up near {hideout}.")

def process_rival_gangs(world):
    for gang in world.rival_gangs:
        if not gang.active: continue
        
        # 1. Move?
        if random.random() < 0.3:
            neighbors = list(world.map.get(gang.hideout, {}).keys())
            if neighbors:
                gang.hideout = random.choice(neighbors)
                # Move members
                gang.leader.location = gang.hideout
                for m in gang.members:
                    m.location = gang.hideout
                    
        # 2. Action?
        if random.random() < 0.4:
            action_roll = random.random()
            town = world.towns.get(gang.hideout)
            
            if action_roll < 0.5:
                # Robbery
                loot = random.randint(50, 200)
                gang.cash += loot
                gang.reputation += 5
                gang.leader.bounty += 20
                if town:
                    town.heat = min(100, town.heat + 10)
                world.rumors.append(f"{gang.name} robbed a store in {gang.hideout}.")
                
            elif action_roll < 0.8:
                # Shootout with Law
                if town and town.lawfulness > 20:
                    # Abstract result
                    if random.random() < 0.5:
                        # Gang wins
                        town.heat += 20
                        world.rumors.append(f"{gang.name} drove off the law in {gang.hideout}!");
                    else:
                        # Gang loses member
                        if gang.members:
                            dead = gang.members.pop()
                            world.rumors.append(f"A member of {gang.name} was killed in {gang.hideout}.")
                        else:
                            # Leader killed?
                            if random.random() < 0.3:
                                gang.active = False
                                world.rumors.append(f"{gang.leader.name} of {gang.name} was killed! The gang has disbanded.")
            
            else:
                # Recruitment
                if len(gang.members) < 8:
                    new_member = NPC("Outlaw")
                    new_member.location = gang.hideout
                    gang.members.append(new_member)
                    world.rumors.append(f"{gang.name} is recruiting in {gang.hideout}.")

if __name__ == "__main__":
    main_menu()
