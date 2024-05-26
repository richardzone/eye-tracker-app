import unittest
from unittest.mock import patch, Mock, MagicMock
import cv2
import cv2.aruco as aruco
import threading
import numpy as np
from PIL import ImageTk, Image
import tkinter

from app.video_capture import (
    convert_aruco_marker_ids_to_coordinates,
    detect_aruco_markers,
    get_video_devices,
    start_video_thread,
    stop_video_capture,
    read_from_video_device,
    get_current_video_device,
    draw_video_image_to_canvas
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
    def test_get_video_devices(self, mock_video_capture):
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap

        # Provide enough values to cover all iterations of the loop (10 times)
        side_effect_values = [(True, Mock())] * 3

        # Append an additional value to simulate the situation when no more video devices are available
        side_effect_values.extend([(False, Mock())] * 7)

        mock_cap.read.side_effect = side_effect_values

        video_device_indices = get_video_devices()
        self.assertEqual(video_device_indices, [0, 1, 2])

    @patch("time.sleep")
    def test_stop_video_capture(self, mock_sleep):
        # Mock the current_video_device and stop_event
        mock_current_video_device = Mock()
        mock_stop_event = threading.Event()

        # Ensure stop_event is initialized
        mock_stop_event.clear()

        with patch("app.video_capture.current_video_device", mock_current_video_device), \
            patch("app.video_capture.stop_event", mock_stop_event):
            stop_video_capture()
            self.assertTrue(mock_stop_event.is_set())
            mock_sleep.assert_called_once_with(1)
            self.assertTrue(mock_current_video_device.release.called)

    @patch("threading.Thread")
    @patch("app.video_capture.stop_video_capture")
    def test_start_video_thread(self, mock_stop_video_capture, mock_thread):
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        canvas = MagicMock()
        result = start_video_thread(0, canvas)

        self.assertTrue(result)
        mock_stop_video_capture.assert_called_once()
        mock_thread.assert_called_once_with(target=read_from_video_device, args=(0, canvas), daemon=True)
        mock_thread_instance.start.assert_called_once()

    @patch("cv2.VideoCapture")
    @patch("app.video_capture.detect_aruco_markers")
    @patch("app.video_capture.convert_aruco_marker_ids_to_coordinates")
    @patch("app.video_capture.move_mouse")
    @patch("PIL.Image.fromarray")
    @patch("app.video_capture.get_current_video_device")
    @patch("app.video_capture.draw_video_image_to_canvas")
    def test_read_from_video_device(self, mock_draw_video_image_to_canvas, mock_get_current_video_device,
                                    mock_fromarray, mock_move_mouse,
                                    mock_convert_aruco_marker_ids_to_coordinates, mock_detect_aruco_markers,
                                    mock_video_capture):
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)  # Creating a dummy frame
        mock_cap.read.return_value = (True, mock_frame)

        mock_get_current_video_device.return_value = mock_cap
        mock_convert_aruco_marker_ids_to_coordinates.return_value = (100, 200)

        # Create a mock image with a valid mode
        mock_img_pil = Mock(spec=Image.Image)
        mock_img_pil.mode = 'RGB'
        mock_fromarray.return_value = mock_img_pil

        canvas = MagicMock()
        stop_event = threading.Event()
        stop_event.clear()

        with patch("app.video_capture.current_video_device", mock_cap), \
            patch("app.video_capture.stop_event", stop_event):

            read_from_video_device(0, canvas)
            self.assertTrue(mock_cap.read.called)
            mock_detect_aruco_markers.assert_called()
            mock_convert_aruco_marker_ids_to_coordinates.assert_called()
            mock_move_mouse.assert_called()
            mock_draw_video_image_to_canvas.assert_called()

    @patch("PIL.ImageTk.PhotoImage")
    @patch("PIL.Image.fromarray")
    def test_draw_video_image_to_canvas(self, mock_fromarray, mock_photoimage):
        mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)  # Creating a dummy frame
        mock_img_pil = Mock(spec=Image.Image)
        mock_fromarray.return_value = mock_img_pil
        mock_img_tk = Mock()
        mock_photoimage.return_value = mock_img_tk

        canvas = MagicMock()
        draw_video_image_to_canvas(mock_frame, canvas)

        mock_fromarray.assert_called_once()
        mock_photoimage.assert_called_once()
        canvas.create_image.assert_called_once_with(0, 0, anchor=tkinter.NW, image=mock_img_tk)
        self.assertEqual(canvas.img_tk, mock_img_tk)


if __name__ == '__main__':
    unittest.main()
