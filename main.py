import sys
import time
import random
from game_state import PlayerState, WorldState, Item, ItemType, AVAILABLE_HORSES, AVAILABLE_WEAPONS, AVAILABLE_HATS
from ui import render_hud, get_menu_choice, clear_screen
from duel_engine_v2 import DuelEngineV2, Combatant, Action, Orientation, ai_cheater, ai_honorable, ai_brawler
from shootout_engine import ShootoutEngine
from characters import NPC

def main():
    # Initialize Game
    world = WorldState()
    player = PlayerState("The Stranger")
    
    # Starting Gear
    player.cash = 12.50
    player.ammo = 6
    # Debug/Cheat for testing
    # player.reputation = 25 
    # player.cash = 50.00
    
    while player.alive:
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
            if player.is_gang_leader:
                print("\nYou slip out of town and ride to your hideout.")
                player.location = "Wilderness Camp"
                time.sleep(1)
            else:
                sleep(player, world)
        elif choice == "7":
            travel_menu(player, world)
        elif choice == "8":
            visit_mayor(player, world)
        elif choice == "9":
            visit_bank(player, world)
        elif choice == "Q":
            sys.exit()
            
    print("\n\n YOU HAVE DIED.")
    print(f" Name: {player.name}")
    print(f" Cash: ${player.cash:.2f}")
    print(f" Honor: {player.honor}")
    input("Press Enter to exit...")

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
            weeks = max(1, round(dist / (speed * 5))) # Rough calc
            
            method = f"Ride {player.horse.name}" if player.horse else "Walk"
            opts[str(i+1)] = f"{dest} ({dist} miles) - {method}: ~{weeks} Weeks"
            
        opts["B"] = "Back"
        
        choice = get_menu_choice(opts)
        
        if choice == "B":
            break
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(destinations):
                dest = destinations[idx]
                dist = neighbors[dest]
                speed = player.horse.stats.get("spd", 5) if player.horse else 2
                weeks = max(1, round(dist / (speed * 5)))
                
                print(f"\nDeparting for {dest}...")
                # Travel Event Loop?
                for w in range(weeks):
                    print(f"Week {w+1} on the trail...")
                    time.sleep(0.5)
                    world.week += 1
                    update_world_simulation(world)
                    # Random Event Chance
                    if random.random() < 0.2:
                        print("You encounter a stranger on the road.")
                        npc = NPC("Outlaw" if random.random() < 0.3 else "Cowboy")
                        print(f"{npc.name} ({npc.archetype}): '{npc.get_line()}'")
                        if npc.archetype == "Outlaw":
                            if input("Fight? (Y/N): ").upper() == "Y":
                                start_duel(player, world, npc)
                
                world.town_name = dest
                print(f"\nArrived in {dest}.")
                time.sleep(1)
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
                
            input("Defend yourself! (Press Enter)")
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
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            if player.cash >= 0.50:
                player.cash -= 0.50
                print("\nYou down the whiskey. It burns.")
                player.hp = min(player.max_hp, player.hp + 5)
                time.sleep(1)
            else:
                print("\nBartender: 'No money, no drink.'")
                time.sleep(1)
                
        elif choice == "2":
            print("\n=== RUMORS ===")
            if not world.rumors:
                print("It's quiet. Too quiet.")
            else:
                for r in world.rumors:
                    print(f"- {r}")
            
            # Mingle with Locals
            locals_here = [n for n in world.active_npcs if n.location == world.town_name]
            if locals_here:
                print("\n=== NOTABLE PEOPLE ===")
                for i, n in enumerate(locals_here):
                    print(f"{i+1}. Talk to {n.name} ({n.archetype})")
                
                print("M. Mingle")
                sub = input("Choice: ").upper()
                if sub == "M":
                    pass # Just looking
                else:
                    try:
                        idx = int(sub) - 1
                        if 0 <= idx < len(locals_here):
                            target = locals_here[idx]
                            print(f"\nYou approach {target.name}.")
                            print(f"{target.name}: '{target.get_line()}'")
                            
                            if target.bounty > 0:
                                print(f"(Wanted: ${target.bounty:.2f})")
                                if input("Attempt to arrest/kill? (Y/N): ").upper() == "Y":
                                    start_duel(player, world, target)
                                    if player.alive and not target.alive:
                                        print(f"You collected the bounty of ${target.bounty:.2f}!")
                                        player.cash += target.bounty
                                        player.reputation += 10
                                        world.active_npcs.remove(target)
                    except: pass
            
            input("Press Enter...")
        
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
        clear_screen()
        print(f"\n=== LOOTING {npc.name.upper()} ===")
        print("Taking items is considered theft and dishonorable.")
        
        options = {}
        if npc.cash > 0:
            options["1"] = f"Take Cash (${npc.cash:.2f}) - Minor Dishonor"
        if npc.weapon:
            options["2"] = f"Take Weapon ({npc.weapon.name}) - Major Dishonor"
        if npc.hat:
            options["3"] = f"Take Hat ({npc.hat.name}) - Major Dishonor"
        
        # Check for Receipts
        receipts = [i for i in npc.inventory if i.item_type == ItemType.RECEIPT]
        if receipts:
            options["4"] = f"Loot Bank Drafts ({len(receipts)} found)"

        options["B"] = "Leave Body"
        
        choice = get_menu_choice(options)
        
        if choice == "1" and npc.cash > 0:
            player.cash += npc.cash
            print(f"You took ${npc.cash:.2f}.")
            npc.cash = 0
            player.honor -= 2
            world.add_heat(5)
            time.sleep(1)
        elif choice == "2" and npc.weapon:
            player.add_item(npc.weapon)
            print(f"You took the {npc.weapon.name}.")
            npc.weapon = None
            player.honor -= 10
            world.add_heat(15)
            time.sleep(1)
        elif choice == "3" and npc.hat:
            player.add_item(npc.hat)
            print(f"You took the {npc.hat.name}.")
            npc.hat = None
            player.honor -= 10
            world.add_heat(10)
            time.sleep(1)
        elif choice == "4" and receipts:
            for r in receipts:
                player.add_item(r)
                print(f"You took {r.name}.")
            npc.inventory = [i for i in npc.inventory if i.item_type != ItemType.RECEIPT]
            player.honor -= 5
            time.sleep(1)
        elif choice == "B":
            break

