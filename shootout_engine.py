import random
import time
import os

class ShootoutCombatant:
    def __init__(self, source_obj, team_id, is_player=False):
        self.source = source_obj
        self.team_id = team_id # 0: Player Team (Left), 1: Enemy Team (Right)
        self.is_player = is_player
        self.name = source_obj.name
        
        # Extract Stats
        if is_player:
            self.hp = source_obj.hp
            self.max_hp = source_obj.max_hp
            self.acc = source_obj.get_acc()
            self.spd = source_obj.get_spd()
        else:
            self.hp = source_obj.hp
            self.max_hp = source_obj.max_hp
            self.acc = source_obj.acc
            self.spd = source_obj.spd
            
        self.alive = True
        self.cover_level = 0 # 0: None, 1: Light (25%), 2: Heavy (50%)
        self.ammo = 6

    def take_damage(self, amount):
        self.hp -= amount
        if self.is_player:
            self.source.hp = max(0, self.hp) # Sync back immediately
        if self.hp <= 0:
            self.alive = False
            if not self.is_player:
                self.source.alive = False # Kill NPC

class ShootoutEngine:
    def __init__(self, player_team, enemy_team):
        # Teams are lists of source objects (PlayerState or NPC)
        self.team_0 = [ShootoutCombatant(p, 0, is_player=(i==0 and p.name == player_team[0].name)) for i, p in enumerate(player_team)]
        self.team_1 = [ShootoutCombatant(e, 1) for e in enemy_team]
        self.all_units = self.team_0 + self.team_1
        self.turn = 0
        self.log = []

    def get_living_enemies(self, my_team_id):
        targets = self.team_1 if my_team_id == 0 else self.team_0
        return [t for t in targets if t.alive]

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n=== SHOOTOUT TURN {self.turn} ===")
        
        # Visualizer
        # Left Side (Team 0)       Right Side (Team 1)
        # [P] Player (HP)          [E] Outlaw (HP)
        
        max_rows = max(len(self.team_0), len(self.team_1))
        
        print(f"{'YOUR GANG':<35} | {'ENEMIES':<35}")
        print("-" * 75)
        
        for i in range(max_rows):
            # Left
            l_str = ""
            if i < len(self.team_0):
                u = self.team_0[i]
                status = "DEAD" if not u.alive else f"{u.hp}/{u.max_hp}"
                cover = f"[{'='*u.cover_level}]" if u.alive else ""
                l_str = f"{u.name[:15]:<15} {status:<8} {cover}"
            
            # Right
            r_str = ""
            if i < len(self.team_1):
                u = self.team_1[i]
                status = "DEAD" if not u.alive else f"{u.hp}/{u.max_hp}"
                cover = f"[{'='*u.cover_level}]" if u.alive else ""
                r_str = f"{cover} {status:>8} {u.name[:15]:>15}"
                
            print(f"{l_str:<35} | {r_str:<35}")
            
        print("-" * 75)
        for l in self.log[-5:]: # Show last 5 logs
            print(f"> {l}")

    def run_turn(self):
        self.turn += 1
        self.log = []
        
        # Sort by Speed (Initiative)
        # Add some random variance
        queue = sorted([u for u in self.all_units if u.alive], key=lambda x: x.spd + random.randint(-5, 5), reverse=True)
        
        for unit in queue:
            if not unit.alive: continue
            
            enemies = self.get_living_enemies(unit.team_id)
            if not enemies:
                break # Combat over
                
            # AI / Player Logic
            if unit.is_player:
                self.player_turn(unit, enemies)
            else:
                self.ai_turn(unit, enemies)
                
        # Check Win Condition
        t0_alive = any(u.alive for u in self.team_0)
        t1_alive = any(u.alive for u in self.team_1)
        
        return t0_alive and t1_alive # Returns True if fight continues

    def player_turn(self, unit, enemies):
        print(f"\nYOUR TURN ({unit.name})")
        print(f"HP: {unit.hp} | Ammo: {unit.ammo} | Cover: {unit.cover_level}")
        print("Targets:")
        for i, e in enumerate(enemies):
            print(f"{i+1}. {e.name} (HP: {e.hp}, Cover: {e.cover_level})")
            
        print("Actions: [S]hoot, [C]over, [R]eload, [A]uto-Play Turn")
        
        while True:
            choice = input("> ").upper()
            if choice == "S":
                try:
                    idx = int(input("Target #: ")) - 1
                    if 0 <= idx < len(enemies):
                        self.attack(unit, enemies[idx])
                        break
                except: pass
            elif choice == "C":
                unit.cover_level = min(2, unit.cover_level + 1)
                self.log.append(f"{unit.name} takes cover.")
                break
            elif choice == "R":
                unit.ammo = 6
                self.log.append(f"{unit.name} reloads.")
                break
            elif choice == "A":
                # Auto-play logic for player
                self.ai_turn(unit, enemies)
                break

    def ai_turn(self, unit, enemies):
        # Simple AI
        # If low ammo, reload
        if unit.ammo <= 0:
            unit.ammo = 6
            self.log.append(f"{unit.name} reloads.")
            return

        # If exposed and hurt, take cover
        if unit.cover_level == 0 and unit.hp < unit.max_hp * 0.5:
            unit.cover_level = 1
            self.log.append(f"{unit.name} scrambles for cover.")
            return
            
        # Otherwise shoot random target
        target = random.choice(enemies)
        self.attack(unit, target)

    def attack(self, attacker, target):
        if attacker.ammo <= 0:
            self.log.append(f"{attacker.name} clicks on empty!")
            return
            
        attacker.ammo -= 1
        
        # Hit Chance
        # Base Acc vs Base Def (Speed?) + Cover
        hit_chance = attacker.acc
        
        # Cover Penalty
        if target.cover_level == 1: hit_chance -= 25
        if target.cover_level == 2: hit_chance -= 50
        
        roll = random.randint(0, 100)
        if roll < hit_chance:
            # CRITICAL LETHALITY: Shootouts are deadly.
            # Base damage 20-40 (vs 100 HP usually means 3-4 shots kill)
            # Headshots/Crits can kill instantly
            
            dmg = random.randint(20, 45)
            
            # Critical Hit Chance (10%)
            if random.random() < 0.10:
                dmg *= 2
                self.log.append(f"CRITICAL HIT! {attacker.name} blasts {target.name} for {dmg} dmg!")
            else:
                self.log.append(f"{attacker.name} hits {target.name} for {dmg} dmg!")
                
            target.take_damage(dmg)
        else:
            self.log.append(f"{attacker.name} shoots at {target.name} and misses!")

