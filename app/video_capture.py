import logging
import threading
import time
import tkinter as tk

import cv2
import cv2.aruco as aruco
from PIL import Image, ImageTk

from .localization import setup_localization
from .window_actions import move_mouse

_, _lang = setup_localization()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

current_video_device = None
video_label = None
stop_event = threading.Event()


def convert_aruco_marker_ids_to_coordinates(marker_ids):
    if len(marker_ids) != 4:
        logging.warning(f"{marker_ids} does not contain exactly 4 elements and coordinates cannot be deduced.")
        return None, None
    return 100 * marker_ids[0] + marker_ids[1], 100 * marker_ids[2] + marker_ids[3]


def detect_aruco_markers(img, dictionary=aruco.DICT_6X6_100):
    aruco_dict = aruco.getPredefinedDictionary(dict=dictionary)
    corners, ids, rejectedImgPoints = aruco.detectMarkers(image=img, dictionary=aruco_dict, parameters=None)

    # logging.debug(f"corners: {corners}")
    logging.debug(f"ids: {ids}")
    # logging.debug(f"rejectedImgPoints: {rejectedImgPoints}")

    if ids is None:
        logging.error("No ArUco markers detected.")
        return []

    # Sort detected markers by their x-coordinate (left to right)
    marker_positions_with_ids = [(corner[0][0][0], id[0]) for corner, id in zip(corners, ids)]
    marker_positions_with_ids.sort()

    logging.debug(f"marker_positions_with_ids: {marker_positions_with_ids}")

    marker_ids = [position[1] for position in marker_positions_with_ids]

    return marker_ids


def get_current_video_device():
    global current_video_device
    return current_video_device


def read_from_video_device(device_index, video_canvas) -> None:
    global current_video_device, stop_event

    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        raise IOError("Cannot open camera")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    logging.info(_("Opened video device {}").format(cap))
    current_video_device = cap
    stop_event.clear()

    while get_current_video_device() is cap and not stop_event.is_set():
        ret, frame = cap.read()

        if not ret:
            logging.warning("cap.read is False, retrying...")
            continue

        img = cv2.resize(frame, (1280, 720))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)

        if video_canvas.winfo_exists():
            video_canvas.img_tk = img_tk  # Keep a reference to prevent garbage collection
            video_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

        marker_ids = detect_aruco_markers(frame)
        logging.debug(f"marker_ids: {marker_ids}")
        x, y = convert_aruco_marker_ids_to_coordinates(marker_ids)
        logging.debug(f"x: {x}, y: {y}")
        if x is not None and y is not None:
            move_mouse(x, y)

        cv2.waitKey(50)


def get_video_devices():
    """
    Lists available video devices.
    """
    # checks the first 10 indexes.
    index = 0
    video_device_indices = []
    i = 10
    while i > 0:
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            video_device_indices.append(index)
            cap.release()
        index += 1
        i -= 1
    return video_device_indices if video_device_indices else [_("No Video Devices Available")]


def start_video_thread(device_index: int, canvas: tk.Canvas) -> bool:
    global current_video_device, stop_event
    stop_video_capture()  # End existing video capture if any

    try:
        threading.Thread(
            target=read_from_video_device, args=(device_index, canvas), daemon=True
        ).start()
        return True
    except IOError as e:
        logging.error(_("Failed to open video device: {}").format(e))
        return False


def stop_video_capture() -> None:
    global current_video_device, stop_event
    if current_video_device:
        logging.info(_("End video capture from {}").format(current_video_device))
        stop_event.set()  # Signal the thread to stop
        time.sleep(1)  # Give the thread some time to exit
        current_video_device.release()
        current_video_device = None
