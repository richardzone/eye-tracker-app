import logging
import random
import tkinter as tk
from enum import Enum

import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageTk

from .localization import setup_localization

_, _lang = setup_localization()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

DEFAULT_MOVE_SPEED = 0.7
CALIBRATION_DOT_SIZE = 50
crazy_movement_active = False
calibration_dot_window = None

aruco_marker_window = None


def generate_aruco_marker(marker_id: int, marker_size, dictionary=cv2.aruco.DICT_7X7_250):
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict=dictionary)
    marker_image = np.zeros((marker_size, marker_size), dtype=np.uint8)
    cv2.aruco.drawMarker(aruco_dict, marker_id, marker_size, marker_image, 1)
    return marker_image


class MarkerPosition(Enum):
    TOPLEFT = 1
    TOPCENTER = 2
    TOPRIGHT = 3
    MIDDLELEFT = 4
    CENTER = 5
    MIDDLERIGHT = 6
    BOTTOMLEFT = 7
    BOTTOMCENTER = 8
    BOTTOMRIGHT = 9


def get_position_coordinates(position, marker_size, screen_width, screen_height):
    if position == MarkerPosition.TOPLEFT:
        return 0, 0
    elif position == MarkerPosition.TOPCENTER:
        return (screen_width // 2 - marker_size // 2), 0
    elif position == MarkerPosition.TOPRIGHT:
        return screen_width - marker_size, 0
    elif position == MarkerPosition.MIDDLELEFT:
        return 0, (screen_height // 2 - marker_size // 2)
    elif position == MarkerPosition.CENTER:
        return (screen_width // 2 - marker_size // 2), (screen_height // 2 - marker_size // 2)
    elif position == MarkerPosition.MIDDLERIGHT:
        return screen_width - marker_size, (screen_height // 2 - marker_size // 2)
    elif position == MarkerPosition.BOTTOMLEFT:
        return 0, screen_height - marker_size
    elif position == MarkerPosition.BOTTOMCENTER:
        return (screen_width // 2 - marker_size // 2), screen_height - marker_size
    elif position == MarkerPosition.BOTTOMRIGHT:
        return screen_width - marker_size, screen_height - marker_size
    else:
        return 0, 0


def show_aruco_marker(position: MarkerPosition, marker_size=200, dictionary=cv2.aruco.DICT_7X7_250):
    global aruco_marker_window
    if aruco_marker_window and aruco_marker_window.winfo_exists():
        return

    screen_width, screen_height = viewport_size()
    x_position, y_position = get_position_coordinates(position, marker_size, screen_width, screen_height)

    aruco_marker_window = tk.Toplevel()
    aruco_marker_window.attributes("-alpha", 0.0)
    aruco_marker_window.overrideredirect(True)
    aruco_marker_window.attributes("-topmost", True)

    aruco_marker_window.geometry(
        f"{marker_size}x{marker_size}+{x_position}+{y_position}"
    )
    aruco_marker_window.attributes("-alpha", 1.0)

    marker_image = generate_aruco_marker(position.value, marker_size, dictionary)
    marker_image_pil = Image.fromarray(marker_image)
    marker_image_tk = ImageTk.PhotoImage(marker_image_pil)

    marker_label = tk.Label(aruco_marker_window, image=marker_image_tk)
    marker_label.image = marker_image_tk
    marker_label.pack()


def hide_aruco_marker():
    global aruco_marker_window
    if aruco_marker_window:
        aruco_marker_window.destroy()
        aruco_marker_window = None


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
        logging.error(_("Coordinates must be valid non-negative integers."))
        return
    except TypeError:
        logging.error(_("Coordinates must not be None and must be convertible to integers."))
        return

    screen_width, screen_height = viewport_size()
    if x < 0 or y < 0:
        logging.error(_("Coordinates must be non-negative."))
        return
    if x > screen_width or y > screen_height:
        logging.error(
            _("Coordinates must be within screen size: {}x{}.").format(
                screen_width, screen_height
            ))
        return
    pyautogui.moveTo(x, y, speed)


def viewport_size():
    return pyautogui.size()


def show_calibration_dot():
    global calibration_dot_window
    if calibration_dot_window and calibration_dot_window.winfo_exists():
        return

    screen_width, screen_height = viewport_size()
    x_position = int(screen_width / 2 - CALIBRATION_DOT_SIZE / 2)
    y_position = int(screen_height / 2 - CALIBRATION_DOT_SIZE / 2)

    calibration_dot_window = tk.Toplevel()
    calibration_dot_window.attributes("-alpha", 0.0)
    calibration_dot_window.overrideredirect(True)
    calibration_dot_window.attributes("-topmost", True)
    calibration_dot_window.configure(bg="red")

    calibration_dot_window.geometry(
        f"{CALIBRATION_DOT_SIZE}x{CALIBRATION_DOT_SIZE}+{x_position}+{y_position}"
    )
    calibration_dot_window.attributes("-alpha", 1.0)

    # Force the window manager to update the window's size and position
    # calibration_dot_window.update_idletasks()
    # calibration_dot_window.update()

    # Make sure the calibration dot window doesn't take focus
    # calibration_dot_window.grab_release()


def hide_calibration_dot():
    global calibration_dot_window
    if calibration_dot_window:
        calibration_dot_window.destroy()
        calibration_dot_window = None