def start_brawl(player, world, npc=None):
    if not npc: npc = NPC("Drunkard")
    
    print(f"\nYou get into a scrap with {npc.name} ({npc.archetype})!")
    input("FIGHT ON! (Press Enter)")
    
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
        engine.render()
        
        # Player Action
        print("\n[1] JAB (Off-hand, Fast)   [2] HOOK (Dominant, Strong)")
        print("[3] BLOCK/WAIT")
        act = input("Action: ")
        
        if act == "1": p1_act = Action.JAB
        elif act == "2": p1_act = Action.HOOK
        else: p1_act = Action.WAIT
        
        # AI Action
        roll = random.random()
        if roll < 0.4: p2_act = Action.JAB
        elif roll < 0.7: p2_act = Action.HOOK
        else: p2_act = Action.WAIT
        
        engine.run_turn(p1_act, p2_act)
        time.sleep(1)
        
    engine.render()
    p1.sync_state() # Save HP loss back to player
    
    if p1.conscious:
        print("\nYOU WON THE BRAWL!")
        if not p2.alive and npc:
            npc.alive = False
            print("You beat them to death!")
            player.honor -= 20
            world.add_heat(20)

        player.reputation += 1
        
        # Loot Chance
        if input("Loot them? (Y/N): ").upper() == "Y":
            loot_screen(player, world, npc)
        
        # Crime Consequence (Heat based)
        heat = world.get_local_heat()
        if random.randint(0, 100) < heat:
            input("The Sheriff is approaching... (Press Enter)")
            handle_crime(player, world, "disturbing the peace")
            
    else:
        print("\nYou were knocked out...")
        loss = random.randint(1, 5)
        player.cash = max(0, player.cash - loss)
        print(f"You wake up with ${loss} less.")
        
    input("Press Enter...")

