import unittest
import os
from yolo_overlay import YOLOOverlay

class TestYOLOOverlay(unittest.TestCase):
    def setUp(self):
        """
        Set up the file paths for testing.
        """
        self.model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../yolo_overlay/resources/writing50e11n.pt")
        )
        self.dll_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../yolo_overlay/resources/overlay-yolo.dll")
        )

    def test_initialization(self):
        """
        Test the successful initialization of YOLOOverlay with actual file paths.
        """
        self.assertTrue(os.path.exists(self.model_path), f"Model file does not exist: {self.model_path}")
        self.assertTrue(os.path.exists(self.dll_path), f"DLL file does not exist: {self.dll_path}")

        try:
            overlay = YOLOOverlay(
                model_path=self.model_path,
                dll_path=self.dll_path,
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
            self.assertIsNotNone(overlay)
            overlay.stop()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

    def test_model_path_integrity(self):
        """
        Ensure the model path is not altered during initialization.
        """
        self.assertTrue(os.path.exists(self.model_path), f"Model file does not exist: {self.model_path}")
        self.assertTrue(os.path.exists(self.dll_path), f"DLL file does not exist: {self.dll_path}")

        try:
            overlay = YOLOOverlay(model_path=self.model_path, dll_path=self.dll_path)
            self.assertEqual(overlay.model_path, self.model_path, "Model path was altered.")
        except Exception as e:
            self.fail(f"Model path integrity test failed with exception: {e}")


if __name__ == "__main__":
    unittest.main()
