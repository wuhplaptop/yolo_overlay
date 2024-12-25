# tests/test_overlay.py

import unittest
from unittest.mock import patch, MagicMock
from yolo_overlay import YOLOOverlay
from pathlib import Path  # Importing Path from pathlib

class TestYOLOOverlay(unittest.TestCase):
    @patch('yolo_overlay.overlay.pkg_resources.path')
    @patch('yolo_overlay.overlay.YOLO')
    @patch('yolo_overlay.overlay.ctypes.WinDLL')
    def test_initialization(self, mock_windll, mock_yolo, mock_pkg_resources_path):
        # Mock the path context manager to return a fake DLL path
        mock_dll_path = MagicMock()
        mock_pkg_resources_path.return_value.__enter__.return_value = mock_dll_path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = 'path/to/overlay-yolo.dll'

        # Mock the DLL loading
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance

        # Mock the YOLO model
        mock_model_instance = MagicMock()
        mock_yolo.return_value = mock_model_instance

        # Initialize YOLOOverlay with mocked dependencies
        try:
            overlay = YOLOOverlay(
                model_path=r"C:\path\to\your-model.pt",
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
            self.assertIsNotNone(overlay)
            # Verify that WinDLL was called with the correct DLL path
            mock_windll.assert_called_with('path/to/overlay-yolo.dll')
            # Verify that YOLO was called with the correct model path
            mock_yolo.assert_called_with(r"C:\path\to\your-model.pt")
            # Stop the overlay
            overlay.stop()
            # Verify that StopOverlay was called
            mock_dll_instance.StopOverlay.assert_called_once()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

    @patch('yolo_overlay.overlay.pkg_resources.path')
    @patch('yolo_overlay.overlay.YOLO')
    @patch('yolo_overlay.overlay.ctypes.WinDLL')
    def test_initialization_with_invalid_model_path(self, mock_windll, mock_yolo, mock_pkg_resources_path):
        # Mock the path context manager to return a fake DLL path
        mock_dll_path = MagicMock()
        mock_pkg_resources_path.return_value.__enter__.return_value = mock_dll_path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = 'path/to/overlay-yolo.dll'

        # Mock the DLL loading
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance

        # Mock the YOLO model to raise an exception when initialized with invalid path
        mock_yolo.side_effect = Exception("Model file not found.")

        with self.assertRaises(SystemExit) as cm:
            overlay = YOLOOverlay(
                model_path=r"C:\invalid\path\to\model.pt",
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
