import os
import sys
import threading

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from .window_actions import (
    crazy_mouse_movement,
    move_mouse,
    move_mouse_randomly,
    stop_crazy_mouse_movement,
    viewport_size,
)
from .serial import (
    get_serial_ports,
    serial_data_queue,
    start_serial_thread,
    disconnect_from_serial,
)

from .localization import setup_localization

_, lang = setup_localization()


def on_escape(event=None):
    stop_crazy_mouse_movement()
    disconnect_from_serial()


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

    # root.update_idletasks()
    root.minsize(550, 300)

    def update_log_output():
        while not serial_data_queue.empty():
            line = serial_data_queue.get()
            if line:
                log_output.insert("end", line + "\n")
                log_output.see("end")  # Auto-scroll to the bottom
        root.after(100, update_log_output)  # Schedule to run again after 100 ms

    update_log_output()

    root.mainloop()


if __name__ == "__main__":
    gui_main()
