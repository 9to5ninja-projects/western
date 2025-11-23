# WESTERN GAME - QUICK START

## 🚀 GET STARTED IN 3 STEPS

### 1. SET UP ASSETS (2 minutes)

```bash
python setup_assets.py
```

This creates `/home/claude/assets/` with placeholder images. Replace placeholders with your pixel art.

### 2. TEST THE SYSTEMS

**World Map:**
```bash
python world_map.py
```
Generates 5 towns with traits, connections, and travel routes.

**Travel Events:**
```bash
python travel_system.py
```
Simulates a 3-day journey with random encounters.

**Scene Renderer:**
```bash
python scene_renderer.py
```
Composites a frame showing the layout from your mockup. Check `/mnt/user-data/outputs/test_scene.png`

### 3. RUN THE GAME

```bash
python western_game.py
```

Menu options:
- `1` - Explore Town (coming soon)
- `2` - Travel to another town (works now)
- `3` - View world map
- `4` - Check stats
- `5` - Rest
- `6` - Quit

---

## 🎨 ASSET WORKFLOW

### What You Need (Minimum Viable)

**Backgrounds (640x380 px):**
- `town_street.png` - Generic town view
- `cantina_interior.png` - Bar fight scene
- `wilderness.png` - For travel

**Character Sprites (50x100 px):**

Create one character folder: `assets/sprites/cowboy_male/`

Required files:
- `idle_right.png`, `idle_left.png`
- `aiming_right.png`, `aiming_left.png`
- `hit_right.png`, `hit_left.png`
- `down_right.png`, `down_left.png`

**Effects (40x40 px):**
- `muzzle_flash.png`
- `blood_splatter.png`

**That's it!** You can make everything else later.

---

## 📐 PIXEL ART TIPS

### Workflow
1. Sketch pose at 200x400 (4x target size)
2. Downsample to 50x100
3. Clean up at pixel level
4. Export with transparency

### States You Need

**IDLE:** Standing, gun holstered or at side
**AIMING:** Gun raised, pointing forward
**HIT:** Recoiling, gun lowered
**DOWN:** On ground, defeated

### Shortcuts

- **Mirror horizontally** for left/right variants (faster than redrawing)
- **Color swap** same base sprite for different characters
- **Trace from photos** of yourself in poses (not theft, just reference)
- Use **Aseprite** or **Piskel** (free online) for pixel art

---

## 🔌 CONNECT YOUR DUEL SYSTEM

You've already got the combat mechanics. Here's how to wire them up:

### In your duel_engine.py, add visual callbacks:

```python
def run_duel(player, enemy, render_callback=None, log_callback=None):
    """
    render_callback: function to update visuals
    log_callback: function to add to game log
    """
    
    # During combat turn:
    if player_hits_enemy:
        if render_callback:
            render_callback(
                player_state="shooting",
                enemy_state="hit",
                effect=("blood_splatter", enemy_x, enemy_y)
            )
        
        if log_callback:
            log_callback("You hit the bandit in the chest!")
```

### Then call from western_game.py:

```python
from duel_engine import run_duel

def handle_combat(self, enemy_data):
    # Visual setup
    self.renderer.load_scene("dusty_street")
    self.renderer.add_actor(Actor("Player", "cowboy_male", x=50, y=250))
    self.renderer.add_actor(Actor("Enemy", "bandit_male", x=500, y=250, facing_left=True))
    
    # Run combat with callbacks
    result = run_duel(
        player=self.player,
        enemy=enemy_data,
        render_callback=self.update_duel_visuals,
        log_callback=self.add_log
    )
    
    return result
```

---

## 🗺️ HOW THE WORLD WORKS

**At Start:**
- 5 towns generated procedurally
- Each has traits (Lawless, Mining, Religious, etc.)
- Connected by travel routes

**Travel:**
- Takes X days based on distance
- Each day: chance of random event
- Events have choices → consequences

**Town State:**
- Each town tracks your reputation
- Your crimes follow you
- NPCs can move between towns

**Persistence:**
- World state saved between sessions
- Your actions have permanent effects
- No "reset" - live with consequences

---

## 🎯 IMMEDIATE TODO

Your existing western repo has:
- ✅ Duel mechanics
- ✅ Combat resolution
- ✅ NPC system
- ✅ Town locations

This new architecture adds:
- ✅ Multi-town world map
- ✅ Travel system
- ✅ Visual rendering
- ✅ Asset pipeline

**What's Missing:**
- ❌ Connection between them

**Next Session Focus:**
Integrate your duel system with the scene renderer. Get one combat working visually. Everything else cascades from there.

---

## 📂 FILE GUIDE

```
world_map.py          → Town nodes, connections, world state
travel_system.py      → Journey mechanics, random events
scene_renderer.py     → Image compositing, visual display
western_game.py       → Main loop, ties everything together
setup_assets.py       → Run once to create asset structure

/assets/              → Your pixel art goes here
  /scenes/            → Backgrounds (640x380)
  /sprites/           → Characters (50x100)
    /cowboy_male/     → One char = one folder
  /portraits/         → Mugshots (140x150)
  /effects/           → Flashes, blood, etc (40x40)
```

---

## 🐛 TROUBLESHOOTING

**"FileNotFoundError" when rendering:**
→ Asset missing. Check `/home/claude/assets/` structure matches expected paths.
→ Renderer falls back to placeholders (colored boxes) when assets missing.

**"No module named X":**
→ Missing dependency. Install with: `pip install pillow`

**Scenes look wrong:**
→ Check asset dimensions match recommendations (640x380 for backgrounds, etc.)

**Sprites don't show:**
→ Verify naming: `{state}_{direction}.png` (e.g., `idle_right.png`)
→ Check sprite folder name matches Actor's `sprite_base` parameter

---

## 💬 WHAT TO ASK CLAUDE NEXT

"Help me integrate my duel_engine.py with the scene renderer"

"Create a simple town hub with 3 locations (cantina, sheriff, doctor)"

"Add save/load system for world state"

"Generate more diverse travel events"

"Build a gang recruitment system that works with the world map"

---

Ready to keep building? **The engine's warmed up and waiting.**
