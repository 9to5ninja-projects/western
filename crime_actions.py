import time
import random
from ui import get_menu_choice, clear_screen
from visualizer import renderer
from game_utils import wait_for_user
from shootout_engine import ShootoutEngine
from combat_runner import process_gang_casualties, start_duel
from characters import NPC

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
