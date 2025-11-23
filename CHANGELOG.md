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

## [0.7.0] - 2025-11-23

### Added
- **Brawl Combat Triangle (RPS System)**:
  - **Tactical Depth**: Brawling now follows a Rock-Paper-Scissors counter system.
    - **Jab beats Hook**: A fast jab interrupts the slower hook animation.
    - **Hook beats Block**: A heavy hook smashes through a defensive guard.
    - **Block beats Jab**: A successful block stops the jab and triggers an automatic counter-attack.
  - **New Action**: `BLOCK` added to the brawl menu.
  - **AI Update**: Opponents now utilize blocking and the full range of melee attacks.

## [0.8.0] - 2025-11-23

### Added
- **Game Structure & Persistence**:
  - **Main Menu**: New entry point with "New Game", "Continue", and "Quit" options.
  - **Character Creation Wizard**:
    - **Name Entry**: Custom character naming.
    - **Handedness Selection**: Choose Right or Left hand (affects combat).
    - **Starting Town**: Choose between Dusty Creek (Tutorial), Shinbone (Trade), or Brimstone (Danger).
  - **Save/Load System**:
    - **Persistence**: Game state (Player & World) is saved to `savegame.pkl`.
    - **Save Points**: Save when renting a room or quitting the game.
    - **Seamless Resume**: "Continue" option loads the exact state of the world and player.
  - **Refactored Main Loop**: Separated initialization from the game loop to support menu navigation.

## [0.9.0] - 2025-11-23

### Added
- **Permadeath & Legacy System**:
  - **Death Handling**: Upon death, players are presented with a choice instead of an immediate exit.
  - **Legacy Mode ("New Drifter")**: Start a new character in the *same* world instance.
    - Inherits the world state (Town heat, dead NPCs, rumors).
    - Previous character's death is recorded as a rumor.
    - Resets player-specific flags (e.g., Mayor status) while keeping world changes.
  - **Full Reset ("New World")**: Option to wipe the save and start fresh.
- **Code Refactoring**:
  - `handle_death` function added to `main.py` to manage the post-mortem flow.
  - `new_game` updated to accept an optional `existing_world` parameter for legacy inheritance.

## [0.10.0] - 2025-11-23

### Added
- **Territory Control Mechanics**:
  - **Rackets**: Gang leaders can now "Demand Protection" from Mayors.
    - Success depends on Gang Intimidation vs Town Lawfulness.
    - Generates weekly income (placeholder).
  - **Town Takeover (War)**:
    - **Positional Warfare**: New `ShootoutEngine` mode where teams battle for territory control (0-100 scale).
    - **Line Battle**: Players must push the battle line from 10 to 100 to seize the town.
    - **New Action**: `[M]ove` allows combatants to advance, sacrificing cover for position.
    - **Victory**: Eliminating defenders grants total control (Lawfulness = 0) and the town treasury.
  - **Gang Jail System**:
    - **Capture**: Gang members defeated in town shootouts have a 50% chance to be captured instead of killed.
    - **Bail**: Players can bail out captured members at the Sheriff's Office ($50.00).
- **Data Structure Updates**:
  - **Town Class**: Now tracks `rackets`, `jail` population, and dynamic `lawfulness`.
  - **Lawfulness**: Derived from town traits (Lawless=10, Poor=30, Rich=70, Fortified=90).

## [0.11.0] - 2025-11-23

### Added
- **Grand Larceny (Heists)**:
  - **Stagecoach Robbery**: Mid-tier heist requiring 3+ gang members and horses. Ambush coaches on the road for cash.
  - **Train Robbery**: End-game heist requiring 5+ gang members, horses, and a **Safecracker** specialist. High risk, massive reward.
- **Horse Economy**:
  - **Horse Theft**: Players can now attempt to steal horses from stables at night.
    - **Stealth Mechanic**: Success depends on Luck vs Town Heat.
    - **Risk**: Failure triggers a brawl with the Stablemaster and massive heat gain.
- **Trophy System**:
  - **Sheriff's Badge**: Killing a Sheriff now allows looting their badge as a trophy.
  - **Effect**: Badges grant +Reputation (Infamy) but -Honor.
- **New Item Types**:
  - Added `TROPHY` item type for badges and unique collectibles.

## [0.12.0] - 2025-11-23

### Added
- **Rival Gangs System**:
  - **Procedural Generation**: Rival gangs are now generated at the start of a new game.
    - **Attributes**: Name (e.g., "The Red Skulls"), Leader (High Bounty NPC), Hideout (Random Town), Members.
  - **Background Simulation**:
    - **Movement**: Gangs move between towns and hideouts.
    - **Activities**: Gangs perform robberies (increasing town heat), fight lawmen, and recruit new members.
    - **Rumors**: Gang actions generate rumors (e.g., "The Red Skulls robbed a store in Shinbone").
  - **Interactions**:
    - **Bounties**: Gang leaders and members appear on the Sheriff's Wanted List.
    - **Ambushes**: Traveling near a gang's hideout risks a road ambush.
    - **Cantina**: Gang members can be found mingling in local cantinas if their gang is in town.

### Fixed
- **Startup Crash**: Fixed an issue where the game would not launch due to a missing entry point in `main.py`.

## [0.13.0] - 2025-11-23

### Added
- **Unique Characters (Officials)**:
  - **Persistent Officials**: Mayors and Sheriffs are now persistent NPCs with names and personalities, rather than generic placeholders.
  - **Mayor Personalities**:
    - **Corrupt**: Cheaper bribes, lower town lawfulness.
    - **Idealist**: Cannot be bribed, higher lawfulness.
    - **Cowardly**: Easier to intimidate.
    - **Tyrant**: Harder to deal with, high taxes.
  - **Sheriff Personalities**:
    - **Corrupt**: Offers 50% discount on paying off bounties.
    - **Lawful**: Refuses to hire low-honor deputies.
    - **Drunkard**: Often found in the cantina (flavor).
    - **Gunslinger**: Deadly in a duel (High Accuracy/Speed).
  - **Dynamic Interactions**: Dialogue and options in Town Hall and Sheriff's Office now reflect the official's personality.

## [0.13.1] - 2025-11-23

### Fixed
- **Dead Officials Handling**:
  - **Sheriff**: If a Sheriff is killed, a temporary "Deputy" now mans the desk, allowing continued interaction.
  - **Mayor**: If a Mayor is killed, players can now call for a "Special Election" to restore order and potentially elect a new NPC.
- **Bank Functionality**:
  - Implemented **Deposit** and **Withdraw** features at the bank.
  - Added `bank_balance` to player stats for safe cash storage.
- **Stat Progression**:
  - Capped `Brawl Atk` and `Brawl Def` gains from stable work to 10 to prevent infinite grinding.
- **Rival Gangs**:
  - Rival gangs now actively defend the bank in their hideout town during robberies.

## [0.15.0] - 2025-11-23

### Added
- **Visual Engine Foundation**:
  - **Scene Renderer**: Implemented `visualizer.py` using Pillow to composite game scenes.
  - **Asset Structure**: Created directory structure for Scenes, Sprites, Portraits, UI, and Effects.
  - **Visualizer Integration**: Added support for rendering backgrounds, characters, and UI overlays.
  - **Fallback System**: Automatically generates placeholder graphics if assets are missing.



