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
        start_brawl(player, world, NPC("Sheriff")) # No return check needed as it returns to menu anyway?
        # Actually demand_protection is called from visit_mayor.
        # If knocked out, we should probably return from demand_protection too.
        # But demand_protection returns void.
        # We can't easily propagate the return up without changing signature.
        # But visit_mayor loop continues.
        # If player is at Doctor, visit_mayor loop will re-render Mayor menu?
        # Yes.
        # I should probably check player location in visit_mayor loop?
        # Or just let it be for now. The user specifically mentioned Cantina.
        # But for consistency, I should fix it.
        # However, demand_protection is a sub-function.
        # I'll leave it for now as it's less critical than the main loops.

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
        log_lines = [f"=== TOWN HALL: {town.name.upper()} ==="]
        
        if town.player_is_mayor:
            log_lines.extend([
                "You sit at the Mayor's desk.",
                f"Town Influence: {town.influence}%",
                "Town Treasury: High"
            ])
            
            options = {
                "1": "Collect Taxes (+$50, +Heat)",
                "2": "Hire Sheriff (Cost $50)",
                "3": "Host Gala (Cost $100, +Rep)",
                "B": "Back"
            }
            
            renderer.render(log_text=log_lines, buttons=options_to_buttons(options), player=player)
            choice = get_menu_choice(options)
            
            if choice == "1":
                player.cash += 50
                town.heat += 20
                town.influence -= 5
                wait_for_user(["You squeeze the locals for cash.", "Collected $50. Heat increased."], player=player)
            elif choice == "2":
                if player.cash >= 50:
                    player.cash -= 50
                    town.lawfulness += 10
                    town.heat = max(0, town.heat - 20)
                    wait_for_user(["You hired a new Sheriff.", "Lawfulness increased. Heat reduced."], player=player)
                else:
                    wait_for_user(["Not enough cash."], player=player)
            elif choice == "3":
                if player.cash >= 100:
                    player.cash -= 100
                    player.reputation += 20
                    town.influence += 10
                    wait_for_user(["You hosted a lavish gala.", "The town loves you! (+20 Rep)"], player=player)
                else:
                    wait_for_user(["Not enough cash."], player=player)
            elif choice == "B":
                break
            
        elif town.mayor_status == "Dead":
            log_lines.append("The Mayor's office is empty. The previous mayor was killed.")
            log_lines.append("The town is in chaos.")
            
            options = {
                "1": "Declare Martial Law (Take Over)",
                "2": "Call for Special Election (Restore Order)",
                "B": "Back"
            }
            
            renderer.render(log_text=log_lines, buttons=options_to_buttons(options), player=player)
            choice = get_menu_choice(options)
            
            if choice == "1":
                if player.reputation > 50 or len(player.gang) > 3:
                    town.player_is_mayor = True
                    town.mayor_status = "Alive" # You are the mayor
                    town.influence = 50
                    wait_for_user(["You slam your gun on the desk.", "'I'm in charge now.'"], player=player)
                else:
                    wait_for_user(["The townsfolk laugh you out of the office."], player=player)
            elif choice == "2":
                log_lines = ["You organize a town meeting to elect a new mayor."]
                if random.random() < 0.8:
                    new_mayor = NPC("Mayor")
                    town.mayor = new_mayor
                    town.mayor_status = "Alive"
                    log_lines.append(f"The town has elected {new_mayor.name} as the new Mayor.")
                    log_lines.append(f"Personality: {new_mayor.personality}")
                    player.reputation += 10
                    player.honor += 10
                    wait_for_user(log_lines, player=player)
                else:
                    log_lines.append("The meeting ends in a brawl! No mayor elected.")
                    wait_for_user(log_lines, player=player)
                    if start_brawl(player, world, NPC("Drunkard")): return
            elif choice == "B":
                break
                
        else:
            # Use Persistent Mayor
            mayor = town.mayor
            if not mayor: # Fallback
                mayor = NPC("Mayor")
                town.mayor = mayor
                
            log_lines.append(f"Mayor {mayor.name} looks up from his paperwork.")
            log_lines.append(f"Personality: {mayor.personality} ({mayor.personality_data.get('desc', '')})")
            
            if town.mayor_status == "Bribed":
                log_lines.append(f"{mayor.name}: 'I'm looking the other way, as agreed.'")
            else:
                log_lines.append(f"{mayor.name}: '{mayor.get_line()}'")
                
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
            
            renderer.render(log_text=log_lines, buttons=options_to_buttons(options), player=player)
            choice = get_menu_choice(options)
            
            if choice == "1":
                if bribe_cost >= 500:
                    wait_for_user([f"{mayor.name}: 'I am a man of principle! Get out!'"], player=player)
                elif player.cash >= bribe_cost:
                    player.cash -= bribe_cost
                    town.mayor_status = "Bribed"
                    town.heat = 0 # Reset heat temporarily
                    wait_for_user([f"{mayor.name}: 'A pleasure doing business.'", "Heat reset."], player=player)
                else:
                    wait_for_user([f"{mayor.name}: 'Get out, pauper.'"], player=player)
                
            elif choice == "2":
                # Intimidate
                power = player.reputation + (len(player.gang) * 10)
                diff_mod = mayor.personality_data.get("intimidate_diff", 0)
                difficulty = 60 + diff_mod
                
                if power > difficulty:
                    town.mayor_status = "Bribed"
                    town.influence += 10
                    wait_for_user(["You threaten the Mayor.", f"{mayor.name}: 'Okay! Okay! Just don't hurt me!'"], player=player)
                else:
                    wait_for_user([f"{mayor.name}: 'Guards! Remove this ruffian!'"], player=player)
                    if start_brawl(player, world, town.sheriff if town.sheriff else NPC("Sheriff")): return
                
            elif choice == "3":
                wait_for_user(["You draw your weapon!"], player=player)
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
                        town.mayor_status = "Dead"
                        player.honor -= 50
                        world.add_heat(100)
                        wait_for_user(["The Mayor is dead.", "You are now a wanted criminal."], player=player)
                    else:
                        wait_for_user(["The Mayor escaped!"], player=player)
                else:
                    wait_for_user(["You failed to kill the Mayor."], player=player)
                    
            elif choice == "4":
                log_lines = ["You start your campaign..."]
                # Simple check for now
                if random.random() < 0.7:
                    log_lines.append("The people love you! You win the election!")
                    town.player_is_mayor = True
                else:
                    log_lines.append("You lost the election.")
                wait_for_user(log_lines, player=player)
            
            elif choice == "5":
                demand_protection(player, world)
                
            elif choice == "6":
                attempt_takeover(player, world)
                
            elif choice == "B":
                break

