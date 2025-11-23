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

## [0.4.0] - 2025-11-22

### Added
- **Shootout Engine (`shootout_engine.py`)**:
  - **Group Combat**: Support for team-based battles (Player Gang vs Sheriff/Outlaws).
  - **Cover System**: Units can take cover to reduce hit chance.
  - **Auto-Play**: AI can take over player turns for large battles.
  - **Lethality**: Increased damage and critical hit chance in shootouts.
- **Town Politics & Economy**:
  - **Mayors**: Interact with town mayors to Bribe, Intimidate, or Kill them.
  - **Elections**: High reputation players can run for Mayor.
  - **Banking System**: Loot Bank Drafts from NPCs and attempt to cash them (Fraud mechanic).
  - **Town Influence**: Track player control over a town.
- **Gang Management**:
  - **Wages**: Gang members require daily wages based on skill.
  - **Charm Discount**: High Charm reduces wage costs.
  - **Camp Upkeep**: Track and pay wages at the Wilderness Camp.
- **Combat Depth**:
  - **Surrender**: Enemies may surrender when low on HP or disarmed.
  - **Recruitment**: Recruit surrendering enemies into your gang or as deputies.
  - **Tactical Injuries**: Specific injuries (Broken Arm, Concussion) now apply stat penalties.

## [0.3.0] - 2025-11-22

### Added
- **Living World Simulation**:
  - **Persistent NPCs**: Characters now have names, traits, and persist in the world.
  - **Simulation Loop**: The world updates when the player sleeps or travels.
  - **NPC Movement**: NPCs travel between towns.
  - **Rumor System**: NPCs generate rumors based on their actions (crimes, hunting, etc.).
  - **Population Control**: New NPCs spawn to replace the dead.
- **Character Depth (`characters.py`)**:
  - **Traits System**: NPCs have traits like `Sharpshooter`, `Brute`, `Drunkard`, `Safecracker`.
  - **Quirks**: Flavor text for NPC personalities (e.g., "Twitches constantly").
  - **Archetypes**: Distinct stats and gear for Cowboys, Outlaws, Sheriffs, etc.
- **Expanded Economy & Meta**:
  - **Town Traits**: Towns have tags like `Rich`, `Poor`, `Lawless`, `Fortified` affecting prices and danger.
  - **Bounty Hunting**: Sheriff's office lists active bounties based on world simulation.
  - **Gang Recruitment**: Recruit NPCs with specific traits for your gang.
  - **Bank Robbery**: Plan heists on specific towns, with difficulty based on town traits.
- **Travel System**:
  - Travel between towns takes time (Weeks).
  - Random road events (Strangers, Duels).

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

## [0.5.0] - 2025-11-22

### Added
- **Combat Refinement (Duel Engine V2)**:
  - **New Actions**:
    - `STEP IN`: Move towards opponent without ending turn (aggressive positioning).
    - `JUMP`: High evasion action (-30% hit chance for opponent) but prevents shooting.
    - `DUCK & SHOOT`: Fire while ducking (Increased accuracy, reduced evasion).
    - `RISE & SHOOT`: Fire while standing up.
  - **Stance Mechanics**:
    - **Ducking**: Increases accuracy (+15%) but decreases evasion (easier to be hit).
    - **Jumping**: Significantly increases evasion.
  - **Dirty Moves**:
    - **Spin & Shoot**: Shooting while facing away now automatically turns the character but incurs a 50% accuracy penalty.
- **Global Systems**:
  - **Cross-Town Bounties**: Sheriff's office now displays bounties for NPCs in other towns.
  - **Bank Fraud**: Looted Bank Drafts must be cashed at their specific town of origin (or forged with a Charm check).

## [0.6.0] - 2025-11-23

### Added
- **Advanced Melee Combat**:
  - **Handedness**: Players now have a dominant hand (Right by default).
  - **Punch Types**:
    - **Jab**: Uses off-hand. Fast (+15% Acc) but weak (-3 Dmg).
    - **Hook**: Uses dominant hand. Strong (+5 Dmg) but wild (-10% Acc).
  - **Broken Hand Mechanic**:
    - **Self-Injury**: 2% chance to break your hand when punching.
    - **Consequences**: A broken hand cannot be used for weapons or punching.
    - **Medical Treatment**: Doctors can "Cast" a broken hand ($25.00).
    - **Healing Time**: Casted hands take 6-8 weeks to heal, during which they remain unusable.
  - **Critical Hits**:
    - **Instant KO**: Dealing >20% of opponent's Max HP in one hit.
    - **Instant Death**: Dealing >30% of opponent's Max HP in one hit.
- **Dirty Moves Refinement**:
  - **Kick Sand**: Now requires facing the opponent and being within 3 spaces. Success chance reduced to 35%.
