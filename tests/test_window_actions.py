import unittest
from unittest.mock import patch

from app.window_actions import (
    move_mouse_randomly,
    move_mouse,
    viewport_size,
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


if __name__ == "__main__":
    unittest.main()