def start_duel(player, world, npc=None, is_sheriff=False):
    if not npc: 
        npc = NPC("Sheriff" if is_sheriff else "Outlaw")
        
    print(f"\nYou challenge {npc.name} ({npc.archetype}) to a duel!")
    input("WALK OUT (Press Enter)")
    
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
        engine.render()
        
        # Check if opponent surrendered in PREVIOUS turn
        if p2.is_surrendering:
            print(f"\n{p2.name} is asking for mercy!")
            print("[1] Accept Surrender (End Fight)")
            print("[2] Demand Loot (Conditional)")
            print("[3] Ignore & Attack (Dishonorable)")
            
            sub = input("Choice: ")
            if sub == "1":
                print("You lower your weapon.")
                p2.conscious = False # End loop gracefully
                break
            elif sub == "2":
                print("You demand their valuables.")
                # Check if they agree?
                if random.random() < 0.8:
                    print(f"{p2.name}: 'Fine! Take it!'")
                    loot_screen(player, world, npc)
                    p2.conscious = False
                    break
                else:
                    print(f"{p2.name}: 'Never!'")
                    p2.is_surrendering = False # They fight on!
            elif sub == "3":
                print("You ignore their plea.")
                player.honor -= 5
                # Continue to action selection
        
        # Player Menu
        print("\n[1] PACE   [2] TURN   [3] DRAW   [4] SHOOT CENTER")
        print("[5] SHOOT HIGH [6] SHOOT LOW [7] RELOAD [8] DUCK")
        print("[9] SURRENDER [0] STEP IN [J] JUMP")
        
        special = "[D] DUCK & SHOOT [R] RISE & SHOOT"
        if p1.orientation == Orientation.FACING_OPPONENT and engine.get_distance() <= 3:
            special += " [K] KICK SAND"
        if engine.get_distance() <= 2:
            special += " [P] PUNCH"
        print(special)
        
        choice = input("Action: ").upper()
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
            p1.conscious = False # End loop
            # Consequences?
            loss = random.randint(5, 15)
            player.cash = max(0, player.cash - loss)
            print(f"They took ${loss} from you.")
            break
            
        turn_count += 1
        time.sleep(1.5)
        
    p1.sync_state()
    
    # Check Surrender (Post-Loop)
    if p2.is_surrendering and p1.alive:
        print(f"\n{npc.name} has SURRENDERED!")
        print("1. Execute")
        print("2. Let go")
        if player.is_gang_leader or player.is_deputy:
            print("3. Recruit")
            
        choice = input("Choice: ")
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
        if npc: npc.alive = False # Mark NPC as dead
        
        if is_sheriff or npc.archetype == "Sheriff":
            print("YOU KILLED THE SHERIFF! You are now a WANTED MAN.")
            player.bounty += 100.00
            player.honor -= 50
            world.add_heat(100)
        else:
            player.honor -= 5 
            player.reputation += 10
            
            if input("Loot them? (Y/N): ").upper() == "Y":
                loot_screen(player, world, npc)

    elif not p1.alive:
        print("\nDEFEAT.")
        
    input("Press Enter...")



def visit_doctor(player, world):
    clear_screen()
    print("DOCTOR")
    
    # Heal HP
    if player.hp < player.max_hp:
        cost = (player.max_hp - player.hp) * 0.1
        print(f"Heal Wounds (HP) to full for ${cost:.2f}?")
        if input("Y/N: ").upper() == "Y":
            if player.cash >= cost:
                player.cash -= cost
                player.hp = player.max_hp
                player.blood = player.max_blood
                print("Healed.")
            else:
                print("Not enough cash.")

    # Treat Injuries
    if player.injuries:
        print("\nTREATING INJURIES:")
        # Create a copy to iterate safely while modifying
        for inj in list(player.injuries):
            if "Broken Hand" in inj:
                cost = 25.00
                print(f"- {inj} (Requires Cast: ${cost:.2f}, 6-8 Weeks)")
                if input("Cast? (Y/N): ").upper() == "Y":
                    if player.cash >= cost:
                        player.cash -= cost
                        duration = random.randint(6, 8)
                        player.healing_injuries[inj] = duration
                        player.injuries.remove(inj)
                        print("Hand casted. It will heal in time.")
                    else:
                        print("Not enough cash.")
            else:
                cost = 15.00 
                print(f"- {inj} (Cost: ${cost:.2f})")
                if input("Treat? (Y/N): ").upper() == "Y":
                    if player.cash >= cost:
                        player.cash -= cost
                        player.injuries.remove(inj)
                        print("Treated.")
                    else:
                        print("Not enough cash.")
                    
    input("Press Enter...")

