import unittest
from unittest.mock import patch, Mock, MagicMock
import cv2
import cv2.aruco as aruco
import threading
import numpy as np
from PIL import ImageTk

from app.video_capture import (
    convert_aruco_marker_ids_to_coordinates,
    detect_aruco_markers,
    get_video_devices,
    start_video_thread,
    stop_video_capture,
    read_from_video_device,
    get_current_video_device,
)

class TestVideoCapture(unittest.TestCase):

    def test_convert_aruco_marker_ids_to_coordinates(self):
        self.assertEqual(convert_aruco_marker_ids_to_coordinates([1, 2, 3, 4]), (102, 304))
        self.assertEqual(convert_aruco_marker_ids_to_coordinates([0, 0, 0, 0]), (0, 0))
        self.assertEqual(convert_aruco_marker_ids_to_coordinates([1, 2, 3]), (None, None))

    @patch("app.video_capture.aruco.detectMarkers")
    def test_detect_aruco_markers(self, mock_detectMarkers):
        img = MagicMock()
        dictionary = aruco.DICT_6X6_100
        mock_detectMarkers.return_value = (
            [np.array([[[0, 0]], [[1, 0]], [[1, 1]], [[0, 1]]]) for _ in range(4)],
            np.array([[1], [2], [3], [4]]),
            Mock()
        )
        marker_ids = detect_aruco_markers(img, dictionary)
        self.assertEqual(marker_ids, [1, 2, 3, 4])

        mock_detectMarkers.return_value = ([], None, Mock())
        marker_ids = detect_aruco_markers(img, dictionary)
        self.assertEqual(marker_ids, [])

    @patch("cv2.VideoCapture")
    def test_get_video_devices(self, mock_VideoCapture):
        mock_cap = Mock()
        mock_VideoCapture.return_value = mock_cap

        # Provide enough values to cover all iterations of the loop (10 times)
        side_effect_values = [(True, Mock())] * 3

        # Append an additional value to simulate the situation when no more video devices are available
        side_effect_values.extend([(False, Mock())] * 7)

        mock_cap.read.side_effect = side_effect_values

        video_device_indices = get_video_devices()
        self.assertEqual(video_device_indices, [0, 1, 2])

    @patch("cv2.VideoCapture")
    def test_stop_video_capture(self, mock_VideoCapture):
        mock_cap = Mock()
        mock_VideoCapture.return_value = mock_cap
        mock_cap.isOpened.return_value = True

        global current_video_device
        current_video_device = mock_cap

        stop_video_capture()
        self.assertTrue(mock_cap.release.called)

    @patch("cv2.VideoCapture")
    @patch("app.video_capture.detect_aruco_markers")
    @patch("app.video_capture.convert_aruco_marker_ids_to_coordinates")
    @patch("app.video_capture.move_mouse")
    @patch("PIL.Image.fromarray")
    @patch("app.video_capture.get_current_video_device")
    def test_read_from_video_device(self, mock_get_current_video_device, mock_fromarray, mock_move_mouse,
                                    mock_convert_aruco_marker_ids_to_coordinates, mock_detect_aruco_markers,
                                    mock_video_capture):
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)  # Creating a dummy frame
        mock_cap.read.return_value = (True, mock_frame)

        mock_get_current_video_device.return_value = mock_cap
        mock_convert_aruco_marker_ids_to_coordinates.return_value = (100, 200)
        mock_fromarray.return_value.size = (1920, 1080)  # Set a size for the mock image

        canvas = MagicMock()
        stop_event = threading.Event()
        stop_event.clear()

        read_from_video_device(0, canvas)
        self.assertTrue(mock_cap.read.called)
        mock_detect_aruco_markers.assert_called_once()
        mock_convert_aruco_marker_ids_to_coordinates.assert_called_once()
        mock_move_mouse.assert_called_once_with(100, 200)
        self.assertTrue(canvas.create_image.called)

if __name__ == '__main__':
    unittest.main()
