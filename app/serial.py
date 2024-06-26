import logging
import re
import threading
import time
from abc import ABC, abstractmethod
from typing import List, Optional

import serial
from serial.tools import list_ports

from .localization import setup_localization
from .window_actions import move_mouse, show_calibration_dot, hide_calibration_dot

_, _lang = setup_localization()

current_serial_connection: Optional[serial.Serial] = None

CALIBRATION_REQUIRED = "calibration_required"
CALIBRATION_DONE = "calibration_done"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_current_serial_connection() -> Optional[serial.Serial]:
    """
    Returns the currently active serial connection, if any.
    """
    global current_serial_connection
    return current_serial_connection


class Command(ABC):
    """
    Abstract base class for command objects.
    """

    @abstractmethod
    def matches(self, line: str) -> bool:
        """
        Checks if the given line matches the command pattern.
        """
        pass

    @abstractmethod
    def execute(self, line: str) -> bool:
        """
        Executes the command for the given line.
        """
        pass


class CoordinateCommand(Command):
    """
    Command class for handling coordinate commands.
    """

    def matches(self, line: str) -> bool:
        """
        Checks if the given line matches the coordinate command pattern.
        """
        match = re.search(r"\d+,\s*\d+", line)
        return bool(match)

    def execute(self, line: str) -> bool:
        """
        Executes the coordinate command by moving the mouse cursor.
        """
        coordinates = re.findall(r"\d+", line)
        if len(coordinates) != 2:
            raise ValueError(_("Data does not contain exactly two integers."))
        move_mouse(coordinates[0], coordinates[1], 0.2)
        return True


class CalibrationRequiredCommand(Command):
    """
    Command class for handling calibration_required commands.
    """

    def matches(self, line: str) -> bool:
        """
        Checks if the given line matches the calibration_required command.
        """
        return line.strip() == CALIBRATION_REQUIRED

    def execute(self, line: str) -> bool:
        """
        Executes the calibration_required command by showing the calibration dot.
        """
        logging.info(_("calibration_required: showing calibration dot"))
        show_calibration_dot()
        return True


class CalibrationDoneCommand(Command):
    """
    Command class for handling calibration_done commands.
    """

    def matches(self, line: str) -> bool:
        """
        Checks if the given line matches the calibration_done command.
        """
        return line.strip() == CALIBRATION_DONE

    def execute(self, line: str) -> bool:
        """
        Executes the calibration_done command by hiding the calibration dot.
        """
        logging.info(_("calibration_done: hiding calibration dot"))
        hide_calibration_dot()
        return True


class CommandParser:
    """
    Class for parsing and executing commands from serial input.
    """

    def __init__(self, commands: Optional[List[Command]] = None):
        """
        Initializes the CommandParser with a list of command objects.
        If no list is provided, it uses the default set of commands.
        """
        if commands is None:
            self.commands = [
                CoordinateCommand(),
                CalibrationRequiredCommand(),
                CalibrationDoneCommand(),
            ]
        else:
            self.commands = commands

    def parse(self, line: str) -> bool:
        """
        Parses the given line and executes the corresponding command, if any.
        Returns True if a command was executed successfully, False otherwise.
        """
        for command in self.commands:
            if command.matches(line):
                return command.execute(line)
        raise ValueError(_("Unknown command: {}").format(line))


def read_from_serial(ser: serial.Serial, parser: CommandParser) -> None:
    """
    Reads data from the serial connection and parses/executes commands.
    """
    global current_serial_connection
    while get_current_serial_connection() is ser:
        if ser.in_waiting:
            line = ser.readline().decode("utf-8").rstrip()
            logging.info(_("Received data from {}: {}").format(ser.port, line))

            try:
                parser.parse(line)
            except ValueError as e:
                logging.error(_("ERROR: error parsing above line, invalid data, error is: {}").format(e))

        time.sleep(0.1)


def get_serial_ports() -> List[str]:
    """
    Lists available serial port names.
    """
    ports = [port.device for port in list_ports.comports()]
    return ports if ports else [_("No Ports Available")]


def start_serial_thread(
    port: str, baud_rate: int, parser: Optional[CommandParser] = None
) -> bool:
    """
    Starts a new thread for reading from the serial connection.
    Returns True if the thread was started successfully, False otherwise.
    """
    global current_serial_connection
    disconnect_from_serial()  # Close existing serial connection if any

    if parser is None:
        parser = CommandParser()

    try:
        ser = serial.Serial(port, baud_rate, timeout=0)
        current_serial_connection = ser
        threading.Thread(
            target=read_from_serial, args=(ser, parser), daemon=True
        ).start()
        logging.info(_("Connected to {}").format(current_serial_connection.port))
        return True
    except serial.SerialException as e:
        logging.error(_("Failed to connect: {}").format(e))
        return False


def disconnect_from_serial() -> None:
    """
    Closes the current serial connection, if any.
    """
    global current_serial_connection
    if current_serial_connection:
        port = current_serial_connection.port
        current_serial_connection.close()
        current_serial_connection = None
        logging.info(_("Disconnected from {}").format(port))
