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
        # Expected paths for model and DLL
        expected_model_path = "resources/writing50e11n.pt"
        expected_dll_path = "resources/overlay-yolo.dll"

        # Mock the DLL path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = expected_dll_path

        # Mock the DLL instance
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance
        mock_dll_instance.StartOverlay.return_value = 0  # Simulate successful overlay start

        # Mock the YOLO model
        mock_model_instance = MagicMock()
        mock_yolo.return_value = mock_model_instance

        # Mock the monitor
        mock_monitor = MagicMock()
        mock_monitor.x = 0
        mock_monitor.y = 0
        mock_monitor.width = 1920
        mock_monitor.height = 1080
        mock_get_monitors.return_value = [mock_monitor]

        try:
            # Initialize the overlay with the expected model path
            overlay = YOLOOverlay(
                model_path=expected_model_path,
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
            self.assertIsNotNone(overlay)

            # Debug: Print mock YOLO call arguments
            print(f"[DEBUG] YOLO was called with: {mock_yolo.call_args}")

            # Assert the YOLO model was called with the correct path
            mock_yolo.assert_called_with(expected_model_path)

            # Stop the overlay and assert the DLL method was called
            overlay.stop()
            mock_dll_instance.StopOverlay.assert_called_once()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

    @patch('yolo_overlay.overlay.pkg_resources.path')
    def test_model_path_check(self, mock_pkg_resources_path):
        """
        Verify the model path used in YOLOOverlay is correct and does not contain typos.
        """
        # Expected path for the model
        expected_model_path = "resources/writing50e11n.pt"
        
        # Mock the DLL path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = "resources/overlay-yolo.dll"
        
        try:
            # Initialize the overlay
            overlay = YOLOOverlay(model_path=expected_model_path)
            self.assertTrue(overlay.model_path.endswith('.pt'), "Model file should end with .pt")
            self.assertEqual(overlay.model_path, expected_model_path, "Model path mismatch")
            print(f"[DEBUG] Model path verified: {overlay.model_path}")
        except Exception as e:
            self.fail(f"Model path check failed with exception: {e}")


if __name__ == "__main__":
    unittest.main()