def sleep(player, world):
    world.week += 1
    world.time_of_day = "Morning"
    player.hp = min(player.max_hp, player.hp + 20)
    player.blood = min(player.max_blood, player.blood + 2)
    
    # World Simulation
    update_world_simulation(world)
    
    # Rent Check
    if player.weeks_rent_paid > 0:
        player.weeks_rent_paid -= 1
        print("You rested for a week. Wounds are healing.")
    else:
        print("You slept in the dirt. It was rough.")
        player.hp = min(player.max_hp, player.hp + 5) # Less healing
        
    # Healing Injuries
    if player.healing_injuries:
        for inj in list(player.healing_injuries.keys()):
            player.healing_injuries[inj] -= 1
            if player.healing_injuries[inj] <= 0:
                del player.healing_injuries[inj]
                print(f"Your {inj} has fully healed!")
            else:
                print(f"{inj} is healing... ({player.healing_injuries[inj]} weeks left)")

    input("Press Enter...")

def visit_stables(player, world):
    while True:
        render_hud(player, world)
        print("\n=== LIVERY STABLES ===")
        
        options = {
            "1": "Buy Horse",
            "2": "Sell Current Horse",
            "3": "Work: Haul Hay (1 Week, +$2, -Heat)",
            "4": "Work: Break Horses (1 Week, +$3, -Heat)",
            "B": "Back"
        }
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            print("\nAVAILABLE HORSES:")
            for i, h in enumerate(AVAILABLE_HORSES):
                print(f"{i+1}. {h.name} (Spd: {h.stats.get('spd', 0)}, HP: {h.stats.get('hp', 0)}) - ${h.value:.2f}")
            
            try:
                idx = int(input("Choice: ")) - 1
                if 0 <= idx < len(AVAILABLE_HORSES):
                    horse = AVAILABLE_HORSES[idx]
                    if player.cash >= horse.value:
                        player.cash -= horse.value
                        player.horse = horse
                        print(f"You bought {horse.name}.")
                    else:
                        print("Not enough cash.")
            except:
                pass
                
        elif choice == "2":
            if player.horse:
                val = player.horse.value * 0.5
                player.cash += val
                print(f"Sold {player.horse.name} for ${val:.2f}.")
                player.horse = None
            else:
                print("You have no horse.")
                
        elif choice == "3":
            print("\nYou spend a week hauling heavy bales of hay.")
            player.cash += 2.00
            player.brawl_atk += 1
            player.honor += 1
            world.week += 1
            world.reduce_heat(5) # Good honest work reduces heat
            print("You earned $2.00 and feel stronger. People respect honest work. (+1 Honor)")
            time.sleep(1.5)
            
        elif choice == "4":
            print("\nYou spend a week getting thrown by wild mustangs.")
            player.cash += 3.00
            player.brawl_def += 1
            player.honor += 1
            world.week += 1
            world.reduce_heat(5)
            print("You earned $3.00 and feel tougher. (+1 Honor)")
            time.sleep(1.5)
            
        elif choice == "B":
            break

def visit_store(player, world, robbery=False):
    while True:
        render_hud(player, world)
        print("\n=== GENERAL STORE ===")
        
        if robbery:
            print("You pull your gun on the shopkeeper!")
            if input("Rob the register? (Y/N): ").upper() == "Y":
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
            for i, w in enumerate(AVAILABLE_WEAPONS):
                cost = w.value * markup
                print(f"{i+1}. {w.name} (Acc: {w.stats['acc']}, Dmg: {w.stats['dmg']}) - ${cost:.2f}")
            # (Simplified buying logic for brevity)
            try:
                idx = int(input("Choice: ")) - 1
                if 0 <= idx < len(AVAILABLE_WEAPONS):
                    w = AVAILABLE_WEAPONS[idx]
                    cost = w.value * markup
                    if player.cash >= cost:
                        player.cash -= cost
                        player.gun = w
                        print(f"Bought {w.name}.")
            except: pass

        elif choice == "4":
            print("\nHATS:")
            for i, h in enumerate(AVAILABLE_HATS):
                cost = h.value * markup
                print(f"{i+1}. {h.name} (Def: {h.stats['def']}, Style: {h.stats['style']}) - ${cost:.2f}")
            try:
                idx = int(input("Choice: ")) - 1
                if 0 <= idx < len(AVAILABLE_HATS):
                    h = AVAILABLE_HATS[idx]
                    cost = h.value * markup
                    if player.cash >= cost:
                        player.cash -= cost
                        player.hat = h
                        print(f"Bought {h.name}.")
            except: pass
            
        elif choice == "B":
            break

