import random
import time
from game_state import ItemType
from characters import NPC
from duel_engine_v2 import DuelEngineV2, Combatant, Action, Orientation, ai_honorable
from visualizer import renderer
from game_utils import wait_for_user
from world_sim import update_world_simulation

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

def loot_screen(player, world, npc):
    while True:
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
        elif choice == "2" and npc.weapon:
            player.add_item(npc.weapon)
            print(f"You took the {npc.weapon.name}.")
            npc.weapon = None
            player.honor -= 10
            world.add_heat(15)
        elif choice == "3" and npc.hat:
            player.add_item(npc.hat)
            print(f"You took the {npc.hat.name}.")
            npc.hat = None
            player.honor -= 10
            world.add_heat(10)
        elif choice == "4" and receipts:
            for r in receipts:
                player.add_item(r)
            print(f"You took {len(receipts)} bank drafts.")
            npc.inventory = [i for i in npc.inventory if i.item_type != ItemType.RECEIPT]
            player.honor -= 5
            world.add_heat(10)
        elif choice == "5" and (npc.archetype == "Sheriff" or npc.name == "Sheriff"):
            print("You took the Sheriff's Badge.")
            player.honor -= 20
            world.add_heat(50)
        elif choice == "B":
            print("You leave the body.")
            break

def handle_crime(player, world, crime_name):
    print(f"\nYOU ARE CAUGHT {crime_name.upper()}!")
    print("The Sheriff draws his gun.")
    
    renderer.render(
        log_text=[f"CAUGHT {crime_name.upper()}!", "Sheriff draws his gun.", "Surrender? (Y/N)"], 
        player=player,
        buttons=[{"label": "Surrender", "key": "Y"}, {"label": "Resist", "key": "N"}]
    )
    
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
        
        # Simulate world during jail time
        for _ in range(min(jail_time, 5)): # Cap at 5 updates to avoid lag/spam
            update_world_simulation(world, player)
            
        wait_for_user(log_msg, player=player)
    else:
        start_duel(player, world, is_sheriff=True)

