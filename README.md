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

### Meta-Game & Progression
- **Persistent World**: Track cash, honor, reputation, and bounties across days.
- **Town Hub**: Visit locations like the Cantina, Doctor, and Sheriff.
- **Social Filter**: Honor determines how NPCs react to you.
- **Consequences**: Collateral damage affects reputation; losing fights leads to medical bills or jail.

## Running the Game

### Full Game Loop
Run the main executable to experience the town, economy, and combat integration:
```bash
python main.py
```

### Prototypes
You can still run the isolated engines for testing:
- **Basic Duel**: `python duel_engine.py`
- **Advanced Simulation**: `python duel_engine_v2.py`

## Vision
This is a reputation-survival sim disguised as a shooter. The gun is just how you punctuate your choices.
- **Sheriff vs Outlaw**: Enforce the law or run from it.
- **Emergent Gameplay**: Random town seeds, collateral damage feuds, and dynamic rivalries.
- **No Game Over**: Defeat means waking up at the doctor's or in jail, not a reload screen.
