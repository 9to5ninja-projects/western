import random
import time
from characters import NPC
from combat_runner import start_duel, start_brawl, loot_screen
from game_utils import wait_for_user
from visualizer import renderer

def check_story_events(player, world):
    """
    Checks for milestone events based on player stats.
    Returns True if an event occurred (to interrupt normal flow), False otherwise.
    """
    
    # 1. THE CHALLENGER (High Honor/Duelist)
    # Triggers if player is a famous good guy or duelist
    if player.duel_wins >= 5 and player.honor > 10 and random.random() < 0.1:
        trigger_challenger_event(player, world)
        return True

    # 2. THE MARSHAL (High Bounty)
    # Triggers if bounty is high
    if player.bounty > 500 and random.random() < 0.15:
        trigger_marshal_event(player, world)
        return True

    # 3. THE THIEF (High Cash)
    # Triggers if player is rich (usually during sleep/travel, but can happen in town)
    if player.cash > 500 and random.random() < 0.05:
        trigger_thief_event(player, world)
        return True
        
    # 4. THE PREACHER (Low Honor)
    if player.honor < -20 and random.random() < 0.1:
        trigger_preacher_event(player, world)
        return True

    return False

def trigger_challenger_event(player, world):
    kid = NPC("Cowboy")
    kid.name = "The Kid"
    kid.acc += 10
    kid.spd += 10
    kid.get_line = lambda: "I hear you're the fastest. I'm here to prove you wrong."
    
    renderer.render(
        log_text=[
            "A young gunslinger steps into your path.",
            f"{kid.name}: '{kid.get_line()}'",
            "He demands a duel.",
            "Accept? (Y/N)"
        ],
        player=player,
        buttons=[{"label": "Duel", "key": "Y"}, {"label": "Decline (-Rep)", "key": "N"}]
    )
    
    if renderer.get_input() == "Y":
        start_duel(player, world, kid)
        if player.alive and not kid.alive:
            player.reputation += 10
            wait_for_user(["You defeated The Kid.", "Your legend grows."], player=player)
    else:
        player.reputation -= 5
        wait_for_user(["You walk away.", "The crowd whispers cowardice."], player=player)

def trigger_marshal_event(player, world):
    marshal = NPC("Sheriff")
    marshal.name = "U.S. Marshal Cogburn"
    marshal.hp = 120
    marshal.acc = 85
    marshal.spd = 15
    marshal.weapon = next((w for w in marshal.inventory if w.item_type.name == "WEAPON"), None) # Ensure weapon
    
    renderer.render(
        log_text=[
            "A grim figure in a long coat approaches.",
            f"{marshal.name}: 'End of the line, {player.name}.'",
            "He holds a warrant for your arrest.",
            "Surrender or Draw?"
        ],
        player=player,
        buttons=[{"label": "Draw!", "key": "D"}, {"label": "Surrender", "key": "S"}]
    )
    
    if renderer.get_input() == "D":
        start_duel(player, world, marshal)
        if player.alive and not marshal.alive:
            player.reputation += 50
            player.bounty += 500 # Killing a Marshal is bad news
            world.add_heat(100)
            wait_for_user(["You killed a U.S. Marshal!", "The law will never stop hunting you now."], player=player)
    else:
        # Surrender logic (Game Over or Jail)
        wait_for_user(["You surrender to the Marshal.", "You are taken to federal prison.", "GAME OVER (For now)"], player=player)
        player.alive = False # Soft game over for now

def trigger_thief_event(player, world):
    thief = NPC("Outlaw")
    thief.name = "Slick Fingers"
    
    # Thief tries to steal 10% of cash
    steal_amount = int(player.cash * 0.1)
    
    renderer.render(
        log_text=[
            "You bump into a stranger...",
            "Hey! He's trying to pick your pocket!",
            "Stop him!"
        ],
        player=player,
        buttons=[{"label": "Punch Him", "key": "P"}, {"label": "Let Him Go", "key": "L"}]
    )
    
    if renderer.get_input() == "P":
        start_brawl(player, world, thief)
        if player.alive and not thief.alive: # Or KO
            wait_for_user(["You taught the thief a lesson."], player=player)
    else:
        player.cash -= steal_amount
        wait_for_user([f"The thief escapes with ${steal_amount}!"], player=player)

def trigger_preacher_event(player, world):
    renderer.render(
        log_text=[
            "A fanatic preacher points a finger at you!",
            "Preacher: 'Sinner! Murderer! The Devil walks among us!'",
            "The crowd looks at you with fear and disgust.",
            "(-5 Reputation, -5 Charm)"
        ],
        player=player
    )
    player.reputation = max(0, player.reputation - 5)
    player.charm_mod -= 5 # Temporary debuff? Or permanent stat hit? Let's say stat hit for now.
    wait_for_user()
