import unittest
from unittest.mock import patch, Mock, call, MagicMock

import serial

from app.serial import (
    disconnect_from_serial,
    read_from_serial,
    get_serial_ports,
    start_serial_thread,
    CommandParser,
    CoordinateCommand,
    CalibrationRequiredCommand,
    CalibrationDoneCommand,
)


class TestSerial(unittest.TestCase):
    def test_coordinate_command_matches(self):
        coordinate_command = CoordinateCommand()
        test_strings = [
            "[-100,200]",
            "(123, 234)",
            "455, 123.5",
            "123,456,789",
            "1,,2",
            "(abc, def)",
        ]

        expected_matches = [True, True, True, True, False, False]

        for test_string, expected_match in zip(test_strings, expected_matches):
            with self.subTest(test_string=test_string, expected_match=expected_match):
                matches = coordinate_command.matches(test_string)
                self.assertEqual(
                    matches, expected_match, f"Unexpected result for '{test_string}'"
                )

    @patch("app.serial.move_mouse")
    def test_coordinate_command_execute(self, mock_move_mouse):
        coordinate_command = CoordinateCommand()
        test_line = "123,456"
        result = coordinate_command.execute(test_line)

        mock_move_mouse.assert_called_once_with("123", "456", 0.2)
        self.assertTrue(result)

    def test_calibration_required_command_matches(self):
        calibration_required_command = CalibrationRequiredCommand()
        self.assertTrue(calibration_required_command.matches("calibration_required"))
        self.assertFalse(calibration_required_command.matches("other_command"))

    @patch("app.serial.show_calibration_dot")
    def test_calibration_required_command_execute(self, mock_show_calibration_dot):
        calibration_required_command = CalibrationRequiredCommand()
        result = calibration_required_command.execute("calibration_required")

        mock_show_calibration_dot.assert_called_once()
        self.assertTrue(result)

    def test_calibration_done_command_matches(self):
        calibration_done_command = CalibrationDoneCommand()
        self.assertTrue(calibration_done_command.matches("calibration_done"))
        self.assertFalse(calibration_done_command.matches("other_command"))

    @patch("app.serial.hide_calibration_dot")
    def test_calibration_done_command_execute(self, mock_hide_calibration_dot):
        calibration_done_command = CalibrationDoneCommand()
        result = calibration_done_command.execute("calibration_done")

        mock_hide_calibration_dot.assert_called_once()
        self.assertTrue(result)

    def test_read_from_serial_coordinates(self):
        mock_ser = Mock()
        mock_ser.port = "COM8"
        mock_ser.in_waiting = True
        mock_ser.readline.return_value = b"[100,200]\n"

        mock_move_mouse = Mock()

        parser = CommandParser(
            commands=[
                CoordinateCommand(),
                CalibrationRequiredCommand(),
                CalibrationDoneCommand(),
            ]
        )

        with patch(
            "app.serial.get_current_serial_connection"
        ) as mock_get_current_serial, patch(
            "app.serial.logging.info"
        ) as mock_logging_info, patch("app.serial.move_mouse", mock_move_mouse):
            mock_get_current_serial.side_effect = [mock_ser, None]
            read_from_serial(mock_ser, parser)
            mock_logging_info.assert_has_calls(
                [
                    call("Received data from {}: [100,200]".format(mock_ser.port)),
                ]
            )
            mock_move_mouse.assert_called_once_with("100", "200", 0.2)

    def test_read_from_serial_calibration_required(self):
        mock_ser = Mock()
        mock_ser.port = "COM8"
        mock_ser.in_waiting = True
        mock_ser.readline.return_value = b"calibration_required\n"

        mock_show_calibration_dot = Mock()

        parser = CommandParser(
            commands=[
                CoordinateCommand(),
                CalibrationRequiredCommand(),
                CalibrationDoneCommand(),
            ]
        )

        with patch(
            "app.serial.get_current_serial_connection"
        ) as mock_get_current_serial, patch(
            "app.serial.logging.info"
        ) as mock_logging_info, patch("app.serial.show_calibration_dot", mock_show_calibration_dot):
            mock_get_current_serial.side_effect = [mock_ser, None]
            read_from_serial(mock_ser, parser)
            mock_logging_info.assert_has_calls(
                [
                    call("Received data from {}: calibration_required".format(mock_ser.port)),
                    call("calibration_required: showing calibration dot"),
                ]
            )
            mock_show_calibration_dot.assert_called_once()

    def test_read_from_serial_calibration_done(self):
        mock_ser = Mock()
        mock_ser.port = "COM8"
        mock_ser.in_waiting = True
        mock_ser.readline.return_value = b"calibration_done\n"

        mock_hide_calibration_dot = Mock()

        parser = CommandParser(
            commands=[
                CoordinateCommand(),
                CalibrationRequiredCommand(),
                CalibrationDoneCommand(),
            ]
        )

        with patch(
            "app.serial.get_current_serial_connection"
        ) as mock_get_current_serial, patch(
            "app.serial.logging.info"
        ) as mock_logging_info, patch("app.serial.hide_calibration_dot", mock_hide_calibration_dot):
            mock_get_current_serial.side_effect = [mock_ser, None]
            read_from_serial(mock_ser, parser)
            mock_logging_info.assert_has_calls(
                [
                    call("Received data from {}: calibration_done".format(mock_ser.port)),
                    call("calibration_done: hiding calibration dot"),
                ]
            )
            mock_hide_calibration_dot.assert_called_once()

    def test_read_from_serial_invalid_data(self):
        mock_ser = Mock()
        mock_ser.port = "COM8"
        mock_ser.in_waiting = True
        mock_ser.readline.return_value = b"invalid_data\n"

        parser = CommandParser(
            commands=[
                CoordinateCommand(),
                CalibrationRequiredCommand(),
                CalibrationDoneCommand(),
            ]
        )

        with patch(
            "app.serial.get_current_serial_connection"
        ) as mock_get_current_serial, patch(
            "app.serial.logging.error"
        ) as mock_logging_error, patch(
            "app.serial.logging.info"
        ) as mock_logging_info, patch("app.serial.move_mouse") as mock_move_mouse:
            mock_get_current_serial.side_effect = [mock_ser, None]
            read_from_serial(mock_ser, parser)
            mock_logging_info.assert_called_once_with(
                "Received data from {}: invalid_data".format(mock_ser.port)
            )
            mock_logging_error.assert_called_once_with(
                "ERROR: error parsing above line, invalid data, error is: Unknown command: invalid_data"
            )
            mock_move_mouse.assert_not_called()

    @patch("app.serial.list_ports.comports")
    def test_get_serial_ports_with_available_ports(self, mock_comports):
        mock_comports.return_value = [
            MagicMock(device="COM8"),
            MagicMock(device="USB Serial Port"),
            MagicMock(device="COM9"),
        ]
        expected_ports = ["COM8", "USB Serial Port", "COM9"]
        actual_ports = get_serial_ports()
        self.assertEqual(
            actual_ports,
            expected_ports,
            "Should return the list of available serial ports",
        )

    @patch("app.serial.list_ports.comports")
    def test_get_serial_ports_with_no_ports(self, mock_comports):
        mock_comports.return_value = []

        expected_ports = ["No Ports Available"]
        actual_ports = get_serial_ports()
        self.assertEqual(
            actual_ports,
            expected_ports,
            "Should return a message indicating no available ports",
        )

    def test_start_serial_thread_success(self):
        mock_serial = MagicMock()
        mock_serial.return_value.port = "COM8"
        with patch("app.serial.serial.Serial", mock_serial), patch(
            "app.serial.disconnect_from_serial"
        ) as mock_disconnect, patch(
            "app.serial.threading.Thread"
        ) as mock_thread, patch(
            "app.serial.logging.info"
        ) as mock_logging_info:
            result = start_serial_thread("COM8", 9600)

            mock_disconnect.assert_called_once()
            mock_serial.assert_called_once_with("COM8", 9600, timeout=0)
            mock_thread.assert_called_once()
            mock_logging_info.assert_called_once_with("Connected to COM8")
            self.assertTrue(result)

    def test_start_serial_thread_failure(self):
        with patch("app.serial.serial.Serial") as mock_serial, patch(
            "app.serial.disconnect_from_serial"
        ) as mock_disconnect, patch(
            "app.serial.logging.error"
        ) as mock_logging_error:
            mock_serial.side_effect = serial.SerialException("Connection failed")

            result = start_serial_thread("COM8", 9600)

            mock_disconnect.assert_called_once()
            mock_serial.assert_called_once_with("COM8", 9600, timeout=0)
            mock_logging_error.assert_called_once_with("Failed to connect: Connection failed")
            self.assertFalse(result)

    def test_disconnect_from_serial(self):
        disconnect_from_serial()
        mock_ser = Mock()
        mock_ser.port = "COM8"

        with patch("app.serial.current_serial_connection", mock_ser), patch(
            "app.serial.logging.info"
        ) as mock_logging_info:
            disconnect_from_serial()

        mock_ser.close.assert_called_once()
        mock_logging_info.assert_called_once_with("Disconnected from COM8")


if __name__ == "__main__":
    unittest.main()
