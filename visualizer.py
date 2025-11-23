import os
from PIL import Image, ImageDraw, ImageFont

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

class SceneRenderer:
    def __init__(self):
        self.actors = []
        self.background = None
        self.ui_overlay = None
        self.font = self._load_font()
        
    def _load_font(self):
        # Try to load a default font, fallback to default
        try:
            return ImageFont.truetype("arial.ttf", 16)
        except IOError:
            return ImageFont.load_default()

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

    def render(self, stats_text=None, log_text=None):
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

        return canvas

    def show(self):
        """Debug method to show the current frame"""
        img = self.render()
        img.show()

if __name__ == "__main__":
    # Test Code
    renderer = SceneRenderer()
    renderer.load_scene("town_street")
    
    player = Actor("Hero", "cowboy_male", 100, 300, "idle", False)
    enemy = Actor("Bandit", "bandit_male", 500, 300, "aiming", True)
    
    renderer.add_actor(player)
    renderer.add_actor(enemy)
    
    renderer.render(
        stats_text=["HP: 100/100", "Ammo: 6/6", "Cash: $50.00"],
        log_text=["Welcome to Dusty Creek.", "A bandit appears!", "Draw your weapon!"]
    ).show()