def start_brawl(player, world, npc=None):
    if not npc: npc = NPC("Drunkard")
    
    print(f"\nYou get into a scrap with {npc.name} ({npc.archetype})!")
    wait_for_user("FIGHT ON!")
    
    # Create Combatants
    p1 = Combatant(player.name, -1, player, source_obj=player)
    p2 = Combatant(npc.name, 1, source_obj=npc)
    # Sync NPC stats to Combatant
    p2.brawl_atk = npc.brawl_atk
    p2.brawl_def = npc.brawl_def
    p2.hp = npc.hp
    p2.max_hp = npc.max_hp
    
    engine = DuelEngineV2(p1, p2)
    
    # Simple Brawl Loop
    while p1.conscious and p2.conscious and p1.alive and p2.alive:
        renderer.render_duel_state(engine, p1, p2)
        
        # Check if opponent surrendered in PREVIOUS turn
        if p2.is_surrendering:
            surrender_buttons = [
                {"label": "Accept Surrender", "key": "1"},
                {"label": "Finish Him!", "key": "2"}
            ]
            renderer.render(
                log_text=[f"{p2.name} is asking for mercy!", "Choose fate..."],
                buttons=surrender_buttons
            )
            
            sub = renderer.get_input()
            if sub == "1":
                wait_for_user(["You step back.", "Fight over."], player=player)
                p2.conscious = False # End loop gracefully
                break
            elif sub == "2":
                wait_for_user(["You ignore their plea."], player=player)
                p2.is_surrendering = False # They fight on!
                p2.surrender_refused = True
                player.honor -= 5

        brawl_buttons = [
            {"label": "JAB (Fast)", "key": "1"},
            {"label": "HOOK (Strong)", "key": "2"},
            {"label": "BLOCK", "key": "3"}
        ]
        if not p1.surrender_refused:
            brawl_buttons.append({"label": "SURRENDER", "key": "4"})
        
        renderer.render(
            stats_text=[f"{p1.name}: {p1.hp}/{p1.max_hp}", f"{p2.name}: {p2.hp}/{p2.max_hp}"],
            log_text=engine.log[-5:] if engine.log else ["Brawl started!"],
            buttons=brawl_buttons
        )
        
        act = renderer.get_input()
        
        if act == "1": p1_act = Action.JAB
        elif act == "2": p1_act = Action.HOOK
        elif act == "3": p1_act = Action.BLOCK
        elif act == "4": p1_act = Action.SURRENDER
        else: p1_act = Action.WAIT
        
        # AI Action
        # Simple AI: If HP < 20%, 50% chance to surrender
        p2_act = Action.WAIT
        if p2.hp < p2.max_hp * 0.2 and random.random() < 0.5 and not p2.surrender_refused:
            p2_act = Action.SURRENDER
        else:
            # RPS Logic
            roll = random.random()
            if roll < 0.33: p2_act = Action.JAB
            elif roll < 0.66: p2_act = Action.HOOK
            else: p2_act = Action.BLOCK
        
        engine.run_turn(p1_act, p2_act)
        
        # Check Player Surrender
        if p1.is_surrendering and p2_act != Action.SURRENDER:
            if not p1.conscious:
                break # Player was KO'd while trying to surrender

            # AI accepts?
            if random.random() < 0.8:
                print(f"\n{p2.name} accepts your surrender.")
                wait_for_user([f"{p2.name} accepts your surrender."], player=player)
                
                # Consequences
                loss = random.randint(5, 10)
                player.cash = max(0, player.cash - loss)
                player.reputation = max(0, player.reputation - 5)
                print(f"They took ${loss} from you.")
                
                p1.sync_state()
                return True
            else:
                wait_for_user([f"{p2.name} laughs and keeps hitting you!"], player=player)
                p1.is_surrendering = False
                p1.surrender_refused = True
        
    renderer.render_duel_state(engine, p1, p2)
    p1.sync_state() # Save HP loss back to player
    renderer.clear_scene_text()
    
    # Capture final combat log
    final_log = engine.log[-3:] if engine.log else []
    
    if not p1.conscious and not p2.conscious:
        print("\nDOUBLE KNOCKOUT!")
        log_lines = final_log + ["", "DOUBLE KNOCKOUT!"]
        player.brawl_draws += 1
        wait_for_user(log_lines, player=player)
        
        # Wake up logic (similar to loss but maybe less penalty?)
        loss = random.randint(1, 5)
        player.cash = max(0, player.cash - loss)
        player.hp = min(player.max_hp, player.hp + 5)
        world.week += 1
        renderer.render(log_text=[f"You both wake up in the dirt.", f"Lost ${loss}. Week passed."], player=player)
        wait_for_user()
        return True

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
        player.brawl_wins += 1
        player.brawler_rep += 10
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
        player.brawl_losses += 1
        player.brawler_rep = max(0, player.brawler_rep - 5)
        
        if npc:
            npc.add_memory("Knocked out player in a brawl", 10)
            if npc not in world.active_npcs:
                world.active_npcs.append(npc)
        
        log_lines = final_log + ["", "You were knocked out..."]
        wait_for_user(log_lines, player=player)
        
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
        return True # End brawl function
        
    wait_for_user()

