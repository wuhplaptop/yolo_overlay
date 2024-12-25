import unittest
from unittest.mock import patch, MagicMock
from ultralytics import YOLO
from yolo_overlay import YOLOOverlay

class TestYOLOOverlay(unittest.TestCase):

    @patch('yolo_overlay.overlay.pkg_resources.path')
    @patch('yolo_overlay.overlay.get_monitors')
    @patch('yolo_overlay.overlay.YOLO')
    @patch('yolo_overlay.overlay.ctypes.WinDLL')
    def test_initialization(self, mock_windll, mock_yolo, mock_get_monitors, mock_pkg_resources_path):
        expected_model_path = "resources/writing50e11n.pt"
        expected_dll_path = "resources/overlay-yolo.dll"

        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = expected_dll_path
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance
        mock_dll_instance.StartOverlay.return_value = 0

        mock_model_instance = MagicMock()
        mock_yolo.return_value = mock_model_instance

        mock_monitor = MagicMock()
        mock_monitor.x = 0
        mock_monitor.y = 0
        mock_monitor.width = 1920
        mock_monitor.height = 1080
        mock_get_monitors.return_value = [mock_monitor]

        try:
            overlay = YOLOOverlay(
                model_path=expected_model_path,
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
            self.assertIsNotNone(overlay)
            mock_yolo.assert_called_with(expected_model_path)
            overlay.stop()
            mock_dll_instance.StopOverlay.assert_called_once()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

if __name__ == "__main__":
    unittest.main()
