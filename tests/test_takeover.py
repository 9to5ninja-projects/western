import time
import random
from game_state import PlayerState, Town, WorldState
from characters import NPC
from shootout_engine import ShootoutEngine

def run_scenario(name, player_gang_size, town_traits, mayor_status="Alive"):
    print(f"\n=== SCENARIO: {name} ===")
    
    # Setup Player
    p = PlayerState("Boss")
    p.is_gang_leader = True
    p.gang = [NPC("Outlaw") for _ in range(player_gang_size)]
    print(f"Player Gang: {len(p.gang)} members")
    
    # Setup Town
    t = Town("Test Town", "A test town", town_traits)
    t.mayor_status = mayor_status
    print(f"Town: {t.name} | Traits: {t.traits} | Mayor: {t.mayor_status}")
    print(f"Lawfulness: {t.lawfulness}")
    
    # Calculate Defenders (Logic from main.py)
    defenders_count = 3 + (t.lawfulness // 20)
    if "Fortified" in t.traits: defenders_count += 2
    
    print(f"Defenders: {defenders_count} (Sheriff + Deputies)")
    
    # Setup Teams
    player_team = [p] + p.gang
    enemy_team = [NPC("Sheriff")] + [NPC("Cowboy") for _ in range(defenders_count)]
    
    # Run Engine
    print("Starting Simulation...")
    engine = ShootoutEngine(player_team, enemy_team, mode="takeover")
    
    turn = 0
    while True:
        # Auto-play for test
        # We need to override player input or just rely on AI if we can.
        # ShootoutEngine.player_turn asks for input.
        # Let's monkey-patch player_turn to be ai_turn for testing
        engine.player_turn = engine.ai_turn 
        
        cont = engine.run_turn()
        turn += 1
        if not cont or turn > 50: # Limit turns
            break
            
    # Results
    p_alive = sum(1 for u in engine.team_0 if u.alive)
    e_alive = sum(1 for u in engine.team_1 if u.alive)
    
    print(f"Result: Player Team Alive: {p_alive}/{len(player_team)} | Enemy Team Alive: {e_alive}/{len(enemy_team)}")
    if p.alive and e_alive == 0:
        print("OUTCOME: VICTORY")
    else:
        print("OUTCOME: DEFEAT")

if __name__ == "__main__":
    # Scenario 1: The Big Heist (Rich Town)
    run_scenario("Rich Town Takeover", 5, ["Rich"], "Alive")
    
    # Scenario 2: Chaos (Dead Mayor)
    run_scenario("Chaos Takeover", 5, ["Rich"], "Dead")
    
    # Scenario 3: Fortified Struggle
    run_scenario("Fortified Assault", 8, ["Fortified", "Rich"], "Alive")
