import random
import time
from game_state import ItemType
from characters import NPC
from duel_engine_v2 import DuelEngineV2, Combatant, Action, Orientation, ai_honorable
from visualizer import renderer
from game_utils import wait_for_user

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
        wait_for_user(log_msg, player=player)
    else:
        start_duel(player, world, is_sheriff=True)

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
        renderer.render_duel_state(engine, p1, p2)
        
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
    
    p1 = Combatant(player.name, -1, player)
    p2 = Combatant(npc.name, 1)
    p2.acc = npc.acc
    p2.spd = npc.spd
    p2.hp = npc.hp
    p2.max_hp = npc.max_hp
    
    engine = DuelEngineV2(p1, p2)
    
    # Duel Loop
    turn_count = 0
    while p1.alive and p2.alive and turn_count < 20:
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
        
        # Define primary buttons for GUI (limited space)
        duel_buttons = [
            {"label": "SHOOT CENTER", "key": "4"},
            {"label": "DRAW / RELOAD", "key": "3/7"},
            {"label": "PACE / TURN", "key": "1/2"},
            {"label": "DUCK / JUMP", "key": "8/J"}
        ]
        
        # Contextual Actions
        if p1.is_ducking:
             duel_buttons.append({"label": "RISE & FIRE", "key": "R"})
        else:
             duel_buttons.append({"label": "DUCK & FIRE", "key": "D"})

        if p1.orientation == Orientation.FACING_OPPONENT and engine.get_distance() <= 3:
            duel_buttons.append({"label": "KICK SAND", "key": "K"})
            
        if engine.get_distance() <= 2:
            duel_buttons.append({"label": "PUNCH", "key": "P"})
        
        log_lines = engine.log[-5:] if engine.log else ["Duel started."]
        
        # Detailed Stats
        stats_text = []
        
        # Player 1 (User)
        stats_text.append(f"--- {p1.name} ---")
        stats_text.append(f"HP: {p1.hp}/{p1.max_hp}")
        stats_text.append(f"Blood: {p1.blood}")
        
        # Visual Ammo
        ammo_p1 = "|" * p1.ammo + "." * (6 - p1.ammo)
        stats_text.append(f"Ammo: [{ammo_p1}]")
        
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
            wait_for_user([f"{p2.name} accepts your surrender."], player=player)
            p1.conscious = False # End loop
            # Consequences?
            loss = random.randint(5, 15)
            player.cash = max(0, player.cash - loss)
            print(f"They took ${loss} from you.")
            break
            
        turn_count += 1
        
        if not p1.conscious:
            break
        
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
            
        player.duel_wins += 1
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
        player.duel_losses += 1
        wait_for_user(final_log + ["", "DEFEAT."], player=player)
        
    else:
        # Draw or Knocked Out
        if not p1.conscious:
            print("\nKNOCKED OUT.")
            player.duel_losses += 1
            wait_for_user(final_log + ["", "KNOCKED OUT."], player=player)
            handle_doctor_visit(player, world)
            return True # Signal that player was moved
        else:
            print("\nDRAW.")
            wait_for_user(final_log + ["", "DRAW (Time Limit Reached)."], player=player)

def handle_blackout(player, world):
    renderer.render(log_text=["Everything goes black..."], player=player)
    time.sleep(2)
    
    player.drunk_counter = 0
    world.week += 1
    
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
