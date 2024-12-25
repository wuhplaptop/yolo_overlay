import unittest
from unittest.mock import patch, MagicMock
from yolo_overlay import YOLOOverlay
import os

class TestYOLOOverlay(unittest.TestCase):

    @patch('yolo_overlay.overlay.get_monitors')
    @patch('yolo_overlay.overlay.ctypes.WinDLL')
    def test_initialization(self, mock_windll, mock_get_monitors):
        """
        Test the successful initialization of YOLOOverlay without mocking the model path.
        """
        # Define the actual paths for testing
        model_path = "resources/writing50e11n.pt"
        dll_path = "resources/overlay-yolo.dll"

        # Ensure the model and DLL exist
        self.assertTrue(os.path.exists(model_path), f"Model file does not exist: {model_path}")
        self.assertTrue(os.path.exists(dll_path), f"DLL file does not exist: {dll_path}")

        # Mock DLL instance
        mock_dll_instance = MagicMock()
        mock_windll.return_value = mock_dll_instance
        mock_dll_instance.StartOverlay.return_value = 0

        # Mock monitor
        mock_monitor = MagicMock()
        mock_monitor.x = 0
        mock_monitor.y = 0
        mock_monitor.width = 1920
        mock_monitor.height = 1080
        mock_get_monitors.return_value = [mock_monitor]

        try:
            overlay = YOLOOverlay(
                model_path=model_path,
                dll_path=dll_path,
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )

            self.assertIsNotNone(overlay)
            print(f"[DEBUG] Model path used: {overlay.model_path}")

            overlay.stop()
            mock_dll_instance.StopOverlay.assert_called_once()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

    def test_model_path_integrity(self):
        """
        Ensure that the model path is correctly passed to YOLOOverlay without alteration.
        """
        model_path = "resources/writing50e11n.pt"

        # Check that the model file exists
        self.assertTrue(os.path.exists(model_path), f"Model file does not exist: {model_path}")

        try:
            overlay = YOLOOverlay(model_path=model_path)
            self.assertEqual(overlay.model_path, model_path, "Model path was altered during initialization.")
            print(f"[DEBUG] Model path integrity test passed: {overlay.model_path}")
        except Exception as e:
            self.fail(f"Model path integrity test failed with exception: {e}")


if __name__ == "__main__":
    unittest.main()
