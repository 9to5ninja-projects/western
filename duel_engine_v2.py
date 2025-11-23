import random
import time
import os
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

class WeaponState(Enum):
    HOLSTERED = "holstered"
    DRAWN = "drawn"
    DROPPED = "dropped"

class Orientation(Enum):
    FACING_OPPONENT = "facing opponent"
    FACING_AWAY = "facing away"

class Action(Enum):
    PACE = "pace"           # Move 1 away from center
    STEP_IN = "step_in"     # Move 1 toward center
    FLEE = "flee"           # Move 2 away from center (if > 13)
    TURN = "turn"           # Toggle orientation
    DRAW = "draw"           # Holstered -> Drawn
    PICK_UP = "pick_up"     # Dropped -> Drawn
    SHOOT_HIGH = "shoot_high"
    SHOOT_CENTER = "shoot_center"
    SHOOT_LOW = "shoot_low"
    RELOAD = "reload"
    DUCK = "duck"           # Toggle stance (Action)
    STAND = "stand"         # Toggle stance (Action)
    DUCK_FIRE = "duck_fire" # Duck and Shoot (Penalty)
    STAND_FIRE = "stand_fire" # Stand and Shoot (Penalty)
    JUMP = "jump"           # Instant evasion
    KICK_SAND = "kick_sand" # Dirty move (Blind)
    TAKE_COVER = "take_cover"
    PUNCH = "punch"
    JAB = "jab"             # Off-hand punch (Accurate, Low Dmg)
    HOOK = "hook"           # Dominant punch (High Dmg, Low Acc)
    SURRENDER = "surrender"
    WAIT = "wait"

class Combatant:
    def __init__(self, name, direction_multiplier, player_state=None):
        self.name = name
        self.player_state = player_state # Reference to persistent state
        
        if player_state:
            self.blood = player_state.blood
            self.max_blood = player_state.max_blood
            self.hp = player_state.hp
            self.max_hp = player_state.max_hp
            self.brawl_atk = player_state.brawl_atk
            self.brawl_def = player_state.brawl_def
            self.acc = player_state.get_acc()
            self.luck = player_state.luck_base
            self.ammo = 6 # Cylinder capacity, not total ammo
            # TODO: Load from inventory?
        else:
            # Default/NPC stats
            self.blood = 12
            self.max_blood = 12
            self.hp = 100
            self.max_hp = 100
            self.brawl_atk = 10
            self.brawl_def = 10
            self.acc = 30
            self.luck = 30
            self.ammo = 6

        self.bleeding_rate = 0
        self.conscious = True
        self.alive = True
        
        # Structural Health (Bone/Flesh integrity)
        self.body_parts = {
            BodyPart.HEAD: 20,
            BodyPart.NECK: 10,
            BodyPart.CHEST: 40,
            BodyPart.ARM_L: 20,
            BodyPart.ARM_R: 20,
            BodyPart.LEG_L: 25,
            BodyPart.LEG_R: 25,
        }
        
        self.position = 0
        self.direction_multiplier = direction_multiplier # 1 (Right) or -1 (Left)
        self.orientation = Orientation.FACING_AWAY # Start back-to-back
        
        self.weapon_state = WeaponState.HOLSTERED
        self.is_ducking = False
        self.is_jumping = False
        self.has_horse = False # Default
        self.behind_cover = False
        
        self.blinded = 0 # 0, 1, 2 eyes lost
        self.temp_blind_turns = 0 # Sand in eyes
        self.injuries = []
        self.dominant_hand = BodyPart.ARM_R
        if player_state and hasattr(player_state, 'dominant_hand'):
             self.dominant_hand = BodyPart.ARM_R if player_state.dominant_hand == "right" else BodyPart.ARM_L
        
        self.is_surrendering = False 

    def sync_state(self):
        """Syncs combat damage back to persistent player state"""
        if self.player_state:
            self.player_state.hp = self.hp
            self.player_state.blood = self.blood
            self.player_state.alive = self.alive
            self.player_state.conscious = self.conscious
            
            # Sync injuries
            for inj in self.injuries:
                if inj not in self.player_state.injuries:
                    self.player_state.injuries.append(inj)

        # Apply persistent injuries to body parts (Start broken if injured)
        if self.player_state:
            all_injuries = self.player_state.injuries + list(self.player_state.healing_injuries.keys())
            for inj in all_injuries:
                if "Broken Hand (R)" in inj: self.body_parts[BodyPart.ARM_R] = 0
                if "Broken Hand (L)" in inj: self.body_parts[BodyPart.ARM_L] = 0
                if "Broken Arm" in inj: 
                    # Generic broken arm affects both? Or random? Let's assume dominant for now or ignore
                    pass 

    def get_distance_from_center(self):
        return abs(self.position)

    def get_status(self):
        status = f"\n{self.name}:"
        status += f"\n  HP: {self.hp}/{self.max_hp} | Blood: {'🩸' * self.blood}{' ' * (12 - self.blood)} ({self.blood}/12)"
        if self.bleeding_rate > 0:
            status += f" (Bleeding -{self.bleeding_rate}/turn)"
        status += f"\n  Brawl: Atk {self.brawl_atk} / Def {self.brawl_def}"
        status += f"\n  Pos: {self.position} | Facing: {self.orientation.value}"
        status += f"\n  Weapon: {self.weapon_state.value.upper()} | Ammo: {self.ammo}/6"
        status += f"\n  Stance: {'DUCKING' if self.is_ducking else 'STANDING'}"
        if self.blinded > 0:
            status += f"\n  BLINDED ({self.blinded} eyes lost)"
        if self.temp_blind_turns > 0:
            status += f"\n  BLINDED BY SAND ({self.temp_blind_turns} turns)"
        if not self.conscious:
            status += f"\n  STATUS: UNCONSCIOUS"
        return status

