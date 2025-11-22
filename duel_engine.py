import random
from enum import Enum

class BodyPart(Enum):
    HEAD = "head"
    NECK = "neck"
    CHEST = "chest"
    ARM_L = "left arm"
    ARM_R = "right arm"
    LEG_L = "left leg"
    LEG_R = "right leg"
    MISS = "miss"

class VerticalState(Enum):
    STANDING = "standing"
    DUCKING = "ducking"
    JUMPING = "jumping"

class AimZone(Enum):
    HIGH = "high"
    CENTER = "center"
    LOW = "low"

class Action(Enum):
    SHOOT_HIGH = "shoot_high"
    SHOOT_CENTER = "shoot_center"
    SHOOT_LOW = "shoot_low"
    RELOAD = "reload"
    STEP_FORWARD = "step_forward"
    STEP_BACK = "step_back"
    FLEE = "flee"
    DUCK = "duck"
    JUMP = "jump"
    TAKE_COVER = "take_cover"
    SURRENDER = "surrender"

class Combatant:
    def __init__(self, name):
        self.name = name
        self.body_parts = {
            BodyPart.HEAD: 20,
            BodyPart.NECK: 15,
            BodyPart.CHEST: 50,
            BodyPart.ARM_L: 30,
            BodyPart.ARM_R: 30,
            BodyPart.LEG_L: 40,
            BodyPart.LEG_R: 40,
        }
        self.ammo = 6
        self.position = 0
        self.vertical_state = VerticalState.STANDING
        self.acc = 60
        self.spd = 50
        self.luck = 50
        self.has_horse = False
        self.behind_cover = False
        self.alive = True
        self.injuries = []
        self.bleeding = False
        
    def is_alive(self):
        return (self.body_parts[BodyPart.HEAD] > 0 and 
                self.body_parts[BodyPart.CHEST] > 0 and
                self.alive)
    
    def apply_damage(self, body_part, damage):
        if body_part == BodyPart.MISS:
            return
        
        old_hp = self.body_parts[body_part]
        self.body_parts[body_part] = max(0, old_hp - damage)
        
        if body_part == BodyPart.HEAD and self.body_parts[body_part] <= 0:
            self.alive = False
        if body_part == BodyPart.CHEST and self.body_parts[body_part] <= 10:
            self.alive = False
            
        if body_part in [BodyPart.ARM_L, BodyPart.ARM_R] and damage > 15:
            self.acc -= 15
            self.injuries.append(f"{body_part.value} wounded")
            
        if body_part in [BodyPart.LEG_L, BodyPart.LEG_R] and damage > 20:
            self.spd -= 20
            self.injuries.append(f"{body_part.value} crippled")

        if damage > 15:
            self.bleeding = True
    
    def get_status(self):
        status = f"\n{self.name}:"
        status += f"\n  Position: {abs(self.position)} paces from center"
        status += f"\n  Ammo: [{'●' * self.ammo}{'○' * (6 - self.ammo)}]"
        status += f"\n  State: {self.vertical_state.value}"
        if self.behind_cover:
            status += " (BEHIND COVER)"
        status += f"\n  Health:"
        for part, hp in self.body_parts.items():
            marker = "💀" if hp <= 0 else "🩸" if hp < 20 else ""
            status += f"\n    {part.value}: {hp} {marker}"
        if self.injuries:
            status += f"\n  Injuries: {', '.join(set(self.injuries))}"
        if self.bleeding:
            status += f"\n  STATUS: BLEEDING"
        return status