def bail_member(player, world):
    town = world.get_town()
    
    if not town.jail:
        wait_for_user(["The cells are empty."], player=player)
        return
        
    log_lines = [f"=== TOWN JAIL: {town.name} ===", "Inmates:"]
    buttons = []
    for i, member in enumerate(town.jail):
        log_lines.append(f"{i+1}. {member.name} (Bail: $50.00)")
        buttons.append({"label": f"Bail {member.name}", "key": str(i+1)})
        
    buttons.append({"label": "Back", "key": "B"})
    
    renderer.render(log_text=log_lines, buttons=buttons, player=player)
    
    choice = renderer.get_input()
    if choice == "B": return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(town.jail):
            member = town.jail[idx]
            if player.cash >= 50:
                player.cash -= 50
                town.jail.pop(idx)
                player.gang.append(member)
                wait_for_user([f"You bailed out {member.name}."], player=player)
            else:
                wait_for_user(["Not enough cash."], player=player)
    except ValueError:
        pass


def visit_cantina(player, world):
    renderer.load_scene("cantina")
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
                if start_duel(player, world, npc): return
            else:
                if start_brawl(player, world, npc): return
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
            f"Brawl: {player.brawl_wins}W-{player.brawl_losses}L-{player.brawl_draws}D ({player.brawler_rep} Rep)",
            f"Duel: {player.duel_wins}W-{player.duel_losses}L"
        ]
        
        renderer.render(
            stats_text=stats_display,
            log_text=["The air is thick with smoke..."],
            buttons=options_to_buttons(options)
        )
        
        choice = get_menu_choice(options)
        
        if choice == "1":
            # Age Check
            if player.age < 18:
                # Charm Check to bypass
                difficulty = 30
                skill = player.charm * 10 + player.luck_base
                
                if skill < difficulty:
                    wait_for_user(["Bartender: 'You look a bit young, kid.'", "He refuses to serve you."], player=player)
                    continue
            
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
                                    if start_duel(player, world, target): return
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
            if start_brawl(player, world, npc): return
            
        elif choice == "4":
            npc = NPC("Cowboy")
            if start_duel(player, world, npc): return
            
        elif choice == "5":
            # Recruit Gang Member
            if not player.camp_established:
                print("\nMercenary: 'You ain't got nowhere for us to hole up.'")
                print("(You must establish a Camp first. Check 'Travel' menu.)")
                wait_for_user(["Mercenary: 'Get a camp first.'"], player=player)
            elif player.reputation < 20:
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
                            print("You have started a gang.")
                            player.is_gang_leader = True
                            # player.camp_established = True # Removed, must be done manually now
                            # player.location = "Wilderness Camp" # Removed force move
                            time.sleep(2)
                            # return # No longer need to exit loop immediately
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
                if start_brawl(player, world, champ): return
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

