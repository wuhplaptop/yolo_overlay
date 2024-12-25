# tests/test_overlay.py

import unittest
from unittest.mock import patch, MagicMock
from yolo_overlay import YOLOOverlay
from pathlib import Path  # Importing Path from pathlib

class TestYOLOOverlay(unittest.TestCase):
    @patch('yolo_overlay.overlay.pkg_resources.path')
    @patch('yolo_overlay.overlay.get_monitors')  # Mocking get_monitors from screeninfo
    @patch('yolo_overlay.overlay.YOLO')
    @patch('yolo_overlay.overlay.ctypes.WinDLL')
    def test_initialization(self, mock_windll, mock_yolo, mock_get_monitors, mock_pkg_resources_path):
        """
        Test the successful initialization of YOLOOverlay with mocked dependencies.
        """
        # Mock the path context manager to return a fake DLL path
        mock_dll_path = MagicMock()
        mock_pkg_resources_path.return_value.__enter__.return_value = mock_dll_path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = 'resources/overlay-yolo.dll'

        # Mock the DLL loading
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance

        # Mock StartOverlay to return 0 (success)
        mock_dll_instance.StartOverlay.return_value = 0

        # Mock the YOLO model
        mock_model_instance = MagicMock()
        mock_yolo.return_value = mock_model_instance

        # Mock get_monitors to return a fake monitor
        mock_monitor = MagicMock()
        mock_monitor.x = 0
        mock_monitor.y = 0
        mock_monitor.width = 1920
        mock_monitor.height = 1080
        mock_monitor.width_mm = 509
        mock_monitor.height_mm = 286
        mock_monitor.name = '\\\\.\\DISPLAY1'
        mock_monitor.is_primary = True
        mock_get_monitors.return_value = [mock_monitor]

        # Initialize YOLOOverlay with mocked dependencies
        try:
            overlay = YOLOOverlay(
                model_path=r"writing50e11n.ptt",
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
            self.assertIsNotNone(overlay)
            
            # Verify that WinDLL was called with the correct DLL path
            mock_windll.assert_called_with('resources/overlay-yolo.dll')
            
            # Verify that YOLO was called with the correct model path
            mock_yolo.assert_called_with(r"writing50e11n.pt")
            
            # Verify that SetTargetMonitorRect was called with correct parameters
            mock_dll_instance.SetTargetMonitorRect.assert_called_with(
                mock_monitor.x,
                mock_monitor.y,
                mock_monitor.x + mock_monitor.width,
                mock_monitor.y + mock_monitor.height
            )
            
            # Verify that SetMaxDetections was called with correct parameter
            mock_dll_instance.SetMaxDetections.assert_called_with(100)
            
            # Verify that StartOverlay was called
            mock_dll_instance.StartOverlay.assert_called_once()
            
            # Stop the overlay
            overlay.stop()
            
            # Verify that StopOverlay was called
            mock_dll_instance.StopOverlay.assert_called_once()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

    @patch('yolo_overlay.overlay.pkg_resources.path')
    @patch('yolo_overlay.overlay.get_monitors')  # Mocking get_monitors from screeninfo
    @patch('yolo_overlay.overlay.YOLO')
    @patch('yolo_overlay.overlay.ctypes.WinDLL')
    def test_initialization_with_invalid_model_path(self, mock_windll, mock_yolo, mock_get_monitors, mock_pkg_resources_path):
        """
        Test the initialization of YOLOOverlay with an invalid model path.
        Expect the program to exit gracefully.
        """
        # Mock the path context manager to return a fake DLL path
        mock_dll_path = MagicMock()
        mock_pkg_resources_path.return_value.__enter__.return_value = mock_dll_path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = 'path/to/overlay-yolo.dll'

        # Mock the DLL loading
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance

        # Mock get_monitors to return a fake monitor
        mock_monitor = MagicMock()
        mock_monitor.x = 0
        mock_monitor.y = 0
        mock_monitor.width = 1920
        mock_monitor.height = 1080
        mock_monitor.width_mm = 509
        mock_monitor.height_mm = 286
        mock_monitor.name = '\\\\.\\DISPLAY1'
        mock_monitor.is_primary = True
        mock_get_monitors.return_value = [mock_monitor]

        # Mock the YOLO model to raise an exception when initialized with invalid path
        mock_yolo.side_effect = Exception("Model file not found.")

        # Since the constructor will call sys.exit(1), we need to handle it
        with self.assertRaises(SystemExit) as cm:
            overlay = YOLOOverlay(
                model_path=r"C:\invalid\path\to\model.pt",
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
        self.assertEqual(cm.exception.code, 1)
        
        # Verify that StopOverlay was called even after failure
        mock_dll_instance.StopOverlay.assert_called_once()

if __name__ == '__main__':
    unittest.main()
