# Western Standoff Engine

A text-based simulation engine for western duels and cantina brawls.

## Features

### Duel Mechanics
- **Turn-based Simultaneous Resolution**: Both combatants act at the same time.
- **Detailed Body Simulation**: Tracking structural damage to specific body parts (Head, Chest, Arms, Legs).
- **Blood Loss**: Fatal wounds cause bleeding over time.
- **Positioning**: Distance management, cover, and orientation (facing away/towards).

### Brawling Mechanics
- **HP & Consciousness**: Separate from lethal blood loss. Characters can be knocked out.
- **Stats**: Brawl Attack and Defense values.
- **Disarming**: Punches can knock weapons out of hands.

## Running the Prototypes

### Basic Duel Engine
Run the initial prototype to see basic shooting mechanics:
```bash
python duel_engine.py
```

### Advanced Engine (V2)
Run the advanced engine to see simulations of different scenarios (e.g., Brawler vs Gunman):
```bash
python duel_engine_v2.py
```

## Scenarios
The V2 engine includes pre-scripted AI behaviors to test mechanics:
- **Honorable Duel**: Both players pace 10 steps, turn, and fire.
- **Cheater**: Turns early to shoot the opponent in the back.
- **Brawler**: Rushes in to punch and disarm the gunman.
