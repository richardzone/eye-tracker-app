import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import random
import math

from .window_actions import (
    crazy_mouse_movement,
    move_mouse,
    move_mouse_randomly,
    stop_crazy_mouse_movement,
    viewport_size,
    hide_calibration_dot,
)
from .serial import (
    get_serial_ports,
    serial_data_queue,
    start_serial_thread,
    disconnect_from_serial,
)
from .localization import setup_localization

_, lang = setup_localization()

marker_size = 100
img_x = 1000 - marker_size

def on_escape(event=None):
    stop_crazy_mouse_movement()
    disconnect_from_serial()
    hide_calibration_dot()
    hide_aruco_marker()

def validate_and_move_mouse(x_str, y_str):
    try:
        move_mouse(x_str, y_str)
    except ValueError as e:
        messagebox.showerror(_("Invalid Input"), str(e))

def generate_aruco_marker():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    marker_size = 100
    marker_image = np.zeros((marker_size, marker_size), dtype=np.uint8)
    cv2.aruco.drawMarker(aruco_dict, 0, marker_size, marker_image, 1)
    return marker_image

def show_aruco_marker():
    global marker_label
    marker_image = generate_aruco_marker()
    marker_image_pil = Image.fromarray(marker_image)
    marker_image_tk = ImageTk.PhotoImage(marker_image_pil)

    if marker_label is None:
        marker_label = tk.Label(root, image=marker_image_tk)
        marker_label.image = marker_image_tk
        marker_label.place(x=0, y=0)
    else:
        marker_label.config(image=marker_image_tk)
        marker_label.image = marker_image_tk
        marker_label.place(x=0, y=0)

def hide_aruco_marker():
    global marker_label
    if marker_label is not None:
        marker_label.place_forget()

def detect_aruco_markers(frame):
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

    img0 = frame[img_x-50:img_x+marker_size+50, 1*marker_size-50:2*marker_size+50]
    corners, ids, _ = cv2.aruco.detectMarkers(image=img0, dictionary=aruco_dict)
    marker_id0 = ids[0][0] if ids is not None else 0

    img1 = frame[img_x-50:img_x+marker_size+50, 3*marker_size-50:4*marker_size+50]
    corners, ids, _ = cv2.aruco.detectMarkers(image=img1, dictionary=aruco_dict)
    marker_id1 = ids[0][0] if ids is not None else 0

    img2 = frame[img_x-50:img_x+marker_size+50, 5*marker_size-50:6*marker_size+50]
    corners, ids, _ = cv2.aruco.detectMarkers(image=img2, dictionary=aruco_dict)
    marker_id2 = ids[0][0] if ids is not None else 0

    img3 = frame[img_x-50:img_x+marker_size+50, 7*marker_size-50:8*marker_size+50]
    corners, ids, _ = cv2.aruco.detectMarkers(image=img3, dictionary=aruco_dict)
    marker_id3 = ids[0][0] if ids is not None else 0

    x = 100 * marker_id0 + marker_id1
    y = 100 * marker_id2 + marker_id3

    return x, y

