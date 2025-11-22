# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-11-22

### Added
- **Duel Engine Prototype (`duel_engine.py`)**:
  - Basic turn-based combat loop.
  - Body part targeting (Head, Chest, Arms, Legs).
  - Ammo management and reloading.
  - Movement (Step forward/back, Flee).
  - Stance system (Standing, Ducking, Jumping).
  - Basic injury system affecting stats.

- **Duel Engine V2 (`duel_engine_v2.py`)**:
  - **Blood System**: Lethal damage tracking via blood loss (12 pints).
  - **HP System**: Non-lethal damage tracking for brawls.
  - **Weapon States**: Holstered, Drawn, Dropped.
  - **Orientation**: Facing opponent vs Facing away (for "Turn and Draw" duels).
  - **Advanced Actions**: Pace, Turn, Draw, Pick Up, Punch.
  - **Brawling Mechanics**:
    - Punching (Atk vs Def).
    - Knockouts (HP < 20%).
    - Disarming opponents.
  - **Simulation Scenarios**:
    - Honorable Duel.
    - Cheater vs Honorable.
    - Brawler vs Gunman.

## [0.2.0] - 2025-11-22

### Added
- **Game State Management (`game_state.py`)**:
  - Persistent player stats (Cash, Honor, Reputation, Bounty).
  - Inventory system (Weapons, Ammo, Horses).
  - World state (Time, Day, Town Name).
- **User Interface (`ui.py`)**:
  - Persistent HUD with ASCII art layout.
  - Town menu navigation.
  - Location-specific interactions (Cantina, Doctor, etc.).
- **Main Game Loop (`main.py`)**:
  - Integrated town exploration and combat.
  - Cantina interactions: Drinking (Heal), Brawling (Non-lethal), Dueling (Lethal).
  - Doctor interaction: Paid healing.
  - Sleep mechanic: Advance day and heal.
- **Visualizer**:
  - ASCII arena rendering for combat.
  - Turn-by-turn animation.
