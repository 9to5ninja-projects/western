import time
from visualizer import renderer

def options_to_buttons(options):
    buttons = []
    for key, value in options.items():
        # Simple truncation for button labels to avoid overflow
        label = value.split(" - ")[0] if " - " in value else value
        if len(label) > 20: label = label[:17] + "..."
        buttons.append({"label": label, "key": key})
    return buttons

def wait_for_user(prompt="Press Enter to continue...", player=None):
    if isinstance(prompt, list):
        log_text = prompt + ["(Press Enter)"]
    else:
        log_text = [prompt]

    renderer.render(
        log_text=log_text,
        buttons=[{"label": "Continue", "key": "ENTER"}],
        player=player
    )
    while True:
        key = renderer.get_input()
        if key in ["ENTER", "SPACE"]:
            break
