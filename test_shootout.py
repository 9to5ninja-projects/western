from shootout_engine import ShootoutEngine
from characters import NPC
from game_state import PlayerState

def test_shootout():
    print("Testing Shootout Engine...")
    
    # Setup Player Team
    p = PlayerState("Test Player")
    p.acc_base = 50
    p.hp = 100
    
    gang_member = NPC("Outlaw")
    gang_member.name = "Gangster Joe"
    
    player_team = [p, gang_member]
    
    # Setup Enemy Team
    enemies = [NPC("Sheriff"), NPC("Cowboy")]
    
    engine = ShootoutEngine(player_team, enemies)
    
    while True:
        engine.render()
        cont = engine.run_turn()
        if not cont:
            break
            
    print("Shootout Over")

if __name__ == "__main__":
    test_shootout()