class DuelEngineV2:
    def __init__(self, p1_combatant=None, p2_combatant=None):
        self.p1 = p1_combatant if p1_combatant else Combatant("PLAYER 1", -1)
        self.p2 = p2_combatant if p2_combatant else Combatant("PLAYER 2", 1)
        self.turn = 0
        self.log = []

    def get_distance(self):
        return abs(self.p1.position - self.p2.position)

    def calculate_hit(self, shooter, target, aim_zone, accuracy_penalty=0):
        msg_prefix = ""

        # 1. Check Orientation (Dirty Move Logic)
        if shooter.orientation != Orientation.FACING_OPPONENT:
            # Dirty Move: Spin and Shoot
            shooter.orientation = Orientation.FACING_OPPONENT
            accuracy_penalty += 50
            msg_prefix = "Spins and fires! "

        # 2. Check Weapon
        if shooter.weapon_state != WeaponState.DRAWN:
            return BodyPart.MISS, 0, "Weapon not drawn!"

        # 3. Check Cover
        if target.behind_cover:
            if random.random() < 0.5: # 50% cover chance
                return BodyPart.MISS, 0, "Shot hits cover!"

        # 4. Calculate Hit Chance
        dist = self.get_distance()
        
        # Base ACC
        hit_chance = shooter.acc - accuracy_penalty
        
        # Distance Penalty (High penalty for poor stats)
        hit_chance -= (dist * 2)
        
        # Offhand Penalty (if dominant arm broken)
        if shooter.body_parts[shooter.dominant_hand] <= 0:
            hit_chance -= 20
            
        # Blindness Penalty
        if shooter.temp_blind_turns > 0:
            hit_chance = 0
            msg_prefix += "(Blind Fire) "
        else:
            hit_chance -= (shooter.blinded * 25)
        
        # Target Stance
        # "if your are prone or crouched your accuraccy increases but your evasion decreases."
        if shooter.is_ducking:
            hit_chance += 15 # Steady aim
            
        if target.is_ducking:
            hit_chance += 15 # Easier target (Evasion decreases)
            
        if target.is_jumping:
            hit_chance -= 30 # Hard to hit
            
        # Luck Modifier
        hit_chance += (shooter.luck - 50) / 5
        
        # Roll
        roll = random.randint(0, 100)
        if roll > hit_chance:
            # Miss Flavor
            miss_msgs = [
                "Missed by a mile!",
                "Shot kicks up dust.",
                "Bullet whizzes past ear.",
                "Shot hits a spittoon. *DING*",
                "Shot shatters a whiskey bottle.",
                "Bullet hits a passing chicken.",
                "Shot knocks a hat off a bystander."
            ]
            flavor = random.choice(miss_msgs)
            return BodyPart.MISS, 0, f"{msg_prefix}Miss! {flavor}"

        # 5. Determine Hit Location
        # Simplified scatter based on aim
        parts = []
        if aim_zone == Action.SHOOT_HIGH:
            parts = [BodyPart.HEAD]*2 + [BodyPart.NECK]*2 + [BodyPart.CHEST]*1
        elif aim_zone == Action.SHOOT_CENTER:
            parts = [BodyPart.CHEST]*4 + [BodyPart.ARM_L, BodyPart.ARM_R, BodyPart.NECK]
        elif aim_zone == Action.SHOOT_LOW:
            parts = [BodyPart.LEG_L, BodyPart.LEG_R, BodyPart.CHEST]
            
        hit_part = random.choice(parts)
        
        # 6. Calculate Effects
        msg = f"{msg_prefix}Hits {hit_part.value}!"
        damage_blood = 1 # Base blood loss for any hit
        
        # Structural Damage
        struct_dmg = random.randint(5, 15)
        target.body_parts[hit_part] = max(0, target.body_parts[hit_part] - struct_dmg)
        
        # Check for Injury
        if target.body_parts[hit_part] <= 0:
            injury_name = None
            if hit_part in [BodyPart.ARM_L, BodyPart.ARM_R]: injury_name = "Broken Arm"
            elif hit_part in [BodyPart.LEG_L, BodyPart.LEG_R]: injury_name = "Broken Leg"
            elif hit_part == BodyPart.HEAD and target.alive: injury_name = "Concussion"
            elif hit_part == BodyPart.CHEST: injury_name = "Cracked Ribs"
            
            if injury_name and injury_name not in target.injuries:
                target.injuries.append(injury_name)
                msg += f" CRITICAL INJURY: {injury_name}!"
        
        # Specific Part Effects
        if hit_part == BodyPart.HEAD:
            # Check for Hat Shot (Near Miss or Glancing Blow)
            if random.random() < 0.3 and target.player_state and target.player_state.hat:
                target.player_state.hat.holes += 1
                msg += f" Bullet punches a hole in their {target.player_state.hat.name}!"
                # No extra damage, just hat damage
            elif random.random() < 0.4: # 40% Fatal Headshot
                damage_blood = 12
                msg += " FATAL HEADSHOT!"
            else:
                target.blinded += 1
                msg += " Eye shot out! Blinded!"
                damage_blood += 2
                
        elif hit_part == BodyPart.NECK:
            target.bleeding_rate += 2
            msg += " Arterial spray! Heavy bleeding."
            
        elif hit_part == BodyPart.CHEST:
            if random.random() < 0.15: # Heart shot
                damage_blood = 12
                msg += " HEART SHOT! Instant death."
            else:
                target.bleeding_rate += 1
                msg += " Lung/Gut hit. Bleeding started."
                
        elif hit_part in [BodyPart.ARM_L, BodyPart.ARM_R]:
            if target.weapon_state == WeaponState.DRAWN:
                if random.random() < 0.5:
                    target.weapon_state = WeaponState.DROPPED
                    msg += " Weapon dropped!"
                    
        return hit_part, damage_blood, msg

    def resolve_punch(self, attacker, defender, punch_type=Action.PUNCH):
        # Determine Hand Used
        hand_used = attacker.dominant_hand
        off_hand = BodyPart.ARM_L if attacker.dominant_hand == BodyPart.ARM_R else BodyPart.ARM_R
        
        if punch_type == Action.JAB:
            hand_used = off_hand
        elif punch_type == Action.HOOK:
            hand_used = attacker.dominant_hand
        else:
            # Auto-select for generic PUNCH (Duels)
            # If weapon drawn, MUST use off-hand
            if attacker.weapon_state == WeaponState.DRAWN:
                hand_used = off_hand
            else:
                # Prefer dominant if free
                hand_used = attacker.dominant_hand

        # Check if Hand is Free/Usable
        if attacker.weapon_state == WeaponState.DRAWN and hand_used == attacker.dominant_hand:
             return "Cannot punch with gun hand!"
             
        if attacker.body_parts[hand_used] <= 0:
            return f"Cannot punch with broken {hand_used.value}!"

        dist = self.get_distance()
        if dist > 2:
            return "Too far to punch!"
            
        # Stats based on Punch Type
        acc_mod = 0
        dmg_mod = 0
        
        if punch_type == Action.JAB:
            acc_mod = 15 # Accurate
            dmg_mod = -3 # Weak
        elif punch_type == Action.HOOK:
            acc_mod = -10 # Wild
            dmg_mod = 5 # Strong
            
        # Hit chance modified by Atk vs Def
        hit_chance = 60 + (attacker.luck - 50)/2 + (attacker.brawl_atk - defender.brawl_def) + acc_mod
        
        if random.randint(0, 100) < hit_chance:
            # Damage Calculation
            base_dmg = random.randint(8, 15)
            dmg_bonus = max(0, attacker.brawl_atk - defender.brawl_def)
            total_dmg = base_dmg + dmg_bonus + dmg_mod
            
            defender.hp -= total_dmg
            msg = f"{attacker.name} {punch_type.value}s {defender.name} for {total_dmg} HP!"
            
            # Self-Injury (Broken Hand)
            if random.random() < 0.02: # 2% chance
                attacker.body_parts[hand_used] = 0
                hand_str = "R" if hand_used == BodyPart.ARM_R else "L"
                attacker.injuries.append(f"Broken Hand ({hand_str})")
                msg += f" {attacker.name} broke their hand on impact!"

            # Critical Effects (Blind/Bleed)
            if random.random() < 0.05: # 5% chance
                effect_roll = random.random()
                if effect_roll < 0.5:
                    defender.blinded += 1
                    msg += " A cheap shot to the eye!"
                else:
                    defender.blood -= 1
                    msg += " Nose broken! Bleeding."

            # Disarm Check
            if defender.weapon_state == WeaponState.DRAWN and random.random() < 0.3:
                 defender.weapon_state = WeaponState.DROPPED
                 msg += " DISARMED!"

            # Death/KO Check
            # Instant Death: > 30% MaxHP
            if total_dmg > (defender.max_hp * 0.30):
                defender.alive = False
                msg += " INSTANT DEATH! Skull fractured!"
            # Instant KO: > 20% MaxHP
            elif total_dmg > (defender.max_hp * 0.20):
                defender.conscious = False
                msg += " KNOCKED OUT COLD!"
            # Regular KO: HP < 20% MaxHP
            elif defender.hp < (defender.max_hp * 0.20):
                defender.conscious = False
                msg += " KNOCKED OUT!"
            
            return msg
        else:
            return f"{attacker.name} swings and misses!"

    def execute_action(self, actor, action, target):
        msgs = []
        
        # Status Checks
        if not actor.conscious or not actor.alive:
            return []
            
        # Reset temp states
        actor.is_jumping = False
        
        # Movement
        if action == Action.PACE:
            # Move away from center
            if actor.position == 0:
                actor.position += actor.direction_multiplier
            elif actor.position > 0:
                actor.position += 1
            else:
                actor.position -= 1
            msgs.append(f"{actor.name} paces. Pos: {actor.position}")
            
        elif action == Action.FLEE:
            if abs(actor.position) >= 13:
                # Check distance from opponent
                if self.get_distance() >= 13:
                    msgs.append(f"{actor.name} flees into the sunset!")
                    # End game logic handled in loop
                else:
                    msgs.append(f"{actor.name} tries to flee but is too close to opponent!")
            else:
                # Move 2 spaces away
                move = 2
                if actor.position >= 0: actor.position += move
                else: actor.position -= move
                msgs.append(f"{actor.name} flees! Pos: {actor.position}")

        elif action == Action.TURN:
            if actor.orientation == Orientation.FACING_AWAY:
                actor.orientation = Orientation.FACING_OPPONENT
            else:
                actor.orientation = Orientation.FACING_AWAY
            msgs.append(f"{actor.name} turns to {actor.orientation.value}.")

        elif action == Action.DRAW:
            if actor.weapon_state == WeaponState.HOLSTERED:
                actor.weapon_state = WeaponState.DRAWN
                msgs.append(f"{actor.name} draws weapon!")
            else:
                msgs.append(f"{actor.name} fumbles for a weapon they don't have holstered.")

        elif action == Action.PICK_UP:
            if actor.weapon_state == WeaponState.DROPPED:
                actor.weapon_state = WeaponState.DRAWN
                msgs.append(f"{actor.name} picks up their weapon from the dust.")
            else:
                msgs.append(f"{actor.name} grasps at the ground for nothing.")

        elif action == Action.SHOOT_HIGH or action == Action.SHOOT_CENTER or action == Action.SHOOT_LOW:
            if actor.ammo > 0:
                actor.ammo -= 1
                part, blood_loss, msg = self.calculate_hit(actor, target, action)
                msgs.append(f"{actor.name} fires: {msg}")
                if part != BodyPart.MISS:
                    target.blood -= blood_loss
            else:
                msgs.append(f"{actor.name} pulls trigger on empty chamber!")

        elif action == Action.RELOAD:
            if actor.ammo < 6:
                actor.ammo += 1
                msgs.append(f"{actor.name} loads a round.")

        elif action == Action.DUCK:
            actor.is_ducking = True
            msgs.append(f"{actor.name} ducks.")
            
        elif action == Action.STAND:
            actor.is_ducking = False
            msgs.append(f"{actor.name} stands.")

        elif action == Action.DUCK_FIRE:
            actor.is_ducking = True
            if actor.ammo > 0:
                actor.ammo -= 1
                part, blood_loss, msg = self.calculate_hit(actor, target, Action.SHOOT_CENTER, accuracy_penalty=20)
                msgs.append(f"{actor.name} ducks and fires: {msg}")
                if part != BodyPart.MISS:
                    target.blood -= blood_loss
            else:
                msgs.append(f"{actor.name} ducks but clicks on empty!")

        elif action == Action.STAND_FIRE:
            actor.is_ducking = False
            if actor.ammo > 0:
                actor.ammo -= 1
                part, blood_loss, msg = self.calculate_hit(actor, target, Action.SHOOT_CENTER, accuracy_penalty=20)
                msgs.append(f"{actor.name} rises and fires: {msg}")
                if part != BodyPart.MISS:
                    target.blood -= blood_loss
            else:
                msgs.append(f"{actor.name} rises but clicks on empty!")

        elif action == Action.JUMP:
            actor.is_jumping = True
            msgs.append(f"{actor.name} jumps!")

        elif action == Action.KICK_SAND:
            dist = self.get_distance()
            if actor.orientation != Orientation.FACING_OPPONENT:
                msgs.append(f"{actor.name} tries to kick sand but isn't facing their target!")
            elif dist > 3:
                msgs.append(f"{actor.name} kicks dust at nothing. Too far away!")
            elif target.orientation != Orientation.FACING_OPPONENT:
                msgs.append(f"{actor.name} kicks sand at {target.name}'s back. It is ineffective.")
            else:
                # Success chance (Base 35% + Luck mod)
                chance = 35 + (actor.luck - 50) / 2
                if random.randint(0, 100) < chance:
                    turns = random.randint(1, 3)
                    target.temp_blind_turns += turns
                    msgs.append(f"{actor.name} kicks sand into {target.name}'s eyes! Blinded for {turns} turns!")
                else:
                    msgs.append(f"{actor.name} kicks sand but {target.name} looks away in time!")

        elif action == Action.TAKE_COVER:
            if actor.has_horse and abs(actor.position) >= 13:
                actor.behind_cover = True
                msgs.append(f"{actor.name} takes cover behind horse.")
            else:
                msgs.append(f"{actor.name} has no cover here.")

        elif action == Action.PUNCH:
            res = self.resolve_punch(actor, target, Action.PUNCH)
            msgs.append(res)

        elif action == Action.JAB:
            res = self.resolve_punch(actor, target, Action.JAB)
            msgs.append(res)

        elif action == Action.HOOK:
            res = self.resolve_punch(actor, target, Action.HOOK)
            msgs.append(res)

        elif action == Action.SURRENDER:
            actor.is_surrendering = True
            actor.weapon_state = WeaponState.HOLSTERED # Put gun away to show intent
            msgs.append(f"{actor.name} raises their hands! 'I YIELD!'")

        elif action == Action.STEP_IN:
            # Move toward center
            if actor.position > 0:
                actor.position -= 1
            elif actor.position < 0:
                actor.position += 1
            # If at 0, cross over? Or stay? Let's stay at 0 for now (melee range)
            msgs.append(f"{actor.name} steps in. Pos: {actor.position}")
        
        return msgs

    def run_turn(self, a1, a2):
        self.turn += 1
        self.log.append(f"\n--- TURN {self.turn} ---")
        
        # Simultaneous Execution
        # We calculate results based on state at START of turn, but apply them.
        # Actually, some actions might interrupt others?
        # For MVP, let's just execute P1 then P2, but check survival.
        
        msgs1 = self.execute_action(self.p1, a1, self.p2)
        msgs2 = self.execute_action(self.p2, a2, self.p1)
        
        self.log.extend(msgs1)
        self.log.extend(msgs2)
        
        # End of Turn Effects
        for p in [self.p1, self.p2]:
            if p.alive:
                # Temporary Blindness Recovery
                if p.temp_blind_turns > 0:
                    p.temp_blind_turns -= 1
                    if p.temp_blind_turns == 0:
                        self.log.append(f"{p.name} blinks the sand out of their eyes.")

                # Bleeding
                if p.bleeding_rate > 0:
                    p.blood -= p.bleeding_rate
                    self.log.append(f"{p.name} bleeds (-{p.bleeding_rate}). Blood: {p.blood}")
                
                # Fainting
                if p.blood <= 4 and p.conscious:
                    if random.random() < 0.3: # Chance to faint
                        p.conscious = False
                        self.log.append(f"{p.name} faints from blood loss!")
                
                # Death
                if p.blood <= 0:
                    p.alive = False
                    self.log.append(f"{p.name} has died.")
                    
        # AI Surrender Logic (Decide to surrender for NEXT turn)
        if self.p2.alive and self.p2.conscious and not self.p2.player_state and not self.p2.is_surrendering:
            # If HP low or Disarmed
            should_surrender = False
            if self.p2.hp < self.p2.max_hp * 0.2: should_surrender = True
            if self.p2.weapon_state == WeaponState.DROPPED and self.p1.weapon_state == WeaponState.DRAWN: should_surrender = True
            
            if should_surrender:
                # Check Bravery/Traits? For now, 50% chance
                if random.random() < 0.5:
                    # They will choose SURRENDER action next turn
                    # We can't force the action here, but we can set a flag for the AI function to read?
                    # Or just let the AI function handle it.
                    pass

    def print_log(self):
        for l in self.log:
            print(l)
        self.log = []

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "="*60)
        print(f"TURN {self.turn}")
        print("="*60 + "\n")
        
        # Arena Visualization
        # Range -15 to +15 (31 chars)
        arena = [" . "] * 31
        center = 15
        
        # Draw Static Elements
        arena[center] = " | "
        arena[center - 13] = " H "
        arena[center + 13] = " H "
        
        # Draw Players
        p1_idx = center + self.p1.position
        p2_idx = center + self.p2.position
        
        # P1 Symbol
        p1_sym = "1"
        if self.p1.orientation == Orientation.FACING_OPPONENT: p1_sym = "1>" if self.p1.direction_multiplier == 1 else "<1" # Wait, P1 is -1 (Left) so facing opp (Right) is >
        else: p1_sym = "<1" if self.p1.direction_multiplier == 1 else "1>" # Facing away
        
        # Fix P1 Orientation Visuals (P1 is Left/-1, P2 is Right/+1)
        # If P1 faces Opponent (Right), he looks >
        # If P1 faces Away (Left), he looks <
        if self.p1.direction_multiplier == -1:
            p1_sym = "1>" if self.p1.orientation == Orientation.FACING_OPPONENT else "<1"
        else:
            p1_sym = "<1" if self.p1.orientation == Orientation.FACING_OPPONENT else "1>"

        if self.p1.is_ducking: p1_sym = p1_sym.replace("1", "1_")
        if self.p1.is_jumping: p1_sym = p1_sym.replace("1", "^1")
        if not self.p1.conscious: p1_sym = "_1_"
        
        # P2 Symbol
        if self.p2.direction_multiplier == 1: # Right side
            p2_sym = "<2" if self.p2.orientation == Orientation.FACING_OPPONENT else "2>"
        else:
            p2_sym = "2>" if self.p2.orientation == Orientation.FACING_OPPONENT else "<2"

        if self.p2.is_ducking: p2_sym = p2_sym.replace("2", "2_")
        if self.p2.is_jumping: p2_sym = p2_sym.replace("2", "^2")
        if not self.p2.conscious: p2_sym = "_2_"

        # Place on Grid
        if 0 <= p1_idx < 31: arena[p1_idx] = f"{p1_sym:^3}"
        if 0 <= p2_idx < 31: 
            if p1_idx == p2_idx:
                arena[p2_idx] = " X " # Collision/Melee
            else:
                arena[p2_idx] = f"{p2_sym:^3}"
                
        print("".join(arena))
        print(" " * (center*3) + "^ (0)")
        
        # Print Stats
        print("\n" + "-"*60)
        print(f"{self.p1.name:<30} | {self.p2.name:<30}")
        print(f"HP: {self.p1.hp:<3}/{self.p1.max_hp:<3} Blood: {self.p1.blood:<2}      | HP: {self.p2.hp:<3}/{self.p2.max_hp:<3} Blood: {self.p2.blood:<2}")
        print(f"Wpn: {self.p1.weapon_state.value:<10} Ammo: {self.p1.ammo}      | Wpn: {self.p2.weapon_state.value:<10} Ammo: {self.p2.ammo}")
        print("-" * 60)
        
        # Print Log
        self.print_log()

