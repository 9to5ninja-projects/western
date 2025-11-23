import random
from game_state import PlayerState
from duel_engine_v2 import DuelEngineV2, Combatant, Action

def run_brawl_sim(player_stats, iterations=10):
    wins = 0
    total_hp_loss = 0
    
    print(f"Simulating {iterations} brawls with stats: Atk {player_stats['atk']}, Def {player_stats['def']}")
    
    for _ in range(iterations):
        # Setup Player
        p1 = Combatant("Player", -1)
        p1.brawl_atk = player_stats['atk']
        p1.brawl_def = player_stats['def']
        p1.hp = 100
        
        # Setup Drunkard (Standard Enemy)
        p2 = Combatant("Drunkard", 1)
        p2.brawl_atk = 8
        p2.brawl_def = 5
        p2.hp = 60
        
        engine = DuelEngineV2(p1, p2)
        
        # Run Fight (Simplified Loop without rendering)
        while p1.conscious and p2.conscious:
            # Simple AI: Both punch 70% of time
            p1_act = Action.PUNCH if random.random() < 0.8 else Action.WAIT
            p2_act = Action.PUNCH if random.random() < 0.7 else Action.WAIT
            
            engine.run_turn(p1_act, p2_act)
            
        if p1.conscious:
            wins += 1
        
        total_hp_loss += (100 - p1.hp)
        
    avg_hp_loss = total_hp_loss / iterations
    print(f"Results: {wins}/{iterations} Wins. Avg HP Loss: {avg_hp_loss:.1f}\n")

def main():
    print("=== BRAWL PROGRESSION TEST ===\n")
    
    # 1. Base Stats (New Character)
    # Default PlayerState has brawl_atk=5, brawl_def=5 (checking game_state.py defaults would be good, assuming 5/5)
    base_stats = {'atk': 5, 'def': 5}
    run_brawl_sim(base_stats)
    
    # 2. After Working at Stables 3 times (+3 Atk, +3 Def)
    trained_stats = {'atk': 8, 'def': 8}
    print("...Working at stables 3 times (+3 Atk/Def)...")
    run_brawl_sim(trained_stats)
    
    # 3. After Working at Stables 10 times (+10 Atk, +10 Def)
    master_stats = {'atk': 15, 'def': 15}
    print("...Working at stables 10 times (+10 Atk/Def)...")
    run_brawl_sim(master_stats)

if __name__ == "__main__":
    main()
