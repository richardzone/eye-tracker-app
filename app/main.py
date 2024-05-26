import logging
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from .localization import setup_localization
from .serial import (
    get_serial_ports,
    start_serial_thread,
    disconnect_from_serial,
)
from .video_capture import get_video_devices, start_video_thread, stop_video_capture
from .window_actions import (
    crazy_mouse_movement,
    move_mouse,
    move_mouse_randomly,
    stop_crazy_mouse_movement,
    viewport_size,
    hide_calibration_dot,
    show_aruco_marker,
    hide_aruco_marker,
    MarkerPosition
)

_, lang = setup_localization()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class TkinterLoggingHandler(logging.Handler):
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        log_entry = self.format(record)
        self.log_widget.insert(tk.END, log_entry + '\n')
        self.log_widget.see(tk.END)  # Auto-scroll to the bottom


def on_escape(event=None):
    stop_crazy_mouse_movement()
    disconnect_from_serial()
    stop_video_capture()
    hide_calibration_dot()
    hide_aruco_marker()


def validate_and_move_mouse(x_str, y_str):
    try:
        move_mouse(x_str, y_str)
    except ValueError as e:
        messagebox.showerror(_("Invalid Input"), str(e))


def gui_main():
    screen_width, screen_height = viewport_size()

    root = tk.Tk()
    root.title(_("Eye Tracker App"))
    root.bind("<Escape>", on_escape)  # Bind the Escape key
    root.bind("1", lambda event: show_aruco_marker(position=MarkerPosition.TOPLEFT))
    root.bind("2", lambda event: show_aruco_marker(position=MarkerPosition.TOPCENTER))
    root.bind("3", lambda event: show_aruco_marker(position=MarkerPosition.TOPRIGHT))
    root.bind("4", lambda event: show_aruco_marker(position=MarkerPosition.MIDDLELEFT))
    root.bind("5", lambda event: show_aruco_marker(position=MarkerPosition.CENTER))
    root.bind("6", lambda event: show_aruco_marker(position=MarkerPosition.MIDDLERIGHT))
    root.bind("7", lambda event: show_aruco_marker(position=MarkerPosition.BOTTOMLEFT))
    root.bind("8", lambda event: show_aruco_marker(position=MarkerPosition.BOTTOMCENTER))
    root.bind("9", lambda event: show_aruco_marker(position=MarkerPosition.BOTTOMRIGHT))

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

    # Dropdown for video device selection
    video_devices = get_video_devices()
    video_devices_var = tk.StringVar(root)
    video_devices_var.set(video_devices[0])  # Set to first available port or message
    tk.Label(frame, text=_("Select Video Device:")).grid(
        row=14, column=0, padx=10, pady=5
    )
    video_device_dropdown = tk.OptionMenu(frame, video_devices_var, *video_devices)
    video_device_dropdown.grid(row=14, column=1, padx=10, pady=5)

    # Log output section
    log_output = scrolledtext.ScrolledText(frame, height=10)
    log_output.grid(row=15, column=0, columnspan=2, pady=10)

    # Add the custom logging handler
    log_handler = TkinterLoggingHandler(log_output)
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(log_handler)

    def connect_to_serial():
        if port_var.get() == _("No Ports Available"):
            messagebox.showerror(_("Error"), _("No serial ports available."))
            return
        start_serial_thread(port_var.get(), baud_var.get())

    connect_to_serial_button = tk.Button(
        frame, text=_("Connect to Serial (Hit Esc to Disconnect)"), command=connect_to_serial
    )
    connect_to_serial_button.grid(row=16, column=0, columnspan=2, pady=10)

    def capture_video():
        if video_devices_var.get() == _("No Video Devices Available"):
            messagebox.showerror(_("Error"), _("No Video Devices Available"))
            return

        # Create a new top-level window for video display
        video_window = tk.Toplevel(root)
        video_window.title(_("Video Capture"))

        video_canvas = tk.Canvas(video_window, width=1280, height=720)
        video_canvas.pack()

        start_video_thread(int(video_devices_var.get()), video_canvas)

    start_video_capture_button = tk.Button(
        frame, text=_("Start Video Capture (Hit Esc to Stop)"), command=capture_video
    )
    start_video_capture_button.grid(row=17, column=0, columnspan=2, pady=10)

    # Restart App button
    refresh_button = tk.Button(
        frame, text=_("Restart App"), command=lambda: restart_app(language_var.get())
    )
    refresh_button.grid(row=18, column=0, columnspan=2, padx=10)

    copyright_label = tk.Label(frame, text=_("© 2024 Eye Tracker"), font=("Arial", 8))
    copyright_label.grid(row=19, column=0, columnspan=2, pady=10)

    root.minsize(550, 300)

    root.mainloop()


if __name__ == "__main__":
    gui_main()