def visit_sheriff(player, world):
    while True:
        render_hud(player, world)
        print("\n=== SHERIFF'S OFFICE ===")
        
        heat = world.get_local_heat()
        if heat > 50:
            print("Sheriff: 'I've got my eye on you, stranger.'")
        if heat > 80:
            print("Sheriff: 'You're pushing your luck.'")
            
        options = {
            "1": "Check Bounties (Not implemented)",
            "2": f"Pay off Bounty/Fines (Cost: ${heat * 2:.2f})",
            "B": "Back"
        }

        if not player.is_deputy:
            options["3"] = "Apply to be Deputy"
        else:
            options["3"] = "Report for Duty (Patrol)"
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            # Check Bounties
            print("\n=== WANTED POSTERS ===")
            wanted = [n for n in world.active_npcs if n.bounty > 0]
            if not wanted:
                print("No active bounties.")
            else:
                for n in wanted:
                    loc = n.location if n.location else "Unknown"
                    print(f"- {n.name} (${n.bounty:.2f}) - Last seen: {loc}")
                    print(f"  '{n.rumor}'")
            input("Press Enter...")

        elif choice == "2":
            cost = heat * 2
            if cost > 0:
                print(f"Sheriff: 'That'll clear your name around here. ${cost:.2f}.'")
                if input("Pay? (Y/N): ").upper() == "Y":
                    if player.cash >= cost:
                        player.cash -= cost
                        world.reduce_heat(100) # Clear all heat
                        print("Sheriff: 'Alright. Keep your nose clean.'")
                    else:
                        print("Sheriff: 'Come back when you have the money.'")
            else:
                print("Sheriff: 'You're clean, son.'")

        elif choice == "3":
            if not player.is_deputy:
                if heat > 10:
                    print("Sheriff: 'I don't hire troublemakers. Clean up your act.'")
                    time.sleep(1.5)
                elif player.honor < 5:
                    print("Sheriff: 'I need someone the people trust. You ain't it.'")
                    time.sleep(1.5)
                else:
                    print("Sheriff: 'You look handy with a gun and got a good head on your shoulders.'")
                    print("Sheriff: 'I'll badge you. $5.00 a week, keep the peace, don't shoot unless shot at.'")
                    if input("Accept? (Y/N): ").upper() == "Y":
                        player.is_deputy = True
                        print("You are now a Deputy.")
                        time.sleep(1)
            else:
                patrol_town(player, world)
                
        elif choice == "B":
            break

def patrol_town(player, world):
    print("\n=== TOWN PATROL ===")
    print("You spend the week walking the streets, breaking up fights, and keeping watch.")
    world.week += 1
    player.cash += 5.00
    world.reduce_heat(10) # Deputies lower town heat
    
    # Random Event
    roll = random.random()
    if roll < 0.3:
        print("You spot a drunkard harassing a lady.")
        if input("Intervene? (Y/N): ").upper() == "Y":
            start_brawl(player, world, NPC("Drunkard"))
            if player.alive and player.conscious:
                print("Sheriff: 'Good work, Deputy.'")
                player.honor += 5
    elif roll < 0.5:
        print("A gang of outlaws rides into town looking for trouble!")
        print("Sheriff: 'Deputy! With me!'")
        
        # Setup Teams: Player + Sheriff vs Outlaws
        sheriff = NPC("Sheriff")
        sheriff.name = "Sheriff" # Generic ally
        
        player_team = [player, sheriff]
        enemy_team = [NPC("Outlaw") for _ in range(random.randint(2, 3))]
        
        print(f"Enemies: {len(enemy_team)}")
        input("Start Shootout (Press Enter)")
        
        engine = ShootoutEngine(player_team, enemy_team)
        while True:
            engine.render()
            if not engine.run_turn(): break
            time.sleep(1.5)
            
        if player.alive:
            print("Sheriff: 'That's one less problem to worry about.'")
            player.reputation += 10
            player.cash += 20.00 # Bonus
            
    else:
        print("It was a quiet week.")
    
    input("Press Enter...")

def handle_crime(player, world, crime_name):
    print(f"\nYOU ARE CAUGHT {crime_name.upper()}!")
    print("The Sheriff draws his gun.")
    
    if input("Surrender? (Y/N): ").upper() == "Y":
        fine = world.get_local_heat() * 1.5
        print(f"You are thrown in jail for a week and fined ${fine:.2f}.")
        player.cash = max(0, player.cash - fine)
        world.week += 1
        world.reduce_heat(20)
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
            sys.exit()

