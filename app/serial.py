import serial
import threading
import time
from serial.tools import list_ports
import queue
from .window_actions import move_mouse
import re

from .localization import setup_localization

_, _lang = setup_localization()

serial_data_queue = queue.Queue()
current_serial_connection = None


# Assuming this is in your `app.serial` module
def get_current_serial_connection():
    global current_serial_connection
    return current_serial_connection


def read_from_serial(ser):
    global current_serial_connection, serial_data_queue
    while get_current_serial_connection() is ser:
        if ser.in_waiting:
            line = ser.readline().decode("utf-8").rstrip()
            # Put the line into the queue for logging widget
            serial_data_queue.put(
                _("Got data from {}: {}").format(ser.port, line) + "\n"
            )

            try:
                coordinates = re.findall(r"\d+", line)
                if len(coordinates) != 2:
                    raise ValueError(_("Data does not contain exactly two integers."))
                move_mouse(coordinates[0], coordinates[1], 0.2)

            except ValueError as e:
                serial_data_queue.put(
                    _(
                        "ERROR: error parsing above line, invalid data, error is: {}"
                    ).format(e)
                    + "\n"
                )

        time.sleep(0.1)


def get_serial_ports():
    """Lists serial port names"""
    ports = [port.device for port in list_ports.comports()]
    return ports if ports else [_("No Ports Available")]


def start_serial_thread(port, baud_rate):
    global current_serial_connection
    # Close existing serial connection if any
    disconnect_from_serial()

    try:
        ser = serial.Serial(port, baud_rate, timeout=5)
        current_serial_connection = ser
        threading.Thread(target=read_from_serial, args=(ser,), daemon=True).start()
        serial_data_queue.put(
            _("Connected to {}").format(current_serial_connection.port) + "\n"
        )
        return True
    except serial.SerialException as e:
        serial_data_queue.put(_("Failed to connect: {}").format(e))
        return False


def disconnect_from_serial():
    global current_serial_connection
    if current_serial_connection:
        port = current_serial_connection.port
        current_serial_connection.close()
        current_serial_connection = None
        serial_data_queue.put(_("Disconnected from {}").format(port) + "\n")
