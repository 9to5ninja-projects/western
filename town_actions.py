import random
import time
from characters import NPC
from combat_runner import start_brawl, start_duel, process_gang_casualties, handle_blackout
from shootout_engine import ShootoutEngine
from ui import get_menu_choice, render_hud
from game_state import ItemType, AVAILABLE_HORSES, AVAILABLE_WEAPONS, AVAILABLE_HATS, LORE_ITEMS
from visualizer import renderer
from game_utils import wait_for_user, options_to_buttons
from story_events import check_story_events
from world_sim import update_world_simulation
from save_manager import save_game

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
        
    elif player.alive and enemies_alive:
        print("\nThe attack failed! You retreat.")
        world.add_heat(50)
    else:
        print("\nYou died in the street war.")

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
                
            wait_for_user(["Defend yourself!"], player=player)
            
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
            "6": "View Patrons",
            "B": "Back to Town"
        }
        
        if not player.is_gang_leader:
             options["5"] = "Recruit Gunhand (Req: 20 Rep, $10)"
        else:
             options["5"] = "Recruit More Muscle ($10)"
        
        # Hidden Brawler Sidequest
        if player.brawler_rep > 50:
            options["7"] = "Challenge The Champ (LEGENDARY BRAWL)"

        stats_display = [
            f"Cash: ${player.cash:.2f}", 
            f"HP: {player.hp}/{player.max_hp}",
            f"Brawl: {player.brawl_wins}W-{player.brawl_losses}L ({player.brawler_rep} Rep)",
            f"Duel: {player.duel_wins}W-{player.duel_losses}L"
        ]
        
        renderer.render(
            stats_text=stats_display,
            log_text=["The air is thick with smoke..."],
            buttons=options_to_buttons(options)
        )
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            if player.cash >= 0.50:
                player.cash -= 0.50
                player.hp = min(player.max_hp, player.hp + 5)
                
                player.drunk_counter += 1
                msgs = ["You down the whiskey.", "It burns. (+5 HP)"]
                
                if player.drunk_counter >= 9:
                    msgs.append("The room spins violently...")
                    wait_for_user(msgs, player=player)
                    handle_blackout(player, world)
                    return # Exit cantina loop
                elif player.drunk_counter >= 6:
                    msgs.append("You can barely see straight. (ACC = 0)")
                elif player.drunk_counter >= 3:
                    msgs.append("You feel woozy. (ACC Halved)")
                
                wait_for_user(msgs, player=player)
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
                                wait_for_user(dialogue, player=player)
                    except: pass
            else:
                wait_for_user(log_lines, player=player)
            
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

        elif choice == "6":
            # View Patrons
            patrons = [n for n in world.active_npcs if n.location == world.town_name]
            # Add Gang Members
            for g in world.rival_gangs:
                if g.active and g.hideout == world.town_name:
                    patrons.append(g.leader)
                    patrons.extend(g.members)
            
            log_lines = ["=== PATRONS ==="]
            if not patrons:
                log_lines.append("The bar is mostly empty.")
            else:
                for p in patrons:
                    status = "Drinking"
                    if p.bounty > 0: status = f"Wanted (${p.bounty})"
                    log_lines.append(f"- {p.name} ({p.archetype}): {status}")
            
            buttons = [
                {"label": "Buy Round ($5.00)", "key": "1"},
                {"label": "Back", "key": "B"}
            ]
            
            renderer.render(log_text=log_lines, buttons=buttons, player=player)
            
            if renderer.get_input() == "1":
                if player.cash >= 5.00:
                    player.cash -= 5.00
                    player.reputation += 5
                    player.charm += 1
                    wait_for_user(["You buy a round for the house!", "Everyone cheers! (+5 Rep, +1 Charm)"], player=player)
                else:
                    wait_for_user(["Bartender: 'Show me the money first.'"], player=player)

        elif choice == "7" and player.brawler_rep > 50:
            # The Champ
            champ = NPC("Brute")
            champ.name = "Iron Jaw McGee"
            champ.hp = 150 # Boss HP
            champ.max_hp = 150
            champ.brawl_atk = 8
            champ.brawl_def = 8
            
            renderer.render(
                log_text=[
                    "The crowd parts...", 
                    "Iron Jaw McGee steps forward.", 
                    "'You think you're tough, kid?'",
                    "Fight? (Y/N)"
                ],
                player=player,
                buttons=[{"label": "Fight", "key": "Y"}, {"label": "Back Down", "key": "N"}]
            )
            
            if renderer.get_input() == "Y":
                start_brawl(player, world, champ)
                # Check if player won (Champ KO'd or Dead)
                if player.alive and (not champ.alive or champ.hp <= 0): 
                    if champ.hp <= 0 or not champ.alive:
                        player.reputation += 50
                        player.cash += 100.00
                        player.brawler_rep += 20
                        wait_for_user(["You knocked out the Champ!", "You are the new Legend of the Ring!", "Earned $100.00 and massive Rep."], player=player)
            else:
                wait_for_user(["The crowd boos as you walk away."], player=player)
                player.reputation -= 5

        elif choice == "B":
            break