def start_duel(player, world, npc=None, is_sheriff=False):
    if not npc: 
        npc = NPC("Sheriff" if is_sheriff else "Outlaw")
        
    wait_for_user([f"You challenge {npc.name} ({npc.archetype}) to a duel!", "WALK OUT"], player=player)
    
    p1 = Combatant(player.name, -1, player, source_obj=player)
    p2 = Combatant(npc.name, 1, source_obj=npc)
    p2.acc = npc.acc
    p2.spd = npc.spd
    p2.hp = npc.hp
    p2.max_hp = npc.max_hp
    
    engine = DuelEngineV2(p1, p2)
    
    # Duel Loop
    while p1.alive and p2.alive:
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
                p2.is_surrendering = False # They fight on!
                p2.surrender_refused = True
        
        # --- DYNAMIC BUTTON LOGIC ---
        duel_buttons = []
        
        # 1. Movement / Turning (Keys 1 & 2)
        # Determine Visual Facing
        is_facing_right = False
        if p1.direction_multiplier == -1: # Left Side
            if p1.orientation == Orientation.FACING_OPPONENT: is_facing_right = True
        else: # Right Side
            if p1.orientation == Orientation.FACING_AWAY: is_facing_right = True

        action_1 = Action.WAIT
        action_2 = Action.WAIT
        
        if is_facing_right:
            # Facing Right (>)
            # 1 (Left) -> Turn Left
            action_1 = Action.TURN
            duel_buttons.append({"label": "TURN LEFT", "key": "1"})
            
            # 2 (Right) -> Step Right
            action_2 = Action.STEP_RIGHT
            duel_buttons.append({"label": "STEP RIGHT", "key": "2"})
        else:
            # Facing Left (<)
            # 1 (Left) -> Step Left
            action_1 = Action.STEP_LEFT
            duel_buttons.append({"label": "STEP LEFT", "key": "1"})
            
            # 2 (Right) -> Turn Right
            action_2 = Action.TURN
            duel_buttons.append({"label": "TURN RIGHT", "key": "2"})

        # 2. Weapon Actions (Key 3/7)
        if p1.weapon_state == "holstered" or str(p1.weapon_state) == "WeaponState.HOLSTERED":
            duel_buttons.append({"label": "DRAW", "key": "3"})
        elif p1.ammo < 6:
            duel_buttons.append({"label": "RELOAD", "key": "7"})
        
        # 3. Shooting Actions (Keys 4, 5, 6) - Only if Drawn
        if p1.weapon_state == "drawn" or str(p1.weapon_state) == "WeaponState.DRAWN":
            duel_buttons.append({"label": "SHOOT BODY", "key": "4"})
            duel_buttons.append({"label": "SHOOT HEAD", "key": "5"})
            duel_buttons.append({"label": "SHOOT LEGS", "key": "6"})
            
        # 4. Stance (Key 8)
        if p1.is_ducking:
            duel_buttons.append({"label": "STAND", "key": "8"})
        else:
            duel_buttons.append({"label": "DUCK", "key": "8"})
            
        # 5. Evasion (Key J)
        duel_buttons.append({"label": "JUMP", "key": "J"})
        
        # 6. Contextual Melee / Dirty
        dist = engine.get_distance()
        if dist <= 2:
            duel_buttons.append({"label": "PUNCH", "key": "P"})
        elif dist <= 3 and p1.orientation == Orientation.FACING_OPPONENT:
            duel_buttons.append({"label": "KICK SAND", "key": "K"})
            
        # 7. Surrender (Key 9)
        if not p1.surrender_refused:
            duel_buttons.append({"label": "SURRENDER", "key": "9"})
        
        # Contextual Fire Actions (Duck/Stand Fire) - Optional if space permits
        # We have used: 1, 2, 3/7, 4, 5, 6, 8, J, P/K, 9 = 10 buttons max.
        # If we have space (e.g. not shooting), we can add more?
        # Actually, Duck Fire / Stand Fire are combos. Let's keep them as hidden shortcuts or replace standard shoot?
        # User said "use them efficiently".
        # Let's stick to the core set above.
        
        log_lines = engine.log[-5:] if engine.log else ["Duel started."]
        
        # Detailed Stats
        stats_text = []
        
        # Player 1 (User)
        stats_text.append(f"--- {p1.name} ---")
        stats_text.append(f"HP: {p1.hp}/{p1.max_hp}")
        stats_text.append(f"Blood: {p1.blood}")
        
        # Visual Ammo
        ammo_p1 = "|" * p1.ammo + "." * (6 - p1.ammo)
        stats_text.append(f"Ammo: [{ammo_p1}] ({p1.reserve_ammo})")
        
        stats_text.append(f"Pos: {p1.position}")
        
        if player.hat:
            stats_text.append(f"Hat: {player.hat.name}")
        if player.horse:
            stats_text.append(f"Horse: {player.horse.name}")
            
        stats_text.append("") # Spacer
        
        # Player 2 (Enemy)
        stats_text.append(f"--- {p2.name} ---")
        stats_text.append(f"HP: {p2.hp}/{p2.max_hp}")
        stats_text.append(f"Blood: {p2.blood}")
        
        ammo_p2 = "|" * p2.ammo + "." * (6 - p2.ammo)
        stats_text.append(f"Ammo: [{ammo_p2}]")
        
        stats_text.append(f"Pos: {p2.position}")
        
        if npc.hat:
            stats_text.append(f"Hat: {npc.hat.name}")
        if hasattr(npc, 'horse') and npc.horse:
            stats_text.append(f"Horse: {npc.horse.name}")
        
        renderer.render(
            stats_text=stats_text,
            log_text=log_lines,
            buttons=duel_buttons
        )
        
        choice = renderer.get_input()
        
        # Dynamic Mapping
        p1_act = Action.WAIT
        
        if choice == "1": p1_act = action_1
        elif choice == "2": p1_act = action_2
        elif choice == "3": p1_act = Action.DRAW
        elif choice == "4": p1_act = Action.SHOOT_CENTER
        elif choice == "5": p1_act = Action.SHOOT_HIGH
        elif choice == "6": p1_act = Action.SHOOT_LOW
        elif choice == "7": p1_act = Action.RELOAD
        elif choice == "8": 
            p1_act = Action.STAND if p1.is_ducking else Action.DUCK
        elif choice == "9": p1_act = Action.SURRENDER
        elif choice == "J": p1_act = Action.JUMP
        elif choice == "P": p1_act = Action.PUNCH
        elif choice == "K": p1_act = Action.KICK_SAND
        elif choice == "D": p1_act = Action.DUCK_FIRE
        elif choice == "R": p1_act = Action.STAND_FIRE
        
        # AI (Cheater or Honorable?)
        p2_act = ai_honorable(p2, p1, engine)
        
        was_surrendering = p1.is_surrendering
        engine.run_turn(p1_act, p2_act)
        
        # Check if Player Surrendered and AI Accepted
        if p1.is_surrendering and p2_act == Action.WAIT:
            if not p1.conscious:
                break

            print(f"\n{p2.name} accepts your surrender.")
            wait_for_user([f"{p2.name} accepts your surrender."], player=player)
            
            # Memory: Player surrendered
            npc.add_memory("Player surrendered to me", 20)
            if npc not in world.active_npcs:
                world.active_npcs.append(npc)
                
            # Consequences?
            loss = random.randint(5, 15)
            player.cash = max(0, player.cash - loss)
            print(f"They took ${loss} from you.")
            
            p1.sync_state()
            return
            
        # Check if AI Refused (Attacked while player was surrendering)
        if was_surrendering and p2_act != Action.WAIT:
             p1.is_surrendering = False
             p1.surrender_refused = True
             wait_for_user([f"{p2.name} refuses your surrender!"], player=player)

        if not p1.conscious:
            break
        
    p1.sync_state()
    renderer.render_duel_state(engine, p1, p2)
    renderer.clear_scene_text()
    
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
            else:
                print(f"{npc.name}: 'I'd rather die!'")
        else:
            print("You let them run.")
            
    elif p1.alive and not p2.alive:
        print("\nVICTORY!")
        
        log_lines = final_log + ["", "VICTORY!"]
        
        # Nemesis Check: Did they survive?
        survived = False
        if npc and not (is_sheriff or npc.archetype == "Sheriff"):
            # Chance to survive if not "Obliterated" (HP > -20)
            if p2.hp > -20 and random.random() < 0.4: # 40% chance
                survived = True
                npc.alive = True
                npc.hp = 10 # Barely alive
                npc.add_scar(random.choice(["Ugly Scar", "Limp", "One Eye", "Broken Hand"]))
                npc.add_memory("Player defeated me in a duel", -50)
                if npc not in world.active_npcs:
                    world.active_npcs.append(npc)
                log_lines.append("You leave them for dead...")
            else:
                npc.alive = False # Confirmed kill
        else:
            if npc: npc.alive = False

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
            
        player.duel_wins += 1
        wait_for_user(log_lines, player=player)
            
        if not (is_sheriff or npc.archetype == "Sheriff") and not survived:
            renderer.render(
                log_text=["Loot them? (Y/N)"],
                buttons=[{"label": "Loot", "key": "Y"}, {"label": "Leave", "key": "N"}]
            )
            if renderer.get_input() == "Y":
                loot_screen(player, world, npc)
        elif survived:
            # Can't loot if they crawled away or you left them
            pass

    elif not p1.alive:
        print("\nDEFEAT.")
        player.duel_losses += 1
        wait_for_user(final_log + ["", "DEFEAT."], player=player)
        
    else:
        # Knocked Out
        if not p1.conscious:
            print("\nKNOCKED OUT.")
            player.duel_losses += 1
            wait_for_user(final_log + ["", "KNOCKED OUT."], player=player)
            handle_doctor_visit(player, world)
            return True # Signal that player was moved