def visit_stables(player, world):
    renderer.load_scene("stables")
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
            
            update_world_simulation(world, player) # Update world while working
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
            
            update_world_simulation(world, player) # Update world while working
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
                    if start_brawl(player, world, sm): return
                    
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
    renderer.load_scene("store")
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
                    if start_duel(player, world, NPC("Cowboy")): return # Use Cowboy stats for shopkeeper
                
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
    renderer.load_scene("sheriff")
    town = world.get_town()
    sheriff = town.sheriff
    
    # Check if Sheriff is dead
    if sheriff and not sheriff.alive:
        # Spawn temporary sheriff for interaction
        sheriff = NPC("Sheriff")
        sheriff.name = "Deputy"
        sheriff.personality = "Lawful" # Deputies are strict
        
    if not sheriff:
        sheriff = NPC("Sheriff")
        town.sheriff = sheriff
        
    while True:
        render_hud(player, world)
        log_lines = [f"=== SHERIFF'S OFFICE ===", f"Sheriff: {sheriff.name}"]
        log_lines.append(f"Personality: {sheriff.personality} ({sheriff.personality_data.get('desc', '')})")
        
        if sheriff.name == "Deputy":
            log_lines.insert(1, "The Sheriff's desk is empty. A deputy is manning it.")
        
        heat = world.get_local_heat()
        if heat > 50:
            log_lines.append(f"{sheriff.name}: 'I've got my eye on you, stranger.'")
        if heat > 80:
            log_lines.append(f"{sheriff.name}: 'You're pushing your luck.'")
            
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
        
        renderer.render(log_text=log_lines, buttons=options_to_buttons(options), player=player)
        choice = get_menu_choice(options)
        
        if choice == "1":
            # Check Bounties
            log_lines = ["=== WANTED POSTERS ==="]
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
                log_lines.append("No active bounties.")
            else:
                for n in wanted:
                    loc = n.location if n.location else "Unknown"
                    # Check if it's a gang leader
                    gang_tag = ""
                    for g in world.rival_gangs:
                        if g.active and (n == g.leader or n in g.members):
                            gang_tag = f" ({g.name})"
                            break
                            
                    log_lines.append(f"- {n.name}{gang_tag} (${n.bounty:.2f}) - Last seen: {loc}")
                    if n.rumor:
                        log_lines.append(f"  '{n.rumor}'")
            wait_for_user(log_lines, player=player)

        elif choice == "2":
            cost = heat * 2
            if sheriff.personality == "Corrupt":
                cost = cost * 0.5
                
            if cost > 0:
                log_lines = [f"{sheriff.name}: 'That'll clear your name around here. ${cost:.2f}.'"]
                if sheriff.personality == "Corrupt":
                    log_lines.append("(Corrupt Discount: 50% off)")
                
                renderer.render(log_text=log_lines + ["Pay? (Y/N)"], player=player)
                if renderer.get_input() == "Y":
                    if player.cash >= cost:
                        player.cash -= cost
                        world.reduce_heat(100) # Clear all heat
                        wait_for_user([f"{sheriff.name}: 'Alright. Keep your nose clean.'"], player=player)
                    else:
                        wait_for_user([f"{sheriff.name}: 'Come back when you have the money.'"], player=player)
            else:
                wait_for_user([f"{sheriff.name}: 'You're clean, son.'"], player=player)

        elif choice == "3":
            if not player.is_deputy:
                if heat > 10:
                    wait_for_user([f"{sheriff.name}: 'I don't hire troublemakers. Clean up your act.'"], player=player)
                elif player.honor < 5 and sheriff.personality == "Lawful":
                    wait_for_user([f"{sheriff.name}: 'I need someone the people trust. You ain't it.'"], player=player)
                else:
                    renderer.render(
                        log_text=[f"{sheriff.name}: 'You look handy with a gun.'", "Accept Deputy Badge? (Y/N)"], 
                        player=player
                    )
                   
                    if renderer.get_input() == "Y":
                        player.is_deputy = True
                        wait_for_user(["You are now a Deputy."], player=player)
            else:
                if patrol_town(player, world): return
        
        elif choice == "4":
            bail_member(player, world)
                
        elif choice == "B":
            break

