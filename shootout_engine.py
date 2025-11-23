import random
import time
import os
from visualizer import renderer

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
        
        # Position for Takeover Mode (0-100)
        # Team 0 starts at 10, Team 1 starts at 90
        self.position = 10 if team_id == 0 else 90

    def take_damage(self, amount):
        self.hp -= amount
        if self.is_player:
            self.source.hp = max(0, self.hp) # Sync back immediately
        if self.hp <= 0:
            self.alive = False
            if not self.is_player:
                self.source.alive = False # Kill NPC

class ShootoutEngine:
    def __init__(self, player_team, enemy_team, mode="standard"):
        self.mode = mode # "standard" or "takeover"
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
        # Build Log Text for GUI
        log_lines = [f"=== SHOOTOUT TURN {self.turn} [{self.mode.upper()}] ==="]
        
        # Visualizer Text Construction
        log_lines.append(f"{'YOUR GANG':<20} | {'ENEMIES':<20}")
        
        max_rows = max(len(self.team_0), len(self.team_1))
        
        for i in range(max_rows):
            # Left
            l_str = ""
            if i < len(self.team_0):
                u = self.team_0[i]
                status = "DEAD" if not u.alive else f"{u.hp}/{u.max_hp}"
                cover = f"[{'='*u.cover_level}]" if u.alive else ""
                pos_str = f"@{u.position}" if self.mode == "takeover" and u.alive else ""
                l_str = f"{u.name[:10]:<10} {status:<6} {cover} {pos_str}"
            
            # Right
            r_str = ""
            if i < len(self.team_1):
                u = self.team_1[i]
                status = "DEAD" if not u.alive else f"{u.hp}/{u.max_hp}"
                cover = f"[{'='*u.cover_level}]" if u.alive else ""
                pos_str = f"@{u.position}" if self.mode == "takeover" and u.alive else ""
                r_str = f"{pos_str} {cover} {status:>6} {u.name[:10]:>10}"
                
            log_lines.append(f"{l_str:<30} | {r_str:<30}")
            
        if self.mode == "takeover":
            # Draw a simple line visualizer
            line = ["."] * 40
            # Mark approximate positions
            for u in self.team_0:
                if u.alive: line[min(39, int(u.position/2.5))] = "P"
            for u in self.team_1:
                if u.alive: line[min(39, int(u.position/2.5))] = "E"
            log_lines.append(f"FIELD: [0] {''.join(line)} [100]")

        for l in self.log[-3:]: # Show last 3 logs
            log_lines.append(f"> {l}")
            
        renderer.render(log_text=log_lines)

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
        # Prepare GUI for Player Turn
        log_lines = [f"YOUR TURN ({unit.name})", f"HP: {unit.hp} | Ammo: {unit.ammo} | Cover: {unit.cover_level}"]
        if self.mode == "takeover":
            log_lines.append(f"Position: {unit.position}/100")
            
        log_lines.append("Targets:")
        target_buttons = []
        for i, e in enumerate(enemies):
            dist_info = ""
            if self.mode == "takeover":
                dist = abs(unit.position - e.position)
                dist_info = f" (Dist: {dist})"
            log_lines.append(f"{i+1}. {e.name} (HP: {e.hp}, Cover: {e.cover_level}){dist_info}")
            target_buttons.append({"label": f"Shoot {e.name[:6]}", "key": str(i+1)})
            
        # Action Buttons
        action_buttons = target_buttons + [
            {"label": "Cover", "key": "C"},
            {"label": "Reload", "key": "R"},
            {"label": "Auto-Play", "key": "A"}
        ]
        if self.mode == "takeover":
            action_buttons.append({"label": "Move", "key": "M"})
        
        renderer.render(log_text=log_lines, buttons=action_buttons)
        
        while True:
            choice = renderer.get_input()
            
            # Check if choice is a target index
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(enemies):
                    self.attack(unit, enemies[idx])
                    break
            except ValueError:
                pass
                
            if choice == "C":
                unit.cover_level = min(2, unit.cover_level + 1)
                self.log.append(f"{unit.name} takes cover.")
                break
            elif choice == "R":
                unit.ammo = 6
                self.log.append(f"{unit.name} reloads.")
                break
            elif choice == "M" and self.mode == "takeover":
                # Move forward
                move_dist = random.randint(10, 20)
                unit.position = min(100, unit.position + move_dist)
                unit.cover_level = 0 # Moving exposes you
                self.log.append(f"{unit.name} advances to position {unit.position}!")
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

        # Takeover Logic: Advance if too far back
        if self.mode == "takeover":
            # Team 1 (Enemy) wants to go to 0. Team 0 (Player AI?) wants to go to 100.
            target_pos = 0 if unit.team_id == 1 else 100
            dist_to_goal = abs(unit.position - target_pos)
            
            # If healthy and far from goal, move
            if unit.hp > unit.max_hp * 0.4 and dist_to_goal > 30:
                if random.random() < 0.5: # 50% chance to move instead of shoot
                    move_dist = random.randint(10, 20)
                    if unit.team_id == 1:
                        unit.position = max(0, unit.position - move_dist)
                    else:
                        unit.position = min(100, unit.position + move_dist)
                    unit.cover_level = 0
                    self.log.append(f"{unit.name} advances to position {unit.position}!")
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
        
        # Distance Modifier (Takeover Mode)
        if self.mode == "takeover":
            dist = abs(attacker.position - target.position)
            # Closer is better. 
            # Dist 0: +30%
            # Dist 100: -20%
            # Formula: 30 - (dist / 2)
            mod = 30 - (dist / 2)
            hit_chance += mod
        
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