def handle_blackout(player, world):
    renderer.render(log_text=["Everything goes black..."], player=player)
    time.sleep(2)
    
    player.drunk_counter = 0
    world.week += 1
    update_world_simulation(world, player)
    
    # Determine Outcome
    roll = random.random()
    
    # 1. Jail (High Heat or Bad Luck)
    heat = world.get_local_heat()
    jail_chance = 0.1 + (heat / 200.0) # 10% to 60%
    
    if roll < jail_chance:
        # Jail
        renderer.render(log_text=["You wake up in a cell."], player=player)
        wait_for_user()
        handle_crime(player, world, "public intoxication")
        return

    # 2. Room (If rented)
    if player.weeks_rent_paid > 0:
        player.weeks_rent_paid -= 1
        player.hp = min(player.max_hp, player.hp + 10)
        renderer.render(log_text=["You wake up in your room with a splitting headache.", "At least you made it home."], player=player)
        wait_for_user()
        return
        
    # 3. Outside (Default)
    loss = random.randint(1, 10)
    player.cash = max(0, player.cash - loss)
    player.reputation = max(0, player.reputation - 5)
    player.honor -= 5
    
    renderer.render(
        log_text=[
            "You wake up face down in the dirt.", 
            f"Your pockets feel lighter. (Lost ${loss})",
            "People are staring. (-5 Rep, -5 Honor)"
        ], 
        player=player
    )
    wait_for_user()

def handle_doctor_visit(player, world):
    renderer.render(log_text=["You are dragged to the Doctor's office."], player=player)
    time.sleep(2)
    
    cost = 10.0
    if player.cash >= cost:
        player.cash -= cost
        msg = f"Doctor takes ${cost:.2f} fee."
    else:
        player.cash = 0
        msg = "Doctor takes what cash you have."
        
    player.hp = min(player.max_hp, player.hp + 20)
    player.blood = player.max_blood
    player.conscious = True
    player.injuries = [] # Heal injuries? Maybe just stabilize.
    
    world.week += 1
    if player.weeks_rent_paid > 0:
        player.weeks_rent_paid -= 1
        
    update_world_simulation(world, player)
    
    renderer.render(
        log_text=[
            "Doctor: 'You're lucky to be alive.'",
            msg,
            "Wounds patched. (+20 HP, Blood Restored)",
            "One week passes."
        ], 
        player=player
    )
    wait_for_user()
