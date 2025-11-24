import os
import sys

# Configuration
SCREEN_WIDTH = 80

class Actor:
    def __init__(self, name, sprite_base, x, y, state="idle", facing_left=False, scars=None, archetype=None):
        self.name = name
        self.x = x
        self.y = y
        # Stub for compatibility

class SceneRenderer:
    def __init__(self):
        self.window = None # Stub for compatibility

    def init_window(self):
        pass # No-op

    def load_scene(self, scene_name):
        # Optional: Print a scene header
        # print(f"\n[ENTERING SCENE: {scene_name.upper()}]")
        pass

    def add_actor(self, actor):
        pass # No-op

    def clear_actors(self):
        pass # No-op

    def get_input(self):
        """Capture input from the terminal"""
        try:
            choice = input(">> ").strip().upper()
            return choice
        except EOFError:
            return "Q"

    def get_text_input(self, prompt="Enter text:", player=None):
        """Capture string input from the user"""
        print(f"\n{prompt}")
        try:
            return input(">> ").strip()
        except EOFError:
            return ""

    def _get_sprite_char(self, combatant):
        """Get single-line sprite for hybrid visualization"""
        # Check alive/conscious
        if not combatant.alive:
            return "[✕_✕]"
        if not combatant.conscious:
            return "[_zZ]"
            
        # Check Surrender
        if getattr(combatant, 'is_surrendering', False):
            return "[\\o/]"
            
        # Check Stance
        if getattr(combatant, 'is_jumping', False):
            return "[^@^]"
        if getattr(combatant, 'is_ducking', False):
            return "[_@_]"
        if getattr(combatant, 'behind_cover', False):
            return "[█@█]"
            
        # Check Weapon State
        ws = combatant.weapon_state
        ws_val = ws.value if hasattr(ws, 'value') else str(ws)
        
        orient = combatant.orientation
        orient_val = orient.value if hasattr(orient, 'value') else str(orient)
        
        # Determine Facing Direction arrow
        # P1 is usually left (-1), P2 is right (1)
        is_p1 = (combatant.direction_multiplier == -1)
        facing_opp = (orient_val == "facing opponent")
        
        if is_p1:
            arrow = "→" if facing_opp else "←"
        else:
            arrow = "←" if facing_opp else "→"
            
        if ws_val == "holstered":
            return f"[{arrow}@-]"
        elif ws_val == "drawn":
            return f"[{arrow}@═]"
        elif ws_val == "dropped":
            return "[@_~]"
            
        return "[@]"

    def render_duel_state(self, engine, p1, p2):
        """Render the duel/brawl state using the Hybrid ASCII Dashboard"""
        
        # Distance visualization
        distance = abs(p1.position - p2.position)
        dist_visual = "═" * distance
        if distance == 0: dist_visual = "⚔" # Crossed swords for melee
        
        p1_sprite = self._get_sprite_char(p1)
        p2_sprite = self._get_sprite_char(p2)
        
        print("\n" + "╔" + "═"*78 + "╗")
        print("║" + " "*30 + "STANDOFF" + " "*40 + "║")
        print("╠" + "═"*78 + "╣")
        
        # Scene Line
        scene_content = f"{p1_sprite} {dist_visual} {p2_sprite}"
        padding = (78 - len(scene_content)) // 2
        print("║" + " "*padding + scene_content + " "*(78 - len(scene_content) - padding) + "║")
        
        # Distance Text
        dist_text = f"[{distance} PACES]"
        padding_d = (78 - len(dist_text)) // 2
        print("║" + " "*padding_d + dist_text + " "*(78 - len(dist_text) - padding_d) + "║")
        
        print("╠" + "═"*78 + "╣")
        
        # Stats Helper
        def stat_bar(current, maximum, symbol="█", length=10):
            if maximum <= 0: maximum = 1
            ratio = max(0, min(1, current / maximum))
            filled = int(ratio * length)
            empty = length - filled
            return symbol * filled + "░" * empty

        # Prepare Data
        p1_hp_bar = stat_bar(p1.hp, p1.max_hp, '█')
        p1_blood_bar = stat_bar(p1.blood, p1.max_blood, '●')
        p1_ammo_bar = stat_bar(p1.ammo, 6, '■', 6)
        p1_ws = p1.weapon_state.value.upper() if hasattr(p1.weapon_state, 'value') else str(p1.weapon_state).upper()
        p1_stance = "DUCKING" if p1.is_ducking else "STANDING"
        
        p2_hp_bar = stat_bar(p2.hp, p2.max_hp, '█')
        p2_blood_bar = stat_bar(p2.blood, p2.max_blood, '●')
        p2_ammo_bar = stat_bar(p2.ammo, 6, '■', 6)
        p2_ws = p2.weapon_state.value.upper() if hasattr(p2.weapon_state, 'value') else str(p2.weapon_state).upper()
        p2_stance = "DUCKING" if p2.is_ducking else "STANDING"

        # Columns
        lines = []
        lines.append(f"║ {p1.name[:25]:<37}│ {p2.name[:25]:<38}║")
        lines.append(f"║ HP:    {p1_hp_bar} ({p1.hp:3}/{p1.max_hp:<3})   │ HP:    {p2_hp_bar} ({p2.hp:3}/{p2.max_hp:<3})    ║")
        lines.append(f"║ Blood: {p1_blood_bar} ({p1.blood:2}/{p1.max_blood:<2})     │ Blood: {p2_blood_bar} ({p2.blood:2}/{p2.max_blood:<2})      ║")
        lines.append(f"║ Ammo:  {p1_ammo_bar} ({p1.ammo}/6)         │ Ammo:  {p2_ammo_bar} ({p2.ammo}/6)           ║")
        lines.append(f"║ Wpn:   {p1_ws:<28}│ Wpn:   {p2_ws:<29}║")
        lines.append(f"║ Stance:{p1_stance:<28}│ Stance:{p2_stance:<29}║")
        
        for line in lines:
            print(line)
            
        # Injuries Section
        if p1.injuries or p2.injuries:
            print("╠" + "═"*38 + "╦" + "═"*39 + "╣")
            print(f"║ INJURIES:{' '*28}┃ INJURIES:{' '*29}║")
            
            max_inj = max(len(p1.injuries), len(p2.injuries))
            for i in range(max_inj):
                i1 = p1.injuries[i] if i < len(p1.injuries) else ""
                i2 = p2.injuries[i] if i < len(p2.injuries) else ""
                print(f"║ • {i1[:33]:<33}┃ • {i2[:33]:<34}║")

        print("╚" + "═"*78 + "╝")

    def render(self, stats_text=None, log_text=None, buttons=None, player=None, world=None):
        """Render text output to terminal"""
        
        if stats_text:
            print("\n" + "─"*80)
            print(" STATS")
            print("─"*80)
            for line in stats_text:
                print(line)

        if log_text:
            print("\n" + "─"*80)
            print(" LOG")
            print("─"*80)
            for line in log_text:
                print(f" > {line}")
        
        if buttons:
            print("\n" + "─"*80)
            print(" ACTIONS")
            print("─"*80)
            
            row = ""
            for btn in buttons:
                key = btn.get('key', '?')
                label = btn.get('label', 'Action')
                item = f"[{key}] {label}"
                
                if len(row) + len(item) + 4 > 80:
                    print(row)
                    row = ""
                
                row += f"{item:<25}"
            
            if row:
                print(row)
            print("─"*80)

# Global Renderer Instance
renderer = SceneRenderer()

