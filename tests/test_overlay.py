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
        """
        Test the successful initialization of YOLOOverlay with mocked dependencies.
        """
        expected_model_path = "resources/writing50e11n.pt"
        expected_dll_path = "resources/overlay-yolo.dll"

        # Mock DLL path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = expected_dll_path

        # Mock DLL instance
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance
        mock_dll_instance.StartOverlay.return_value = 0

        # Mock YOLO model
        mock_model_instance = MagicMock()
        mock_yolo.return_value = mock_model_instance

        # Mock monitor
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

            # Debug the call arguments for YOLO
            print(f"[DEBUG] mock_yolo call args: {mock_yolo.call_args}")
            self.assertIsNotNone(overlay)

            # Assert the YOLO model was called with the correct path
            mock_yolo.assert_called_with(expected_model_path)

            overlay.stop()
            mock_dll_instance.StopOverlay.assert_called_once()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

    @patch('yolo_overlay.overlay.pkg_resources.path')
    def test_model_path_integrity(self, mock_pkg_resources_path):
        """
        Ensure that the model path is not modified during initialization.
        """
        expected_model_path = "resources/writing50e11n.pt"
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = "resources/overlay-yolo.dll"

        try:
            overlay = YOLOOverlay(model_path=expected_model_path)
            self.assertEqual(overlay.model_path, expected_model_path, "Model path was altered during initialization.")
            print(f"[DEBUG] Model path integrity test passed: {overlay.model_path}")
        except Exception as e:
            self.fail(f"Model path integrity test failed with exception: {e}")


if __name__ == "__main__":
    unittest.main()
