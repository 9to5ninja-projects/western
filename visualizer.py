import os
import threading
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Configuration
SCREEN_WIDTH = 800
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
        if event.char and event.char.isprintable():
            self.last_key = event.char
        # Handle special keys
        if event.keysym == "Return": self.last_key = "ENTER"
        if event.keysym == "Escape": self.last_key = "ESC"
        if event.keysym == "BackSpace": self.last_key = "BACKSPACE"

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

    def render(self, stats_text=None, log_text=None, buttons=None):
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
            canvas.paste(sprite, (pos_x, pos_y), sprite)

        # 4. Draw UI Layout (Mockup style)
        draw = ImageDraw.Draw(canvas)
        
        # Sidebar (Stats)
        draw.rectangle([SCENE_WIDTH + 10, 10, SCREEN_WIDTH - 10, SCENE_HEIGHT], outline="white")
        draw.text((SCENE_WIDTH + 20, 20), "STATS", fill="yellow", font=self.font)
        if stats_text:
            y_off = 50
            for line in stats_text:
                draw.text((SCENE_WIDTH + 20, y_off), line, fill="white", font=self.font)
                y_off += 20

        # Bottom Panel (Log)
        draw.rectangle([10, SCENE_HEIGHT + 10, SCENE_WIDTH, SCREEN_HEIGHT - 10], outline="white")
        draw.text((20, SCENE_HEIGHT + 20), "LOG", fill="yellow", font=self.font)
        if log_text:
            y_off = SCENE_HEIGHT + 50
            # Show last 8 lines
            for line in log_text[-8:]:
                draw.text((20, y_off), line, fill="white", font=self.font)
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
            
            y_off = btn_y + 40
            for btn in buttons:
                # btn = {"label": "Attack", "key": "1"}
                label = f"[{btn.get('key', '?')}] {btn.get('label', 'Action')}"
                
                # Draw button background
                draw.rectangle([btn_x + 5, y_off, btn_x + btn_w - 5, y_off + 25], fill=(50, 50, 50), outline="white")
                draw.text((btn_x + 10, y_off + 5), label, fill="white", font=self.font)
                y_off += 30

        # Update Window if it exists
        if self.window:
            self.window.update_image(canvas)

        return canvas

    def show(self):
        """Debug method to show the current frame"""
        img = self.render()
        img.show()

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

