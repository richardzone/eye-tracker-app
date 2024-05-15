import serial
import threading
import time
from serial.tools import list_ports
import queue
from .window_actions import move_mouse, show_calibration_dot, hide_calibration_dot
import re
from abc import ABC, abstractmethod

from .localization import setup_localization

_, _lang = setup_localization()

serial_data_queue = queue.Queue()
current_serial_connection = None

CALIBRATION_REQUIRED = "calibration_required"
CALIBRATION_DONE = "calibration_done"

def get_current_serial_connection():
    global current_serial_connection
    return current_serial_connection

class Command(ABC):
    @abstractmethod
    def matches(self, line):
        pass

    @abstractmethod
    def execute(self, line):
        pass


class CoordinateCommand(Command):
    def matches(self, line):
        match =  re.search(r'\d+,\s*\d+', line)
        return bool(match)

    def execute(self, line):
        coordinates = re.findall(r"\d+", line)
        if len(coordinates) != 2:
            raise ValueError(_("Data does not contain exactly two integers."))
        move_mouse(coordinates[0], coordinates[1], 0.2)
        return coordinates


class CalibrationRequiredCommand(Command):
    def matches(self, line):
        return line.strip() == CALIBRATION_REQUIRED

    def execute(self, line):
        serial_data_queue.put(_("Calibration required: showing calibration dot") + "\n")
        show_calibration_dot()
        return CALIBRATION_REQUIRED


class CalibrationDoneCommand(Command):
    def matches(self, line):
        return line.strip() == CALIBRATION_DONE

    def execute(self, line):
        serial_data_queue.put(_("Calibration done: hiding calibration dot") + "\n")
        hide_calibration_dot()
        return CALIBRATION_DONE


class CommandParser:
    def __init__(self, commands=None):
        if commands is None:
            self.commands = [CoordinateCommand(), CalibrationRequiredCommand(), CalibrationDoneCommand()]
        else:
            self.commands = commands

    def parse(self, line):
        for command in self.commands:
            if command.matches(line):
                return command.execute(line)
        raise ValueError(_("Unknown command: {}").format(line))


def read_from_serial(ser, parser):
    global current_serial_connection, serial_data_queue
    while get_current_serial_connection() is ser:
        if ser.in_waiting:
            line = ser.readline().decode("utf-8").rstrip()
            serial_data_queue.put(_("Received data from {}: {}").format(ser.port, line) + "\n")

            try:
                parser.parse(line)
            except ValueError as e:
                serial_data_queue.put(_("ERROR: error parsing above line, invalid data, error is: {}").format(e) + "\n")

        time.sleep(0.1)


def get_serial_ports():
    """Lists serial port names"""
    ports = [port.device for port in list_ports.comports()]
    return ports if ports else [_("No Ports Available")]

def start_serial_thread(port, baud_rate, parser=None):
    global current_serial_connection
    disconnect_from_serial() # Close existing serial connection if any

    if parser is None:
        parser = CommandParser()

    try:
        ser = serial.Serial(port, baud_rate, timeout=0)
        current_serial_connection = ser
        threading.Thread(target=read_from_serial, args=(ser, parser), daemon=True).start()
        serial_data_queue.put(_("Connected to {}").format(current_serial_connection.port) + "\n")
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
