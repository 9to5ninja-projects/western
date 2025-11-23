import os
import threading
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Configuration
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
SCENE_WIDTH = 640
SCENE_HEIGHT = 380
ASSET_DIR = "assets"

class Actor:
    def __init__(self, name, sprite_base, x, y, state="idle", facing_left=False):
        self.name = name
        self.sprite_base = sprite_base # Folder name in assets/sprites/
        self.x = x
        self.y = y
        self.state = state
        self.facing_left = facing_left

class GameWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Western Legend")
        self.root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        self.root.resizable(True, True) # Allow resizing
        self.root.state('zoomed') # Maximize window
        
        self.label = tk.Label(self.root)
        self.label.pack(fill=tk.BOTH, expand=True)
        
        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_image(self, pil_image):
        if not self.running: return
        
        # Force update of pending geometry changes
        self.root.update_idletasks()
        
        # Get current window size
        win_w = self.root.winfo_width()
        win_h = self.root.winfo_height()
        
        # Fallback if window size is not yet reported correctly
        if win_w <= 1: win_w = self.root.winfo_screenwidth()
        if win_h <= 1: win_h = self.root.winfo_screenheight()
        
        # Only resize if window is ready and different from default
        if win_w > 1 and win_h > 1:
             # Resize image to fit window (maintain aspect ratio or fill?)
             # For now, let's fill to keep it simple, or maybe fit width
             pil_image = pil_image.resize((win_w, win_h), Image.Resampling.LANCZOS)

        # Convert PIL image to ImageTk
        self.tk_image = ImageTk.PhotoImage(pil_image)
        self.label.config(image=self.tk_image)
        self.root.update()

    def on_close(self):
        self.running = False
        self.root.destroy()

