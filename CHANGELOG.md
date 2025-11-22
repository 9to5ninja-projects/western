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
