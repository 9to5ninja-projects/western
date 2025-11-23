# WESTERN GAME - MODULAR ARCHITECTURE

A text-based Western adventure with visual scene rendering. Built for rapid iteration and easy asset integration.

## 🎯 CURRENT STATUS

**COMPLETE:**
- ✅ World map system with procedural town generation
- ✅ Travel system with random events and danger levels
- ✅ Scene rendering with sprite compositing
- ✅ Asset structure with placeholder images
- ✅ Basic game loop integration

**READY FOR:**
- Your pixel art assets (drop them in `/home/claude/assets/`)
- Integration with your existing duel system from the repo
- Town hub interactions (cantina, sheriff, doctor, etc.)
- NPC AI and gang management
- Save/load system

---

## 📁 FILE STRUCTURE

```
western/
├── world_map.py           # World state, towns, connections
├── travel_system.py       # Journey mechanics, random encounters
├── scene_renderer.py      # Visual composition (PIL-based)
├── western_game.py        # Main game loop (integrates everything)
├── setup_assets.py        # Asset directory generator
└── assets/               # Your pixel art goes here
    ├── scenes/           # Background images (640x380)
    ├── sprites/          # Character sprites (50x100)
    ├── portraits/        # Mugshots (140x150)
    ├── effects/          # Muzzle flashes, blood, etc. (40x40)
    └── ui/               # Buttons, borders, etc.
```

---

## 🧩 CORE SYSTEMS

### 1. WORLD MAP (`world_map.py`)

**Purpose:** Manages the overworld - multiple towns, travel routes, global state.

**Key Classes:**
- `TownNode` - A single town with traits, population, law level
- `TravelRoute` - Connection between two towns (distance, terrain, danger)
- `WorldMap` - The complete world state container

**Usage:**
```python
world = WorldMap()
world.generate_procedural_world(num_towns=5, seed=42)

# Get current town
current = world.get_town(world.current_location)

# Get travel options
routes = world.get_connections(current.id)

# Move player
world.set_location(new_town_id)
world.advance_time(days=3)
```

**Town Traits:**
- LAWLESS, STRICT_LAW, MINING, AGRICULTURAL, MILITARY, RELIGIOUS
- TRADING_POST, GHOST_TOWN, FORTIFIED, CORRUPT

Each trait affects gameplay, NPC reactions, available quests, etc.

---

### 2. TRAVEL SYSTEM (`travel_system.py`)

**Purpose:** Handles journeys between towns with time passage and random events.

**Key Classes:**
- `TravelEvent` - A random encounter during travel
- `TravelSystem` - Manages active journey state

**Event Types:**
- BANDIT_AMBUSH, MERCHANT_CARAVAN, INJURED_TRAVELER
- ABANDONED_CAMP, WILDLIFE_ENCOUNTER, OASIS
- WANTED_POSTER, FELLOW_TRAVELER, etc.

**Usage:**
```python
travel = TravelSystem()

# Start journey
journey = travel.start_journey(
    from_town="Dustfall",
    to_town="Saint's Rest", 
    distance_days=3,
    danger_level=6,
    terrain="desert"
)

# Progress each day
while not journey["completed"]:
    event = travel.advance_day()
    
    if event:
        # Handle event - present choices to player
        print(event.title)
        print(event.description)
        for choice in event.choices:
            print(f"- {choice}")
```

**Event Outcomes:**
Events have consequences defined in `outcomes` dict:
- Combat encounters
- Reputation changes
- Loot/gold gains or losses
- Skill checks (charisma, speed, survival)
- Health/resource changes

---

### 3. SCENE RENDERER (`scene_renderer.py`)

**Purpose:** Composite images to create visual game scenes matching your mockup.

**Key Classes:**
- `Actor` - Character in a scene with position and state
- `Effect` - Temporary visual effect (muzzle flash, blood, etc.)
- `SceneRenderer` - Composites everything into a frame

**Actor States:**
- IDLE, AIMING, SHOOTING, HIT, DOWN, DEAD

