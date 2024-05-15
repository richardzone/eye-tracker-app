import unittest
from unittest.mock import patch, MagicMock

from app.window_actions import (
    show_calibration_dot,
    hide_calibration_dot,
    calibration_dot_window,
    viewport_size,
    move_mouse_randomly,
    move_mouse,
)


class TestWindowActions(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        patch.stopall()

    def test_move_mouse_randomly(self):
        with patch("app.window_actions.random.randint") as mock_randint:
            with patch("app.window_actions.viewport_size", return_value=(800, 600)):
                with patch("app.window_actions.move_mouse") as mock_move_mouse:
                    mock_randint.side_effect = [100, 200]
                    move_mouse_randomly(0.5)
                    mock_move_mouse.assert_called_with(100, 200, 0.5)

    def test_move_mouse_valid_coordinates(self):
        with patch("app.window_actions.viewport_size", return_value=(800, 600)):
            with patch("app.window_actions.pyautogui.moveTo") as mock_moveTo:
                move_mouse(100, 200, 0.3)
                mock_moveTo.assert_called_with(100, 200, 0.3)

    def test_move_mouse_invalid_coordinates(self):
        with patch("app.window_actions.viewport_size", return_value=(800, 600)):
            with self.assertRaises(ValueError):
                move_mouse(-100, 200, 0.3)
            with self.assertRaises(ValueError):
                move_mouse(100, 800, 0.3)
            with self.assertRaises(ValueError):
                move_mouse("invalid", 200, 0.3)
                move_mouse(100, "invalid", 0.3)

    def test_viewport_size(self):
        with patch("app.window_actions.pyautogui.size", return_value=(1920, 1080)):
            width, height = viewport_size()
            self.assertEqual(width, 1920)
            self.assertEqual(height, 1080)

    @patch("app.window_actions.viewport_size", return_value=(800, 600))
    def test_show_calibration_dot(self, mock_viewport_size):
        with patch("app.window_actions.tk.Toplevel", new_callable=MagicMock) as mock_Toplevel:
            show_calibration_dot()
            mock_Toplevel.assert_called_once()
            instance = mock_Toplevel.return_value
            instance.overrideredirect.assert_called_once_with(True)
            instance.geometry.assert_called_once_with("50x50+375+275")
            instance.attributes.assert_any_call("-topmost", True)
            instance.configure.assert_called_once_with(bg='red')

    @patch("app.window_actions.calibration_dot_window", new_callable=MagicMock)
    def test_hide_calibration_dot(self, mock_calibration_dot_window):
        instance = mock_calibration_dot_window
        hide_calibration_dot()
        instance.destroy.assert_called_once()
        self.assertIsNone(calibration_dot_window)

    @patch("app.window_actions.calibration_dot_window", None)
    def test_hide_calibration_dot_when_not_visible(self):
        hide_calibration_dot()  # Should not raise an exception or call destroy
        self.assertIsNone(calibration_dot_window)



if __name__ == "__main__":
    unittest.main()
