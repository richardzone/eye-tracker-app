import pyautogui
import tkinter as tk
import random

from .localization import setup_localization

_, _lang = setup_localization()


DEFAULT_MOVE_SPEED = 0.7

crazy_movement_active = False

calibration_dot_window = None

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

def show_calibration_dot():
    global calibration_dot_window
    if calibration_dot_window and calibration_dot_window.winfo_exists():
        return

    screen_width, screen_height = viewport_size()

    calibration_dot_window = tk.Toplevel()
    calibration_dot_window.overrideredirect(True)
    calibration_dot_window.geometry(f"20x20+{screen_width // 2 - 10}+{screen_height // 2 - 10}")
    calibration_dot_window.attributes("-topmost", True)
    calibration_dot_window.attributes("-alpha", 0.7)
    calibration_dot_window.configure(bg='red')

    # Make sure the calibration dot window doesn't take focus
    calibration_dot_window.focus_set()
    calibration_dot_window.grab_release()

def hide_calibration_dot():
    global calibration_dot_window
    if calibration_dot_window:
        calibration_dot_window.destroy()
        calibration_dot_window = None
