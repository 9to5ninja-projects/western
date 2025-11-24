# Development Roadmap

## Phase 1: Core Mechanics (Completed)
- [x] **Duel Engine**: Turn-based combat, body part targeting, ammo.
- [x] **Brawl Engine**: Non-lethal combat, HP vs Blood, Knockouts.
- [x] **Basic UI**: Persistent HUD, Town Menu, ASCII Visualizer.
- [x] **Game State**: Persistent player stats (Cash, Honor, Injuries).

## Phase 2: The Horse & Mobility (Completed)
- [x] **Horse Ownership**: Buying/Selling horses at Stables.
- [x] **Travel System**: Moving between towns (requires Horse).
- [x] **Flee Mechanic**: 
    - Implement "13 paces" rule in Duel Engine.
    - Leg injuries preventing flee.
    - Horse requirement for escaping town after crimes.

## Phase 3: Economy & Injuries (Completed)
- [x] **Tactical Injuries**:
    - Implement stat penalties for specific injuries (Leg=Speed, Arm=Acc).
    - Persistent injury tracking in `PlayerState`.
- [x] **Doctor**:
    - Dynamic pricing based on injury severity.
    - Recovery time (Time skip).
- [x] **Economy**:
    - General Store (Ammo, Gun upgrades).
    - Stables (Work for cash).
    - Bank (Deposit/Rob).

## Phase 4: Law & Order (The Meta) (Completed)
- [x] **Honor System**:
    - Sheriff interactions based on Honor.
    - Wanted levels and Bounties.
- [x] **Sheriff Role**:
    - Job board / Bounties.
    - Jail system (Bail/Breakout).
- [x] **Outlaw Role**:
    - Bank Robbery minigame.
    - Gang recruitment at Cantina.

## Phase 5: Procedural World (Completed)
- [x] **Town Generation**: Random names, economy modifiers, law levels.
- [x] **Town States**: Implement Lawful, Corrupt, Lawless, Vigilante states.
- [x] **NPC Generation**: Random duelists/brawlers with unique stats.

## Phase 6: The Living World (Completed)
- [x] **The National List**:
    - Pool of persistent NPCs (Outlaws, Bounty Hunters).
    - Migration logic (NPCs moving between towns).
- [x] **Volatile Law**:
    - Sheriff/Deputy slots that can be filled or emptied.
    - Consequences of "No Sheriff" (Crime wave).
- [x] **Permadeath Options**:
    - "New Character, Same World" logic.
    - "Full Reset" logic.

## Phase 7: Politics & Warfare (Completed)
- [x] **Group Combat**: Shootout engine for gang wars.
- [x] **Town Politics**: Mayors, Bribes, and Elections.
- [x] **Banking**: Fraud and Economy.
- [x] **Territory Control**:
    - Racket system (Protection money).
    - Town takeover mechanics (Line Battles).

## Phase 8: Scaling & Variety (Completed)
- [x] **Grand Larceny**:
    - Stagecoach Robbery (Mid-tier heist).
    - Train Robbery (End-game heist, requires specialists).
- [x] **Horse Economy**:
    - Stealing horses from stables (Stealth/Risk).
    - Selling stolen horses (Fence system - Planned).
- [x] **Unique Characters**:
    - Distinct Mayors and Sheriffs with personalities.
- [x] **Lore Items**:
    - Lore-based unique items (Guns, Hats, Horses).
- [x] **Trophy System**:
    - Collect Sheriff/Deputy badges from kills.
    - Infamy score based on trophies.
- [x] **Rival Gangs**:
    - Procedurally generated gangs (Name, Leader, Hideout).
    - Background simulation (Robberies, Shootouts, Recruitment).
    - Interactions (Ambushes, Bounties, Cantina).

## Phase 9: UI & Presentation (In Progress)
- [x] **Visual Engine Foundation**:
    - Scene Renderer (Pillow-based).
    - Asset directory structure.
- [x] **Menu Integration**:
    - Title Screen.
    - Town Navigation (Visual backgrounds).
    - Shop Interfaces.
- [ ] **Combat Visualization**:
    - Duel scene rendering (Currently ASCII).
    - Shootout scene rendering (Currently ASCII).
- [ ] **Asset Pipeline**:
    - Integration of pixel art assets.

## Phase 10: Narrative Reactivity (Completed)
- [x] **Milestone Events**:
    - **Infamy**: High bounty attracts US Marshals (Elite Hunters).
    - **Fame**: High Honor attracts "The Kid" (Rival Duelist seeking glory).
    - **Wealth**: High cash attracts thieves and muggers in towns.
    - **Gang Power**: Large gangs attract US Cavalry patrols.
- [x] **Nemesis System**:
    - Enemies who survive duels/shootouts can return with scars and vendettas.
    - Family members of killed Sheriffs/Mayors seeking revenge (Partially implemented via Nemesis memory).
    - Active hunting/ambushing by Nemeses.

## Phase 11: Gang Depth & End Game (In Progress)
- [x] **Gang Management**:
    - Equip members with weapons and hats.
    - Promote members (Training) for stat bonuses.
    - Manage wages and dismiss members.
- [ ] **Racket Economy**:
    - Implement weekly income collection.
    - Rival gang attacks on rackets.
- [ ] **End Game Scenarios**:
    - **Retirement**: Retire to a ranch with $5000.
    - **Conquest**: Control all towns (Mayor of all).
    - **Legend**: Max Reputation/Infamy.

## Phase 12: Combat Refinement (Completed)
- [x] **Combat 2.0**:
    - **Dynamic Controls**: Context-sensitive movement keys.
    - **Ammo Economy**: Reserve ammo, reloading, and scarcity.
    - **Brawl Overhaul**: Surrender, Counter-Attacks, Double KOs, Draws.
    - **Simultaneous Resolution**: Trading blows logic.

## Phase 13: Polish & Quality of Life (Planned)
- [ ] **Save System**:
    - Multiple save slots.
    - Auto-save frequency settings.
- [ ] **Settings Menu**:
    - Text speed, Volume (if audio added), ASCII vs Graphical toggle.
- [ ] **Bug Fixes**:
    - Resolve circular dependencies.
    - Fill in placeholder logic (e.g., Mayor options).



