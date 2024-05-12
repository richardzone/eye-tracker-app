import pyautogui
import random

from .localization import setup_localization

_, _lang = setup_localization()


DEFAULT_MOVE_SPEED = 0.7

# Flag to control the crazy movement
crazy_movement_active = False


def crazy_mouse_movement():
    global crazy_movement_active
    crazy_movement_active = True
    while crazy_movement_active:
        move_mouse_randomly(0.12)


def stop_crazy_mouse_movement():
    global crazy_movement_active
    crazy_movement_active = False


def move_mouse_randomly(speed=DEFAULT_MOVE_SPEED):
    screen_width, screen_height = viewport_size()
    random_x = random.randint(0, screen_width - 1)
    random_y = random.randint(0, screen_height - 1)
    move_mouse(random_x, random_y, speed)


def move_mouse(x_str, y_str, speed=DEFAULT_MOVE_SPEED):
    try:
        x = int(x_str)
        y = int(y_str)
    except ValueError:
        raise ValueError(_("Coordinates must be valid non-negative integers."))

    screen_width, screen_height = viewport_size()
    if x < 0 or y < 0:
        raise ValueError(_("Coordinates must be non-negative."))
    if x > screen_width or y > screen_height:
        raise ValueError(
            _("Coordinates must be within screen size: {}x{}.").format(
                screen_width, screen_height
            )
        )
    pyautogui.moveTo(x, y, speed)


def viewport_size():
    return pyautogui.size()
