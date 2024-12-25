import unittest
from yolo_overlay import YOLOOverlay
import os

class TestYOLOOverlay(unittest.TestCase):

    def test_initialization(self):
        """
        Test the successful initialization of YOLOOverlay with actual file paths.
        """
        model_path = "resources/writing50e11n.pt"
        dll_path = "resources/overlay-yolo.dll"

        self.assertTrue(os.path.exists(model_path), f"Model file does not exist: {model_path}")
        self.assertTrue(os.path.exists(dll_path), f"DLL file does not exist: {dll_path}")

        try:
            overlay = YOLOOverlay(
                model_path=model_path,
                dll_path=dll_path,
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
        model_path = "resources/writing50e11n.pt"
        self.assertTrue(os.path.exists(model_path), f"Model file does not exist: {model_path}")

        try:
            overlay = YOLOOverlay(model_path=model_path)
            self.assertEqual(overlay.model_path, model_path, "Model path was altered.")
        except Exception as e:
            self.fail(f"Model path integrity test failed with exception: {e}")


if __name__ == "__main__":
    unittest.main()
