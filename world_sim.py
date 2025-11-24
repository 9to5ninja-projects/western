import random
from characters import NPC
from game_state import Gang

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