def plan_heist(player, world):
    print("\n=== PLAN HEIST ===")
    print("Choose a target:")
    
    # Dynamic Targets based on Map
    options = {}
    targets = []
    
    # Find nearby towns
    neighbors = world.map.get(world.town_name, {}) # Camp is "near" the last town visited usually, or we abstract it
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
            elif choice == "B":
                break
                
        else:
            print("The Mayor looks up from his paperwork.")
            if town.mayor_status == "Bribed":
                print("Mayor: 'I'm looking the other way, as agreed.'")
            else:
                print("Mayor: 'What do you want?'")
                
            options = {
                "1": "Bribe ($50) - Ignore Crimes for 1 Week",
                "2": "Intimidate (Req: High Rep/Gang)",
                "3": "Kill Him",
                "B": "Back"
            }
            
            if player.reputation > 80 and not player.is_gang_leader:
                options["4"] = "Run for Mayor (Election)"
            
            choice = get_menu_choice(options)
            
            if choice == "1":
                if player.cash >= 50:
                    player.cash -= 50
                    town.mayor_status = "Bribed"
                    print("Mayor: 'A pleasure doing business.'")
                    town.heat = 0 # Reset heat temporarily
                else:
                    print("Mayor: 'Get out, pauper.'")
                time.sleep(1)
                
            elif choice == "2":
                # Intimidate
                power = player.reputation + (len(player.gang) * 10)
                if power > 60:
                    print("You threaten the Mayor.")
                    print("Mayor: 'Okay! Okay! Just don't hurt me!'")
                    town.mayor_status = "Bribed"
                    town.influence += 10
                else:
                    print("Mayor: 'Guards! Remove this ruffian!'")
                    start_brawl(player, world, NPC("Sheriff"))
                time.sleep(1)
                
            elif choice == "3":
                print("You draw your weapon!")
                # Mayor has guards?
                guards = [NPC("Sheriff")]
                engine = ShootoutEngine([player] + player.gang, guards + [NPC("Mayor")])
                while True:
                    engine.render()
                    if not engine.run_turn(): break
                    time.sleep(1)
                
                if player.alive:
                    print("The Mayor is dead.")
                    town.mayor_status = "Dead"
                    player.honor -= 50
                    world.add_heat(100)
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
                
            elif choice == "B":
                break

def visit_bank(player, world):
    while True:
        render_hud(player, world)
        print("\n=== FIRST NATIONAL BANK ===")
        
        # Check for receipts
        receipts = [i for i in player.inventory if i.item_type == ItemType.RECEIPT]
        
        options = {
            "1": "Deposit Cash (Safe Storage)",
            "2": "Withdraw Cash",
            "B": "Back"
        }
        
        if receipts:
            options["3"] = f"Cash Bank Drafts ({len(receipts)} available)"
            
        choice = get_menu_choice(options)
        
        if choice == "1":
            # Placeholder for deposit logic
            print("Teller: 'We don't have accounts set up for drifters yet.'")
            time.sleep(1)
            
        elif choice == "2":
            print("Teller: 'You have no account here.'")
            time.sleep(1)
            
        elif choice == "3":
            print("\n=== CASHING DRAFTS ===")
            for i, r in enumerate(receipts):
                origin = r.stats.get("origin", "Unknown")
                print(f"{i+1}. {r.name} from {origin}")
                
            try:
                idx = int(input("Select draft to cash (0 to cancel): ")) - 1
                if 0 <= idx < len(receipts):
                    draft = receipts[idx]
                    origin = draft.stats.get("origin")
                    
                    print(f"Teller examines the draft for ${draft.value:.2f}...")
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
                            print("Teller: 'Everything seems in order.'")
                            print(f"You receive ${draft.value:.2f}.")
                            player.cash += draft.value
                            player.inventory.remove(draft)
                        else:
                            print("Teller: 'Wait a minute... this isn't you!'")
                            print("ALARM RAISED!")
                            world.add_heat(30)
                            player.bounty += 20
                            player.honor -= 5
                            # Fight or Flee?
                            if input("Flee? (Y/N): ").upper() == "N":
                                start_duel(player, world, NPC("Sheriff"))
                            else:
                                print("You run out of the bank!")
                                return
                    else:
                        print(f"Teller: 'This is drawn on the {origin} branch. You must go there to cash it.'")
                        time.sleep(1.5)
            except: pass
            
        elif choice == "B":
            break

if __name__ == "__main__":
    main()
