# Western Standoff - Design Vision

## Core Philosophy
**"Every shot is chaos with intention."**

This is not just a shooter; it is a reputation-survival simulation. The gun is a tool for punctuation, but the consequences ripple through the social fabric of the game world.

## The Honor System (Social Filter)
Honor is not a high score; it is a filter that changes how the world interacts with the player.
- **Low Honor (Outlaw)**:
  - Recruitable gang members at the Cantina.
  - Bounties on your head.
  - Hunted by Sheriffs.
  - Doctor may refuse service or charge double.
- **High Honor (Lawman)**:
  - Can be deputized or become Sheriff.
  - Targeted by outlaws seeking fame.
  - Townsfolk offer discounts or free drinks.

## Combat & Collateral Damage
The random targeting system is a feature, not a bug. Missed shots have consequences:
- **Collateral Damage**: Hitting a bystander, killing a horse, or shattering a window creates debt and enemies.
- **Emergent Feuds**: The owner of a killed horse may hunt you down later.
- **Legal Trouble**: "Reckless endangerment" can lead to jail time even if you win the duel.

## The Economy of Violence
Money flows through blood and survival.
- **Income**:
  - **Bounties**: Hunt wanted men (requires Horse).
  - **Sheriff Salary**: Steady income, but you become a target.
  - **Dueling Wagers**: High risk, high reward.
  - **Bank Robberies**: The big score, but brings permanent heat.
- **Expenses**:
  - **Doctor Bills**: Proportional to injury severity.
  - **Horses**: Essential for multi-town play and survival.
  - **Bail/Fines**: The cost of getting caught or causing collateral damage.

## Tactical Injury System
Injuries are not just HP loss; they define your limitations.
- **Leg Wound**: Movement penalty. Cannot flee banks or chase bounties.
- **Arm Wound**: Accuracy penalty. Slower reload times.
- **Eye Loss**: Permanent perception and accuracy reduction.
- **Critical Wounds**: Massive recovery time and cost (bleeding cash at the Doctor's).

## The Horse: The Pivot Point
The horse is the key to the open world.
- **No Horse**: Trapped in the current town.
- **Horse**: Access to other towns, ability to flee reputation, chase targets.
- **Dead Horse**: You are vulnerable and stuck until you can afford a replacement.

## Multi-Town Roguelike Structure
The world is a collection of towns, each with its own laws and seed.
- **Town Types**:
  - **Civilized**: Strict laws, harsh penalties, high security.
  - **Lawless**: No sheriff, pure chaos, high danger.
- **Reputation Travel**: Wanted posters spread. Sheriffs telegraph warnings.
- **The Run**: The game continues until you are too injured, too broke, or too wanted to go on. Then, a new seed, a new character.

## The Living World
The world does not wait for the player.
- **The National List**: A persistent pool of named NPCs (Outlaws, Bounty Hunters, Duelists) with their own stats and agendas.
  - They migrate between towns based on "Heat" and opportunity.
  - They compete with the player: An NPC might kill your bounty target before you get there.
  - They hunt the player: If you are wanted, famous bounty hunters will track you down.
- **Volatile Law**: The Sheriff slot is not static.
  - **Sheriff**: Can be Player, NPC, or Empty. They can die, quit, or be run out of town.
  - **Deputy**: Might step up, flee, or challenge the killer of the previous Sheriff.
  - **Vacuum**: No Sheriff = Outlaw Magnet. Criminals flock to lawless towns.

## Emergent Town States
Towns evolve based on who is in charge (or who isn't).
- **Lawful**: Sheriff + Deputy. Low crime, high fines, safe but strict.
- **Transitional**: New Sheriff (Player/NPC). Uncertain loyalty.
- **Corrupt**: Sheriff takes bribes, ignores crimes.
- **Lawless**: No law. High danger, high opportunity for outlaws.
- **Vigilante**: Citizens enforce their own justice (Lynch mobs).

## The Player is Just Another Piece
You are not the protagonist; you are a survivor.
- **Reputation Attraction**:
  - **High Bounty**: Attracts elite NPC bounty hunters.
  - **High Honor**: Lawmen respect you; offers for Deputy jobs.
  - **Low Honor**: Outlaws seek you for gangs or grudge matches.
- **Persistence**:
  - **Same World**: If you die, you can reroll a new character in the same world. Your old character's corpse is in the cemetery, and their actions (and the chaos they caused) remain.
  - **Full Reset**: Generate a completely new world seed.

## Roles & Playstyles

### The Sheriff
- **Stationary**: Set up shop in one town.
- **Duty**: Enforce laws or accept bribes.
- **Target**: Face challengers seeking your badge.
- **Loss Condition**: Leave town and you lose the badge.

### The Outlaw
- **Mobile**: Rob banks, flee on horseback.
- **Hunted**: Sheriffs from previous towns track you.
- **Gang**: Recruit NPCs to aid in heists.
- **Risk**: Cannot settle; must keep moving.

## Progression & "No Game Over"
Death is rare; consequences are frequent.
- **Defeat**: Wake up at the Doctor's (debt) or in Jail (loss of time/items).
- **Jail**: Break out, serve time, or rot.
- **Fleeing**: Move to a new randomly generated town, but reputation follows.

## Procedural Generation
Each playthrough seeds a new world:
- **Towns**: Random names, layouts, and NPC dispositions.
- **Player**: Random starting stats and "past injuries".
- **Economy**: Variable prices and job availability.

## UI & HUD
- **Persistent HUD**: Wanted status, Town info, Gun stats, Visual sprite (injuries), Cash, Ammo, Horse status.
- **Duel Screen**: Full takeover. Tension building. Visible ammo cylinders. Range markers.
