import unittest
import os
import requests
from unittest.mock import patch, MagicMock
from ultralytics import YOLO  # Ensure the ultralytics library is available for YOLO detection
from yolo_overlay import YOLOOverlay  # Import the actual class being tested

MODEL_URL = "https://github.com/wuhplaptop/yolo_overlay/raw/main/resources/writing50e11n.pt"
MODEL_PATH = "resources/writing50e11n.pt"

# Helper function to download the model if it doesn't exist
def download_model():
    if not os.path.exists(MODEL_PATH):
        print(f"[INFO] Downloading model from {MODEL_URL}...")
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        response = requests.get(MODEL_URL)
        if response.status_code == 200:
            with open(MODEL_PATH, 'wb') as f:
                f.write(response.content)
            print("[INFO] Model downloaded successfully.")
        else:
            raise RuntimeError(f"Failed to download model. Status code: {response.status_code}")

class TestYOLOOverlay(unittest.TestCase):

    @patch('yolo_overlay.overlay.pkg_resources.path')
    @patch('yolo_overlay.overlay.get_monitors')  # Mocking get_monitors from screeninfo
    @patch('yolo_overlay.overlay.YOLO')
    @patch('yolo_overlay.overlay.ctypes.WinDLL')
    def test_initialization(self, mock_windll, mock_yolo, mock_get_monitors, mock_pkg_resources_path):
        """
        Test the successful initialization of YOLOOverlay with mocked dependencies.
        """
        # Ensure model is downloaded
        download_model()

        # Correct paths
        expected_model_path = MODEL_PATH  # Ensure proper extension for YOLO model file
        expected_dll_path = "resources/overlay-yolo.dll"

        # Mock DLL path
        mock_dll_path = MagicMock()
        mock_pkg_resources_path.return_value.__enter__.return_value = mock_dll_path
        mock_pkg_resources_path.return_value.__enter__.return_value.__str__.return_value = expected_dll_path

        # Mock DLL
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
            self.assertIsNotNone(overlay)

            # Verify DLL path
            mock_windll.assert_called_with(expected_dll_path)

            # Verify YOLO model initialization
            print(f"[DEBUG] Mock YOLO calls: {mock_yolo.call_args_list}")  # Debug statement for test
            mock_yolo.assert_called_with(expected_model_path)  # Match expected path

            overlay.stop()
            mock_dll_instance.StopOverlay.assert_called_once()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

if __name__ == "__main__":
    unittest.main()