class DuelEngine:
    def __init__(self):
        self.player = Combatant("YOU")
        self.opponent = Combatant("OPPONENT")
        self.turn = 0
        self.log = []
        
    def calculate_hit(self, shooter, target, aim_zone):
        if target.behind_cover:
            if random.random() < 0.3:
                if shooter.has_horse:
                    shooter.has_horse = False
                    return BodyPart.MISS, 0, "Your horse takes the bullet and collapses!"
                return BodyPart.MISS, 0, "Shot hits opponent's horse! It collapses dead."
            return BodyPart.MISS, 0, "Shot blocked by cover!"
        
        distance = abs(shooter.position - target.position)
        distance_penalty = distance * 3
        hit_chance = shooter.acc - distance_penalty + (shooter.luck - 50) / 10
        
        if random.randint(0, 100) > hit_chance:
            return BodyPart.MISS, 0, "Shot misses wide!"
        
        body_part = self.determine_body_part(aim_zone, target.vertical_state)
        base_damage = random.randint(15, 35)
        
        if body_part == BodyPart.HEAD:
            base_damage *= 2
        
        return body_part, base_damage, None
    
    def determine_body_part(self, aim_zone, vertical_state):
        if aim_zone == AimZone.HIGH:
            if vertical_state == VerticalState.DUCKING:
                return BodyPart.HEAD if random.random() < 0.3 else BodyPart.MISS
            elif vertical_state == VerticalState.JUMPING:
                return random.choice([BodyPart.HEAD, BodyPart.NECK, BodyPart.CHEST])
            else:
                return random.choice([BodyPart.HEAD, BodyPart.NECK, BodyPart.CHEST])
        
        elif aim_zone == AimZone.CENTER:
            if vertical_state == VerticalState.DUCKING:
                return random.choice([BodyPart.HEAD, BodyPart.NECK])
            elif vertical_state == VerticalState.JUMPING:
                return random.choice([BodyPart.LEG_L, BodyPart.LEG_R, BodyPart.CHEST])
            else:
                return random.choice([BodyPart.CHEST, BodyPart.ARM_L, BodyPart.ARM_R])
        
        elif aim_zone == AimZone.LOW:
            if vertical_state == VerticalState.DUCKING:
                return random.choice([BodyPart.LEG_L, BodyPart.LEG_R])
            elif vertical_state == VerticalState.JUMPING:
                return random.choice([BodyPart.LEG_L, BodyPart.LEG_R]) if random.random() < 0.4 else BodyPart.MISS
            else:
                return random.choice([BodyPart.LEG_L, BodyPart.LEG_R])
        
        return BodyPart.MISS
    
    def execute_action(self, combatant, action, target):
        results = []
        
        if action not in [Action.DUCK, Action.JUMP]:
            combatant.vertical_state = VerticalState.STANDING
        combatant.behind_cover = False
        
        if action in [Action.SHOOT_HIGH, Action.SHOOT_CENTER, Action.SHOOT_LOW]:
            if combatant.ammo > 0:
                combatant.ammo -= 1
                aim = {Action.SHOOT_HIGH: AimZone.HIGH, 
                       Action.SHOOT_CENTER: AimZone.CENTER, 
                       Action.SHOOT_LOW: AimZone.LOW}[action]
                body_part, damage, msg = self.calculate_hit(combatant, target, aim)
                if msg:
                    results.append(f"{combatant.name}: {msg}")
                else:
                    target.apply_damage(body_part, damage)
                    results.append(f"{combatant.name} shoots {aim.value.upper()}. Hits {target.name}'s {body_part.value} for {damage} damage!")
            else:
                results.append(f"{combatant.name} pulls trigger. *CLICK* Empty!")
        
        elif action == Action.RELOAD:
            if combatant.ammo < 6:
                combatant.ammo += 1
                results.append(f"{combatant.name} reloads one round. [{combatant.ammo}/6]")
            else:
                results.append(f"{combatant.name}'s cylinder is full!")
        
        elif action == Action.STEP_FORWARD:
            combatant.position = max(-10, combatant.position - 1)
            results.append(f"{combatant.name} steps forward. Distance: {abs(combatant.position - (5 if combatant == self.player else -5))} paces")
        
        elif action == Action.STEP_BACK:
            combatant.position += 1
            results.append(f"{combatant.name} steps back. Distance: {abs(combatant.position - (5 if combatant == self.player else -5))} paces")
        
        elif action == Action.FLEE:
            if combatant.spd > 30:
                combatant.position += 2
                results.append(f"{combatant.name} flees backward! Distance: {abs(combatant.position - (5 if combatant == self.player else -5))} paces")
            else:
                results.append(f"{combatant.name} tries to flee but leg injuries prevent escape!")
        
        elif action == Action.DUCK:
            combatant.vertical_state = VerticalState.DUCKING
            results.append(f"{combatant.name} ducks low!")
        
        elif action == Action.JUMP:
            combatant.vertical_state = VerticalState.JUMPING
            results.append(f"{combatant.name} leaps up!")
        
        elif action == Action.TAKE_COVER:
            if combatant.has_horse and abs(combatant.position) >= 13:
                combatant.behind_cover = True
                results.append(f"{combatant.name} takes cover behind horse!")
            else:
                if not combatant.has_horse:
                    results.append(f"{combatant.name} has no horse for cover!")
                else:
                    results.append(f"{combatant.name} is too close to use horse cover!")
        
        elif action == Action.SURRENDER:
            results.append(f"{combatant.name} throws down their gun and surrenders!")
            combatant.alive = False
        
        return results
    
    def resolve_turn(self, player_action, opponent_action):
        self.turn += 1
        self.log.append(f"\n=== TURN {self.turn} ===")
        
        # Initiative Roll
        p_speed = self.player.spd + random.randint(-10, 10)
        o_speed = self.opponent.spd + random.randint(-10, 10)
        
        # Determine order
        first, second = self.player, self.opponent
        first_act, second_act = player_action, opponent_action
        
        if o_speed > p_speed:
            first, second = second, first
            first_act, second_act = second_act, first_act
            
        # Execute First
        results_1 = self.execute_action(first, first_act, second)
        self.log.extend(results_1)
        
        # Execute Second (if alive)
        if second.is_alive():
            results_2 = self.execute_action(second, second_act, first)
            self.log.extend(results_2)
        else:
            self.log.append(f"{second.name} collapses before they can act!")
            
        # Bleeding Effects
        self.log.extend(self.player.tick())
        self.log.extend(self.opponent.tick())
        
        if not self.player.is_alive() and not self.opponent.is_alive():
            self.log.append("\n*** BOTH DEAD! DOUBLE KILL! ***")
            return "draw"
        elif not self.player.is_alive():
            self.log.append(f"\n*** YOU ARE DEAD! ***")
            return "loss"
        elif not self.opponent.is_alive():
            self.log.append(f"\n*** OPPONENT DEAD! ***")
            return "win"
        
        if abs(self.player.position) >= 13:
            self.log.append(f"\n*** YOU FLED SUCCESSFULLY! ***")
            return "fled"
        if abs(self.opponent.position) >= 13:
            self.log.append(f"\n*** OPPONENT FLED! ***")
            return "win"
        
        return "continue"
    
    def display_state(self):
        print("\n" + "="*60)
        print(self.player.get_status())
        print(self.opponent.get_status())
        print("="*60)
    
    def display_log(self):
        for entry in self.log[-15:]:
            print(entry)
        self.log = []
    
    def get_player_action(self):
        print("\n[1] Shoot HIGH    [2] Shoot CENTER  [3] Shoot LOW")
        print("[4] Reload        [5] Step Forward  [6] Step Back")
        print("[7] Flee          [8] Duck          [9] Jump")
        print("[10] Take Cover   [11] Surrender")
        
        action_map = {
            "1": Action.SHOOT_HIGH, "2": Action.SHOOT_CENTER, "3": Action.SHOOT_LOW,
            "4": Action.RELOAD, "5": Action.STEP_FORWARD, "6": Action.STEP_BACK,
            "7": Action.FLEE, "8": Action.DUCK, "9": Action.JUMP,
            "10": Action.TAKE_COVER, "11": Action.SURRENDER,
        }
        
        while True:
            choice = input("\nAction: ").strip()
            if choice in action_map:
                return action_map[choice]
            print("Invalid!")
    
    def get_ai_action(self):
        if self.opponent.ammo == 0:
            return Action.RELOAD
        
        if self.opponent.body_parts[BodyPart.CHEST] < 20:
            if random.random() < 0.5:
                return Action.FLEE
        
        if self.opponent.ammo <= 2 and random.random() < 0.4:
            return Action.RELOAD
        
        if random.random() < 0.15:
            return random.choice([Action.DUCK, Action.JUMP])
        
        return random.choice([Action.SHOOT_HIGH, Action.SHOOT_CENTER, Action.SHOOT_LOW])
    
    def run(self):
        print("\n" + "="*60)
        print("         WESTERN STANDOFF - DUEL ENGINE")
        print("="*60)
        print("\nYou face your opponent. The sun beats down.")
        print("Draw when ready. Survive if you can.\n")
        
        self.player.position = -5
        self.opponent.position = 5
        self.player.has_horse = True
        
        while True:
            self.display_state()
            player_action = self.get_player_action()
            opponent_action = self.get_ai_action()
            result = self.resolve_turn(player_action, opponent_action)
            self.display_log()
            
            if result != "continue":
                print("\n" + "="*60)
                if result == "win":
                    print("VICTORY! You survived!")
                elif result == "loss":
                    print("DEFEAT! You died in the dust!")
                elif result == "draw":
                    print("DOUBLE KILL!")
                elif result == "fled":
                    print("You fled! Dishonor...")
                print("="*60)
                break

if __name__ == "__main__":
    duel = DuelEngine()
    duel.run()