# --- SIMULATION SCENARIOS ---

def run_simulation(scenario_name, p1_ai, p2_ai):
    print(f"\n\n>>> SIMULATION: {scenario_name} <<<")
    input("Press Enter to start...")
    engine = DuelEngineV2()
    
    # Run for max 20 turns
    for i in range(20):
        if not engine.p1.alive or not engine.p2.alive:
            break
        # if not engine.p1.conscious and not engine.p2.conscious:
        #    break 
        # Keep running even if unconscious to see if they get beaten up (as per user request)
            
        # Get actions from AI functions
        # If AI is a list, use index. If function, call it.
        if isinstance(p1_ai, list):
            a1 = p1_ai[i % len(p1_ai)]
        else:
            a1 = p1_ai(engine.p1, engine.p2, engine)
            
        if isinstance(p2_ai, list):
            a2 = p2_ai[i % len(p2_ai)]
        else:
            a2 = p2_ai(engine.p2, engine.p1, engine)
        
        # Override for unconscious
        if not engine.p1.conscious: a1 = Action.WAIT
        if not engine.p2.conscious: a2 = Action.WAIT
        
        engine.run_turn(a1, a2)
        engine.render()
        time.sleep(1.5)
        
    print("\nSIMULATION ENDED")

# AI Behaviors
def ai_honorable(me, opp, engine):
    # Check if opponent is surrendering
    if opp.is_surrendering:
        return Action.WAIT

    # Self Preservation (Surrender?)
    if me.hp < me.max_hp * 0.2 or (me.weapon_state == WeaponState.DROPPED and opp.weapon_state == WeaponState.DRAWN):
        if random.random() < 0.7: # Honorable people know when they are beat
            return Action.SURRENDER

    # Pace to 10, Turn, Draw, Shoot
    if abs(me.position) < 10:
        return Action.PACE
    if me.orientation != Orientation.FACING_OPPONENT:
        return Action.TURN
    if me.weapon_state == WeaponState.HOLSTERED:
        return Action.DRAW
    return Action.SHOOT_CENTER

