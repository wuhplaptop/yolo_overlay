# tests/test_overlay.py

import unittest
from yolo_overlay import YOLOOverlay

class TestYOLOOverlay(unittest.TestCase):
    def test_initialization(self):
        try:
            overlay = YOLOOverlay(
                model_path=r"C:\path\to\your-model.pt",
                max_detections=100,
                conf_threshold=0.5,
                monitor_index=0
            )
            self.assertIsNotNone(overlay)
            overlay.stop()
        except Exception as e:
            self.fail(f"Initialization failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()