**Layout Zones (matching your mockup):**
- Viewport: (0, 0, 640, 380) - Main scene
- Portrait: (650, 0, 800, 120) - Character mugshot
- Stats: (650, 130, 800, 380) - HP, ammo, stats
- Log: (0, 390, 640, 600) - Combat log
- Buttons: (650, 390, 800, 600) - Command buttons

**Usage:**
```python
renderer = SceneRenderer()

# Load background
renderer.load_scene("cantina_interior")

# Add characters
player = Actor("Player", "cowboy_male", x=50, y=250, state=ActorState.AIMING)
enemy = Actor("Bandit", "bandit_male", x=500, y=250, state=ActorState.IDLE, facing_left=True)

renderer.add_actor(player)
renderer.add_actor(enemy)

# Add effects
renderer.add_effect(Effect("muzzle_flash", x=50, y=260))

# Render frame
frame = renderer.render(
    stats_text=["HP: 80/100", "Ammo: 5/6"],
    log_text=["You draw your gun!", "The bandit reaches for his holster."],
    buttons=["Shoot", "Take Cover", "Run"]
)

frame.save("output.png")  # or display in window
```

---

## 🎨 ASSET INTEGRATION

### Setup

Run this once to create the asset structure:

```bash
python setup_assets.py
```

This creates `/home/claude/assets/` with placeholder images.

### Asset Requirements

**Scenes (Backgrounds):**
- Size: 640x380 px
- Format: PNG (RGB)
- Examples: `town_street.png`, `cantina_interior.png`, `doctor_office.png`

**Character Sprites:**
- Size: 50x100 px (or 64x128 for more detail)
- Format: PNG with transparency (RGBA)
- Naming: `{state}_{direction}.png`
  - `idle_right.png`, `idle_left.png`
  - `aiming_right.png`, `aiming_left.png`
  - `shooting_right.png`, `shooting_left.png`
  - `hit_right.png`, `hit_left.png`
  - `down_right.png`, `down_left.png`

**Portraits:**
- Size: 140x150 px
- Format: PNG
- Examples: `player_male.png`, `sheriff.png`, `bandit_01.png`

**Effects:**
- Size: 40x40 px (flexible)
- Format: PNG with transparency
- Examples: `muzzle_flash.png`, `blood_splatter.png`, `dust_cloud.png`

### Adding Your Assets

1. Create your pixel art at the recommended sizes
2. Name files exactly as shown in the structure
3. Drop them into the appropriate `/home/claude/assets/` subfolder
4. Run your game - assets load automatically

**No coding required for asset swaps!**

---

## 🔌 INTEGRATING WITH YOUR EXISTING DUEL SYSTEM

Your `duel_engine.py` and `duel_engine_v2.py` can plug into this architecture:

### Integration Points

**1. Combat Initiation:**
```python
# In western_game.py, when combat starts:
from duel_engine_v2 import run_duel

def handle_combat(player_data, enemy_data):
    # Set up visual scene
    renderer.load_scene("dusty_street")
    renderer.add_actor(Actor("Player", "cowboy_male", x=50, y=250))
    renderer.add_actor(Actor("Enemy", "bandit_male", x=500, y=250, facing_left=True))
    
    # Run duel
    result = run_duel(player_data, enemy_data, 
                      render_callback=renderer.render,
                      log_callback=game.add_log)
    
    return result
```

**2. Visual State Updates:**
Your duel engine should call renderer methods to update visuals:
```python
# In duel turn resolution:
if player_hits:
    renderer.update_actor_state("Enemy", ActorState.HIT)
    renderer.add_effect(Effect("blood_splatter", enemy_x, enemy_y))
    log.append("You hit the bandit in the chest!")
```

**3. Render Callbacks:**
Your duel system can accept a `render_frame()` callback:
```python
def duel_turn(attacker, defender, render_frame=None):
    # ... resolve combat ...
    
    if render_frame:
        render_frame()  # Update visual display
```

---

## 🎮 GAME LOOP FLOW

