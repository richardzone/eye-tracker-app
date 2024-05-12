import unittest
from unittest.mock import patch, Mock, call, MagicMock
import serial
from app.serial import (
    disconnect_from_serial,
    read_from_serial,
    get_serial_ports,
    start_serial_thread,
)


class TestSerial(unittest.TestCase):
    def test_read_from_serial_successful(self):
        mock_ser = Mock()
        mock_ser.in_waiting = True
        mock_ser.readline.return_value = b"100,200\n"

        mock_queue = Mock()
        mock_move_mouse = Mock()

        with patch(
            "app.serial.get_current_serial_connection"
        ) as mock_get_current_serial, patch(
            "app.serial.serial_data_queue", mock_queue
        ), patch("app.serial.move_mouse", mock_move_mouse):
            mock_get_current_serial.side_effect = [mock_ser, None]
            read_from_serial(mock_ser)

        # Assert the expected calls were made
        mock_queue.put.assert_has_calls(
            [
                call("Got data from {}: 100,200".format(mock_ser.port) + "\n"),
            ]
        )
        mock_move_mouse.assert_called_once_with("100", "200", 0.2)

    def test_read_from_serial_invalid_data(self):
        mock_ser = Mock()
        mock_ser.port = "COM8"
        mock_ser.in_waiting = True
        mock_ser.readline.return_value = b"invalid_data\n"
        mock_queue = Mock()

        with patch(
            "app.serial.get_current_serial_connection"
        ) as mock_get_current_serial, patch(
            "app.serial.serial_data_queue", mock_queue
        ), patch("app.serial.move_mouse") as mock_move_mouse:
            mock_get_current_serial.side_effect = [mock_ser, None]
            read_from_serial(mock_ser)

            mock_queue.put.assert_has_calls(
                [
                    call("Got data from {}: invalid_data\n".format(mock_ser.port)),
                    call(
                        "ERROR: error parsing above line, invalid data, error is: Data does not contain exactly two integers.\n"
                    ),
                ]
            )
            mock_move_mouse.assert_not_called()

    @patch("app.serial.list_ports.comports")
    def test_get_serial_ports_with_available_ports(self, mock_comports):
        # Simulate `list_ports.comports()` returning a list of available ports
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
        # Simulate `list_ports.comports()` returning an empty list, indicating no available ports
        mock_comports.return_value = []

        expected_ports = ["No Ports Available"]
        actual_ports = get_serial_ports()
        self.assertEqual(
            actual_ports,
            expected_ports,
            "Should return a message indicating no available ports",
        )

    def test_start_serial_thread_success(self):
        mock_serial = MagicMock(port="COM8")
        with patch(
            "app.serial.serial.Serial", mock_serial
        ), patch(
            "app.serial.disconnect_from_serial"
        ) as mock_disconnect, patch(
            "app.serial.threading.Thread"
        ) as mock_thread, patch("app.serial.serial_data_queue.put") as mock_queue_put:
            result = start_serial_thread("COM8", 9600)

            mock_disconnect.assert_called_once()
            mock_serial.assert_called_once_with("COM8", 9600, timeout=5)
            mock_thread.assert_called_once()
            mock_queue_put.assert_called()
            self.assertTrue(result)

    def test_start_serial_thread_failure(self):
        with patch(
            "app.serial.serial.Serial"
        ) as mock_serial, patch(
            "app.serial.disconnect_from_serial"
        ) as mock_disconnect, patch(
            "app.serial.serial_data_queue.put"
        ) as mock_queue_put:
            mock_serial.side_effect = serial.SerialException("Connection failed")

            result = start_serial_thread("COM8", 9600)

            mock_disconnect.assert_called_once()
            mock_serial.assert_called_once_with("COM8", 9600, timeout=5)
            mock_queue_put.assert_called()
            self.assertFalse(result)

    def test_disconnect_from_serial(self):
        disconnect_from_serial()
        mock_ser = Mock()
        mock_ser.port = "COM8"
        mock_queue = Mock()
        mock_queue.put.assert_not_called()

        with patch("app.serial.current_serial_connection", mock_ser):
            with patch("app.serial.serial_data_queue", mock_queue):
                disconnect_from_serial()

        mock_ser.close.assert_called_once()
        mock_queue.put.assert_called_once_with("Disconnected from COM8\n")


if __name__ == "__main__":
    unittest.main()