class SceneRenderer:
    def __init__(self):
        self.actors = []
        self.background = None
        self.ui_overlay = None
        self.font = self._load_font()
        self.window = None # Lazy init
        
    def _load_font(self):
        # Try to load a default font, fallback to default
        try:
            return ImageFont.truetype("arial.ttf", 16)
        except IOError:
            return ImageFont.load_default()

    def init_window(self):
        if not self.window or not self.window.running:
            self.window = GameWindow()
            # Bind Key Events
            self.window.root.bind("<Key>", self._on_key)
            
    def _on_key(self, event):
        # Store the key press
        # print(f"DEBUG: Key pressed: {event.keysym} char: {repr(event.char)}")
        
        if event.char and event.char.isprintable():
            self.last_key = event.char.upper() # Force upper case for consistency
        
        # Handle special keys
        if event.keysym in ["Return", "KP_Enter"]: self.last_key = "ENTER"
        if event.keysym == "Escape": self.last_key = "ESC"
        if event.keysym == "BackSpace": self.last_key = "BACKSPACE"
        if event.keysym == "space": self.last_key = "SPACE" # Explicit space
        
        # print(f"DEBUG: Resolved to: {self.last_key}")

    def get_input(self):
        """Blocking call to wait for a key press from the window"""
        self.last_key = None
        # Wait loop
        while self.last_key is None:
            if self.window and not self.window.running:
                return "Q" # Exit if window closed
            if self.window:
                self.window.root.update()
            import time
            time.sleep(0.05)
        
        return self.last_key

    def get_text_input(self, prompt="Enter text:"):
        """Capture string input from the user"""
        current_text = ""
        while True:
            # Render current state
            self.render(log_text=[prompt, f"> {current_text}_"])
            
            key = self.get_input()
            
            if key == "ENTER":
                return current_text
            elif key == "BACKSPACE":
                current_text = current_text[:-1]
            elif key == "ESC":
                return ""
            elif len(key) == 1:
                current_text += key

    def load_scene(self, scene_name):
        """Load a background image from assets/scenes/"""
        path = os.path.join(ASSET_DIR, "scenes", f"{scene_name}.png")
        if os.path.exists(path):
            self.background = Image.open(path).convert("RGBA")
            self.background = self.background.resize((SCENE_WIDTH, SCENE_HEIGHT))
        else:
            # Create placeholder background
            self.background = Image.new("RGBA", (SCENE_WIDTH, SCENE_HEIGHT), (50, 50, 50, 255))
            draw = ImageDraw.Draw(self.background)
            draw.text((10, 10), f"Scene: {scene_name} (Missing Asset)", fill="white", font=self.font)

    def add_actor(self, actor):
        self.actors.append(actor)

    def clear_actors(self):
        self.actors = []

    def _get_sprite(self, actor):
        """Load sprite based on actor state and direction"""
        direction = "left" if actor.facing_left else "right"
        filename = f"{actor.state}_{direction}.png"
        path = os.path.join(ASSET_DIR, "sprites", actor.sprite_base, filename)
        
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        else:
            # Placeholder sprite
            img = Image.new("RGBA", (50, 100), (255, 0, 0, 255))
            draw = ImageDraw.Draw(img)
            draw.text((5, 40), actor.name[:4], fill="white", font=self.font)
            return img

    def render(self, stats_text=None, log_text=None, buttons=None, player=None, world=None):
        """Composite the final frame"""
        # 1. Create Base Canvas
        canvas = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), (20, 20, 20))
        
        # 2. Draw Background
        if self.background:
            canvas.paste(self.background, (0, 0), self.background)
            
        # 3. Draw Actors (Sorted by Y for simple depth)
        sorted_actors = sorted(self.actors, key=lambda a: a.y)
        for actor in sorted_actors:
            sprite = self._get_sprite(actor)
            # Center sprite on x, y is bottom
            w, h = sprite.size
            pos_x = int(actor.x - w/2)
            pos_y = int(actor.y - h)
            
            # Ensure sprite is within bounds (roughly)
            if pos_x < -50 or pos_x > SCENE_WIDTH + 50: continue
            
            canvas.paste(sprite, (pos_x, pos_y), sprite)

        # 4. Draw UI Layout (Mockup style)
        draw = ImageDraw.Draw(canvas)
        
        # Sidebar (Stats)
        draw.rectangle([SCENE_WIDTH + 10, 10, SCREEN_WIDTH - 10, SCENE_HEIGHT], outline="white")
        draw.text((SCENE_WIDTH + 20, 20), "STATS", fill="yellow", font=self.font)
        
        if player:
            # Detailed Player Stats
            x = SCENE_WIDTH + 20
            y = 50
            line_height = 20
            
            # Name & Cash
            draw.text((x, y), f"NAME: {player.name}", fill="white", font=self.font)
            y += line_height
            draw.text((x, y), f"CASH: ${player.cash:.2f}", fill="lightgreen", font=self.font)
            y += line_height + 5
            
            # Honor & Bounty
            honor_str = "Neutral"
            if player.honor > 20: honor_str = "Honorable"
            if player.honor < -20: honor_str = "Outlaw"
            draw.text((x, y), f"HONOR: {player.honor} ({honor_str})", fill="white", font=self.font)
            y += line_height
            draw.text((x, y), f"BOUNTY: ${player.bounty:.2f}", fill="red", font=self.font)
            y += line_height + 5
            
            # HP & Blood
            draw.text((x, y), f"HP: {player.hp}/{player.max_hp}", fill="white", font=self.font)
            y += line_height
            blood_str = "O" * player.blood
            draw.text((x, y), f"BLOOD: {blood_str}", fill="red", font=self.font)
            y += line_height + 5
            
            # Stats
            draw.text((x, y), f"ACC: {player.get_acc()} SPD: {player.get_spd()} CHM: {player.charm}", fill="cyan", font=self.font)
            y += line_height
            draw.text((x, y), f"BRAWL: {player.brawl_atk}/{player.brawl_def}", fill="cyan", font=self.font)
            y += line_height + 5
            
            # Equip
            wpn = player.equipped_weapon.name if player.equipped_weapon else "None"
            draw.text((x, y), f"WPN: {wpn}", fill="white", font=self.font)
            y += line_height
            draw.text((x, y), f"AMMO: {player.ammo}", fill="white", font=self.font)
            y += line_height
            
            horse = player.horse.name if player.horse else "None"
            draw.text((x, y), f"HORSE: {horse}", fill="white", font=self.font)
            y += line_height
            
            hat = player.hat.name if player.hat else "None"
            draw.text((x, y), f"HAT: {hat}", fill="white", font=self.font)
            y += line_height
            
            draw.text((x, y), f"RENT: {player.weeks_rent_paid} wks", fill="white", font=self.font)
            y += line_height + 5
            
            # Injuries
            if player.injuries:
                draw.text((x, y), "INJURIES:", fill="red", font=self.font)
                y += line_height
                for inj in player.injuries[:3]: # Limit to 3
                    draw.text((x, y), f"- {inj}", fill="red", font=self.font)
                    y += line_height
            else:
                draw.text((x, y), "No Injuries", fill="green", font=self.font)

        elif stats_text:
            y_off = 50
            for line in stats_text:
                draw.text((SCENE_WIDTH + 20, y_off), line, fill="white", font=self.font)
                y_off += 20

        # Bottom Panel (Log & Town Info)
        log_x = 20
        log_width = SCENE_WIDTH - 20
        
        if world:
            # Split Bottom Panel: Left for Town Info, Right for Log
            town_info_width = 250
            
            # Draw Town Info Box
            draw.rectangle([10, SCENE_HEIGHT + 10, 10 + town_info_width, SCREEN_HEIGHT - 10], outline="white")
            draw.text((20, SCENE_HEIGHT + 20), "TOWN INFO", fill="yellow", font=self.font)
            
            town = world.get_town()
            if town:
                ty = SCENE_HEIGHT + 50
                draw.text((20, ty), f"{town.name.upper()}", fill="white", font=self.font)
                ty += 20
                
                heat = getattr(town, "heat", 0)
                draw.text((20, ty), f"Heat: {heat}/100", fill="red" if heat > 50 else "green", font=self.font)
                ty += 20
                
                law = getattr(town, "lawfulness", "??")
                draw.text((20, ty), f"Law: {law}", fill="cyan", font=self.font)
                ty += 20
                
                mayor = getattr(town, "mayor", None)
                mayor_name = mayor.name if mayor else "None"
                mayor_status = getattr(town, "mayor_status", "Unknown")
                draw.text((20, ty), f"Mayor: {mayor_name}", fill="white", font=self.font)
                ty += 20
                draw.text((20, ty), f"Status: {mayor_status}", fill="gray", font=self.font)
                ty += 20
                
                sheriff = getattr(town, "sheriff", None)
                sheriff_name = sheriff.name if sheriff else "None"
                draw.text((20, ty), f"Sheriff: {sheriff_name}", fill="white", font=self.font)
                ty += 20
                
                traits = ", ".join(town.traits[:2])
                draw.text((20, ty), f"Traits: {traits}", fill="gray", font=self.font)

            # Adjust Log Area
            log_x = 10 + town_info_width + 10
            log_width = SCENE_WIDTH - log_x
            
            draw.rectangle([log_x - 5, SCENE_HEIGHT + 10, SCENE_WIDTH, SCREEN_HEIGHT - 10], outline="white")
        else:
            # Full width Log
            draw.rectangle([10, SCENE_HEIGHT + 10, SCENE_WIDTH, SCREEN_HEIGHT - 10], fill=(20, 20, 20), outline="white")

        draw.text((log_x, SCENE_HEIGHT + 20), "LOG", fill="yellow", font=self.font)
        if log_text:
            y_off = SCENE_HEIGHT + 50
            # Show last 8 lines
            for line in log_text[-8:]:
                # Simple truncation to prevent overflow
                max_chars = int(log_width / 8) # Approx char width
                if len(line) > max_chars: line = line[:max_chars-3] + "..."
                draw.text((log_x, y_off), line, fill="white", font=self.font)
                y_off += 20

        # Bottom Right (Buttons)
        # Area: x=650 to 790, y=390 to 590
        if buttons:
            btn_x = SCENE_WIDTH + 10
            btn_y = SCENE_HEIGHT + 10
            btn_w = SCREEN_WIDTH - btn_x - 10
            btn_h = SCREEN_HEIGHT - btn_y - 10
            
            draw.rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], outline="white")
            draw.text((btn_x + 10, btn_y + 10), "ACTIONS", fill="yellow", font=self.font)
            
            # 2-Column Layout
            col_w = (btn_w - 15) / 2
            start_y = btn_y + 40
            
            for i, btn in enumerate(buttons):
                col = i % 2
                row = i // 2
                
                bx = btn_x + 5 + (col * (col_w + 5))
                by = start_y + (row * 30)
                
                # Check bounds
                if by + 25 > btn_y + btn_h: break 
                
                label = f"[{btn.get('key', '?')}] {btn.get('label', 'Action')}"
                # Truncate label if too long for column
                if len(label) > 18: label = label[:16] + ".."
                
                draw.rectangle([bx, by, bx + col_w, by + 25], fill=(50, 50, 50), outline="white")
                draw.text((bx + 5, by + 5), label, fill="white", font=self.font)

        # Update Window if it exists
        if self.window:
            self.window.update_image(canvas)

        return canvas

    def show(self):
        """Debug method to show the current frame"""
        img = self.render()
        img.show()

    def render_duel_state(self, engine, p1, p2):
        """Render the duel/brawl state using the visualizer"""
        # 1. Clear Actors
        self.clear_actors()
        
        # 2. Add Combatants
        # Map engine position (-15 to 15) to screen coordinates
        # Center is SCENE_WIDTH / 2
        center_x = SCENE_WIDTH // 2
        scale_x = 15 # Pixels per unit
        
        # Ensure positions are within reasonable bounds for display
        # If distance is very small (brawl), separate them visually
        dist = abs(p1.position - p2.position)
        if dist < 2:
            # Force visual separation for brawl
            p1_x = center_x - 40
            p2_x = center_x + 40
        else:
            p1_x = center_x + (p1.position * scale_x)
            p2_x = center_x + (p2.position * scale_x)
        
        # Determine Sprites
        p1_state = "idle"
        if p1.weapon_state == "drawn": p1_state = "aiming"
        if p1.is_ducking: p1_state = "ducking"
        if not p1.conscious: p1_state = "dead"
        
        p2_state = "idle"
        if p2.weapon_state == "drawn": p2_state = "aiming"
        if p2.is_ducking: p2_state = "ducking"
        if not p2.conscious: p2_state = "dead"
        
        # Facing
        p1_facing_left = (p1.orientation.value == "facing away" and p1.direction_multiplier == -1) or \
                         (p1.orientation.value == "facing opponent" and p1.direction_multiplier == 1)
                         
        p2_facing_left = (p2.orientation.value == "facing opponent" and p2.direction_multiplier == 1) or \
                         (p2.orientation.value == "facing away" and p2.direction_multiplier == -1)

        # Add Actors
        self.add_actor(Actor(p1.name, "cowboy_male", p1_x, 300, p1_state, p1_facing_left))
        self.add_actor(Actor(p2.name, "bandit_male", p2_x, 300, p2_state, p2_facing_left))
        
        # 3. Render
        # Convert log to list
        log_lines = engine.log[-5:] if engine.log else ["Fight started!"]
        
        stats = [
            f"{p1.name}: {p1.hp}/{p1.max_hp} HP",
            f"{p2.name}: {p2.hp}/{p2.max_hp} HP"
        ]
        
        self.render(stats_text=stats, log_text=log_lines)

# Global Renderer Instance
renderer = SceneRenderer()

if __name__ == "__main__":
    # Test Code
    renderer.init_window()
    renderer.load_scene("town_street")
    
    player = Actor("Hero", "cowboy_male", 100, 300, "idle", False)
    enemy = Actor("Bandit", "bandit_male", 500, 300, "aiming", True)
    
    renderer.add_actor(player)
    renderer.add_actor(enemy)
    
    import time
    # Simple animation loop
    for i in range(50):
        player.x += 2
        renderer.render(
            stats_text=["HP: 100/100", "Ammo: 6/6", "Cash: $50.00"],
            log_text=[f"Frame {i}", "Moving..."]
        )
        time.sleep(0.05)