def ai_cheater(me, opp, engine):
    # Cheaters might shoot surrendering opponents!
    if opp.is_surrendering:
        if random.random() < 0.5:
            return Action.SHOOT_CENTER # Cheap shot!
        return Action.WAIT

    # Self Preservation
    if me.hp < me.max_hp * 0.15:
        if random.random() < 0.3: # Cheaters are stubborn or cowardly?
            return Action.SURRENDER

    # Turn immediately, Draw, Shoot
    if me.orientation != Orientation.FACING_OPPONENT:
        return Action.TURN
    if me.weapon_state == WeaponState.HOLSTERED:
        return Action.DRAW
    if me.ammo > 0:
        return Action.SHOOT_CENTER
    return Action.RELOAD

def ai_brawler(me, opp, engine):
    if opp.is_surrendering:
        return Action.WAIT

    # Turn immediately, Punch
    if me.orientation != Orientation.FACING_OPPONENT:
        return Action.TURN
    
    # If opponent is close, punch
    if engine.get_distance() <= 2:
        return Action.PUNCH
        
    # If opponent is far... we can't move closer? 
    # Just taunt/wait?
    return Action.WAIT

if __name__ == "__main__":
    # run_simulation("HONORABLE DUEL", ai_honorable, ai_honorable)
    # run_simulation("CHEATER VS HONORABLE", ai_cheater, ai_honorable)
    run_simulation("POINT BLANK: BRAWLER VS GUNMAN", ai_brawler, ai_cheater)

