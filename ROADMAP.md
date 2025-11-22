# Development Roadmap

## Phase 1: Core Mechanics (Completed)
- [x] **Duel Engine**: Turn-based combat, body part targeting, ammo.
- [x] **Brawl Engine**: Non-lethal combat, HP vs Blood, Knockouts.
- [x] **Basic UI**: Persistent HUD, Town Menu, ASCII Visualizer.
- [x] **Game State**: Persistent player stats (Cash, Honor, Injuries).

## Phase 2: The Horse & Mobility (Next)
- [ ] **Horse Ownership**: Buying/Selling horses at Stables.
- [ ] **Travel System**: Moving between towns (requires Horse).
- [ ] **Flee Mechanic**: 
    - Implement "13 paces" rule in Duel Engine.
    - Leg injuries preventing flee.
    - Horse requirement for escaping town after crimes.

## Phase 3: Economy & Injuries
- [ ] **Tactical Injuries**:
    - Implement stat penalties for specific injuries (Leg=Speed, Arm=Acc).
    - Persistent injury tracking in `PlayerState`.
- [ ] **Doctor**:
    - Dynamic pricing based on injury severity.
    - Recovery time (Time skip).
- [ ] **Economy**:
    - General Store (Ammo, Gun upgrades).
    - Stables (Work for cash).
    - Bank (Deposit/Rob).

## Phase 4: Law & Order (The Meta)
- [ ] **Honor System**:
    - Sheriff interactions based on Honor.
    - Wanted levels and Bounties.
- [ ] **Sheriff Role**:
    - Job board / Bounties.
    - Jail system (Bail/Breakout).
- [ ] **Outlaw Role**:
    - Bank Robbery minigame.
    - Gang recruitment at Cantina.

## Phase 5: Procedural World
- [ ] **Town Generation**: Random names, economy modifiers, law levels.
- [ ] **NPC Generation**: Random duelists/brawlers with unique stats.