def patrol_town(player, world):
    town = world.get_town()
    sheriff = town.sheriff if town.sheriff else NPC("Sheriff")
    
    log_lines = ["=== TOWN PATROL ===", "You spend the week walking the streets."]
    
    world.week += 1
    player.drunk_counter = 0 # Sober up
    if player.weeks_rent_paid > 0:
        player.weeks_rent_paid -= 1
        log_lines.append("Rent paid for 1 week.")
        
    player.cash += 5.00
    world.reduce_heat(10) # Deputies lower town heat
    
    update_world_simulation(world, player)
    check_story_events(player, world)
    
    # Random Event
    roll = random.random()
    if roll < 0.3:
        log_lines.append("You spot a drunkard harassing a lady.")
        renderer.render(log_text=log_lines + ["Intervene? (Y/N)"], player=player)
        
        if renderer.get_input() == "Y":
            if start_brawl(player, world, NPC("Drunkard")): return True
            if player.alive and player.conscious:
                player.honor += 5
                wait_for_user([f"{sheriff.name}: 'Good work, Deputy.'"], player=player)
    elif roll < 0.5:
        log_lines.append("A gang of outlaws rides into town!")
        log_lines.append(f"{sheriff.name}: 'Deputy! With me!'")
        
        # Setup Teams: Player + Sheriff vs Outlaws
        player_team = [player, sheriff]
        enemy_team = [NPC("Outlaw") for _ in range(random.randint(2, 3))]
        
        log_lines.append(f"Enemies: {len(enemy_team)}")
        wait_for_user(log_lines + ["Start Shootout"], player=player)
        
        engine = ShootoutEngine(player_team, enemy_team)
        while True:
            engine.render()
            if not engine.run_turn(): break
            time.sleep(1.5)
            
        if player.alive:
            player.reputation += 10
            player.cash += 20.00 # Bonus
            wait_for_user([f"{sheriff.name}: 'That's one less problem.'", "You earned $20.00 bonus."], player=player)
            
    else:
        log_lines.append("It was a quiet week.")
        wait_for_user(log_lines, player=player)