def video_thread():
    print("inside video_thread")
    cap = cv2.VideoCapture(1)
    print(cap)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    while True:
        ret, frame = cap.read()
        print(ret, frame)
        if not ret:
            break
        x_det, y_det = detect_aruco_markers(frame)
        print(x_det, y_det)
        move_mouse(x_det, y_det)

        cv2.imshow('Camera', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def gui_main():
    global root, marker_label
    marker_label = None

    screen_width, screen_height = viewport_size()

    root = tk.Tk()
    root.title(_("Eye Tracker App"))
    root.bind("<Escape>", on_escape)  # Bind the Escape key
    root.bind("1", lambda event: show_aruco_marker())  # Bind the "1" key

    frame = tk.Frame(root)
    frame.pack(expand=True)

    supported_langs = {"English": "en", "中文": "zh"}

    def restart_app(selected_lang=None):
        selected_iso_code = (
            supported_langs[selected_lang] if selected_lang is not None else "en"
        )
        os.execl(
            sys.executable, sys.executable, *sys.argv, f"--lang={selected_iso_code}"
        )

    language_var = tk.StringVar(root)
    language_var.set("中文" if lang == "zh" else "English")  # Set default language
    language_dropdown = tk.OptionMenu(
        root, language_var, *supported_langs.keys(), command=restart_app
    )
    language_dropdown.pack()

    tk.Label(frame, text=_("X Coordinate:")).grid(row=5, column=0, padx=10, pady=5)
    tk.Label(frame, text=_("Y Coordinate:")).grid(row=6, column=0, padx=10, pady=5)

    x_entry = tk.Entry(frame)
    y_entry = tk.Entry(frame)

    x_entry.grid(row=5, column=1, padx=10, pady=5)
    y_entry.grid(row=6, column=1, padx=10, pady=5)

    tk.Label(frame, text=_("Display Size:")).grid(row=7, column=0, padx=10, pady=5)
    display_size_entry = tk.Entry(frame)
    display_size_entry.insert(0, f"{screen_width} x {screen_height}")
    display_size_entry.configure(state="readonly")
    display_size_entry.grid(row=7, column=1, padx=10, pady=5)

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    move_button = tk.Button(
        frame,
        text=_("Move Mouse To Above Coordinates"),
        command=lambda: validate_and_move_mouse(x_entry.get(), y_entry.get()),
    )
    move_button.grid(row=8, column=0, columnspan=2, pady=10)

    random_move_button = tk.Button(
        frame, text=_("Random Move Mouse"), command=move_mouse_randomly
    )
    random_move_button.grid(row=9, column=0, columnspan=2, pady=10)

    go_crazy_button = tk.Button(
        frame,
        text=_("Go Crazy (hit Esc to stop)"),
        command=lambda: threading.Thread(
            target=crazy_mouse_movement, daemon=True
        ).start(),
    )
    go_crazy_button.grid(row=10, column=0, columnspan=2, pady=10)

    # Horizontal separator line
    separator = ttk.Separator(frame, orient="horizontal")
    separator.grid(row=11, column=0, columnspan=2, sticky="ew", pady=10)

    # Dropdown for serial port selection
    ports = get_serial_ports()
    port_var = tk.StringVar(root)
    port_var.set(ports[0])  # Set to first available port or message
    tk.Label(frame, text=_("Select Serial Port:")).grid(
        row=12, column=0, padx=10, pady=5
    )
    port_dropdown = tk.OptionMenu(frame, port_var, *ports)
    port_dropdown.grid(row=12, column=1, padx=10, pady=5)

    # Baud rate entry
    tk.Label(frame, text=_("Baud Rate:")).grid(row=13, column=0, padx=10, pady=5)
    baud_var = tk.StringVar(root, value="9600")  # Default value
    baud_entry = tk.Entry(frame, textvariable=baud_var)
    baud_entry.grid(row=13, column=1, padx=10, pady=5)

    # Log output section
    log_output = scrolledtext.ScrolledText(frame, height=10)
    log_output.grid(row=14, column=0, columnspan=2, pady=10)

    def connect():
        if port_var.get() == _("No Ports Available"):
            messagebox.showerror(_("Error"), _("No serial ports available."))
            return
        start_serial_thread(port_var.get(), baud_var.get())

    # Connect button
    connect_button = tk.Button(
        frame, text=_("Connect to Serial (Hit Esc to Disconnect)"), command=connect
    )
    connect_button.grid(row=15, column=0, columnspan=2, pady=10)

    # Restart App button
    refresh_button = tk.Button(
        frame, text=_("Restart App"), command=lambda: restart_app(language_var.get())
    )
    refresh_button.grid(row=16, column=0, columnspan=2, padx=10)

    copyright_label = tk.Label(frame, text=_("© 2024 Eye Tracker"), font=("Arial", 8))
    copyright_label.grid(row=17, column=0, columnspan=2, pady=10)

    root.minsize(550, 300)

    def update_log_output():
        while not serial_data_queue.empty():
            line = serial_data_queue.get()
            if line:
                log_output.insert("end", line + "\n")
                log_output.see("end")  # Auto-scroll to the bottom
        root.after(50, update_log_output)  # Schedule to run again after 50 ms

    update_log_output()

    # Start the video processing thread
    threading.Thread(target=video_thread, daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    gui_main()

