import os
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_hud(player, world):
    clear_screen()
    print("="*80)
    
    # Top Bar: Location | Time | Week | Weather
    print(f" {world.town_name.upper():<20} | {world.time_of_day:<10} | Week {world.week:<3} | {world.weather}")
    print("-" * 80)
    
    # Left Column: Player Info & Stats
    # Right Column: Status & Inventory
    
    # Helper for columns
    c1_w = 35
    
    # Row 1: Name & Cash
    print(f" NAME: {player.name:<23} | CASH: ${player.cash:.2f}")
    
    # Row 2: Honor & Bounty
    honor_str = "Neutral"
    if player.honor > 20: honor_str = "Honorable"
    if player.honor < -20: honor_str = "Outlaw"
    
    # Get local bounty/rep
    town = world.towns.get(world.town_name)
    local_bounty = town.bounty if town else 0.0
    local_rep_val = town.reputation if town else 0
    
    print(f" HONOR: {player.honor:<4} ({honor_str:<9}) | BOUNTY: ${local_bounty:.2f} (Global: ${player.bounty:.2f})")
    
    # Row 3: Health & Blood
    hp_bar = f"{player.hp}/{player.max_hp}"
    blood_bar = "🩸" * player.blood
    print(f" HP: {hp_bar:<25} | BLOOD: {blood_bar}")
    
    print("-" * 80)
    
    # Stats Block
    print(f" [STATS] ACC: {player.get_acc():<3} SPD: {player.get_spd():<3} CHARM: {player.charm:<2} | [BRAWL] ATK: {player.brawl_atk:<3} DEF: {player.brawl_def:<3}")
    
    # Equipment Block
    wpn = player.equipped_weapon.name if player.equipped_weapon else "None"
    horse = player.horse.name if player.horse else "No Horse"
    hat_str = f"{player.hat.name} ({player.hat.holes} holes)" if player.hat else "No Hat"
    
    print(f" [EQUIP] WEAPON: {wpn:<20} | AMMO: {player.ammo:<3} rounds")
    print(f"         HORSE:  {horse:<20} | HAT:  {hat_str}")
    print(f"         RENT:   {player.weeks_rent_paid} weeks left")
    
    # Injuries
    if player.injuries:
        print(f" [INJURIES] {', '.join(player.injuries)}")
    else:
        print(f" [INJURIES] None")
        
    print("="*80)

def get_menu_choice(options):
    for key, value in options.items():
        print(f" [{key}] {value}")
    
    while True:
        choice = input("\n> ").strip().upper()
        if choice in options:
            return choice
        print("Invalid choice.")