```
START
  ↓
Generate World (5-10 towns)
  ↓
MAIN MENU LOOP
  ├─→ Explore Town
  │     ├─→ Cantina (drink, gamble, hear rumors)
  │     ├─→ Sheriff (bounties, jail)
  │     ├─→ Doctor (heal, buy medicine)
  │     ├─→ General Store (trade)
  │     └─→ Back to menu
  │
  ├─→ Travel
  │     ├─→ Choose destination
  │     ├─→ Day-by-day progress
  │     │     ├─→ Random events
  │     │     └─→ Player choices
  │     └─→ Arrive at new town
  │
  ├─→ View Map (world overview)
  │
  ├─→ Check Stats
  │
  ├─→ Rest (heal, pass time)
  │
  └─→ Quit
```

---

## 🚀 NEXT STEPS

### Phase 1: Asset Creation
1. Create 5-7 background scenes
2. Create 2-3 character sprite sets (player, bandit, sheriff)
3. Create character portraits
4. Create basic effects (muzzle flash, blood)

### Phase 2: Duel Integration
1. Connect your duel_engine.py to the renderer
2. Map combat states to sprite states
3. Add combat log integration
4. Test visual feedback during fights

### Phase 3: Town Hub
1. Create location classes (Cantina, Sheriff, etc.)
2. Add NPC interaction system
3. Implement shop/trade mechanics
4. Add reputation consequences

### Phase 4: Living World
1. NPC movement between towns
2. Bounty generation and tracking
3. Gang recruitment and management
4. Dynamic events based on player actions

### Phase 5: Save/Load
1. Serialize world state
2. Serialize player state
3. JSON-based save files
4. Continue from last location

---

## 🧪 TESTING

### Test World Generation
```bash
python world_map.py
```

### Test Travel System
```bash
python travel_system.py
```

### Test Scene Rendering
```bash
python scene_renderer.py
# Check /mnt/user-data/outputs/test_scene.png
```

### Test Full Game Loop
```bash
python western_game.py
```

---

## 💡 DESIGN PHILOSOPHY

**Modular:**
Each system (world, travel, rendering) is independent. You can test them separately and swap implementations easily.

**Asset-Driven:**
Game content is driven by assets, not code. Add new characters by adding sprite folders. Add new scenes by adding background images.

**State-Based, Not Animated:**
No complex animation engine. Characters have discrete states (idle, aiming, hit). Visual feedback comes from state swaps, not frame interpolation.

**Text + Image:**
The combat log tells the story. Images provide context and immersion. Balance tilts toward narrative over visual spectacle.

**Rapid Iteration:**
Changes take seconds, not hours. Tweak a town trait? Edit one line. New character? Drop in sprites. Adjust layout? Change zone coordinates.

---

## 📋 ASSET CHECKLIST

When you're ready to make this yours, create:

### Priority 1 (Core Gameplay)
- [ ] Main street background
- [ ] Cantina interior background  
- [ ] Player character sprites (all states)
- [ ] Bandit enemy sprites (all states)
- [ ] Player portrait
- [ ] Muzzle flash effect
- [ ] Blood splatter effect

### Priority 2 (World Variety)
- [ ] Desert travel background
- [ ] Sheriff office background
- [ ] Doctor office background
- [ ] Sheriff character sprites
- [ ] More enemy variants
- [ ] NPC portraits (3-4)

### Priority 3 (Polish)
- [ ] Additional town backgrounds (5-7 total)
- [ ] Special character sprites (gang leader, mysterious stranger)
- [ ] More effects (dust, smoke, impact)
- [ ] UI elements (custom buttons, borders)

---

## 🎯 THE VISION

This isn't just a text adventure with pictures. It's a **visual novel meets roguelike**, where:

- Every choice ripples through a living world
- Reputation matters more than raw stats
- Death is permanent but prestige carries forward
- Stories emerge from systemic interactions
- Art reinforces mood and stakes

The engine is ready. The structure is flexible. The assets are waiting for your vision.

**Now make it yours.**

---

## 📞 INTEGRATION NOTES

When you're ready to connect this to your existing repo:

1. Copy these files into your `/western/` directory
2. Your duel systems slot in as combat resolvers
3. Your NPC system populates towns
4. Your economy systems drive shops
5. Your gang mechanics layer on top of world travel

Everything here is designed to play nice with what you've already built.
