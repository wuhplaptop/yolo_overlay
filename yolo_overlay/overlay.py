import ctypes
from ctypes import wintypes
import threading
import itertools
import sys
import time
from .detection import DetectionBox, process_detections
from .utils import rgb_to_colorref, encode_label
from mss import mss
from ultralytics import YOLO
from screeninfo import get_monitors
from PIL import Image
import os
from pathlib import Path
import platform

class YOLOOverlay:
    def __init__(self, model_path, dll_path=None, max_detections=100, conf_threshold=0.5, monitor_index=0):
        if platform.system() != 'Windows':
            raise OSError("YOLO Overlay is only supported on Windows systems.")
        
        if dll_path is None:
            # Locate the DLL within the package
            current_dir = Path(__file__).parent
            dll_path = current_dir / 'resources' / 'overlay-yolo.dll'
            dll_path = str(dll_path.resolve())
        
        self.dll_path = dll_path
        self.model_path = model_path
        self.max_detections = max_detections
        self.conf_threshold = conf_threshold
        self.monitor_index = monitor_index
        self.overlay_dll = None
        self.model = None
        self.monitor = None
        self.monitor_width = 0
        self.monitor_height = 0
        self.id_gen = itertools.count(1)
        self.detection_thread = None

        self._load_dll()
        self._load_model()
        self._select_monitor()
        self._initialize_overlay()

    def _load_dll(self):
        try:
            self.overlay_dll = ctypes.WinDLL(self.dll_path)
            # Setup DLL functions
            self.overlay_dll.UpdateDetections.argtypes = [ctypes.POINTER(DetectionBox), ctypes.c_int]
            self.overlay_dll.UpdateDetections.restype = None
            self.overlay_dll.StartOverlay.restype = ctypes.c_int
            self.overlay_dll.StopOverlay.restype = None
            self.overlay_dll.SetTargetMonitorRect.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.overlay_dll.SetTargetMonitorRect.restype = None
            self.overlay_dll.SetMaxDetections.argtypes = [ctypes.c_int]
            self.overlay_dll.SetMaxDetections.restype = None

            print("[INFO] DLL loaded and functions configured successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load DLL: {e}")
            sys.exit(1)

    def _load_model(self):
        if self.model_path is None:
            print("[ERROR] YOLO model path not provided.")
            self.stop()
            sys.exit(1)
        
        try:
            self.model = YOLO(self.model_path)
            print("[INFO] YOLO model loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO model: {e}")
            self.stop()
            sys.exit(1)

    def _select_monitor(self):
        monitors = get_monitors()
        if not monitors:
            print("[ERROR] No monitors detected.")
            sys.exit(1)

        if self.monitor_index < 0 or self.monitor_index >= len(monitors):
            print(f"[WARNING] Monitor index {self.monitor_index} out of range. Using monitor 0.")
            self.monitor_index = 0

        self.monitor = monitors[self.monitor_index]
        print(f"[INFO] Selected monitor {self.monitor_index}: {self.monitor}")

    def _initialize_overlay(self):
        monitor_x_offset = self.monitor.x
        monitor_y_offset = self.monitor.y
        self.monitor_width = self.monitor.width
        self.monitor_height = self.monitor.height

        # Set the target monitor rectangle in the DLL
        self.overlay_dll.SetTargetMonitorRect(
            monitor_x_offset,
            monitor_y_offset,
            monitor_x_offset + self.monitor_width,
            monitor_y_offset + self.monitor_height
        )
        print(f"[INFO] Set target monitor rectangle to: Left={monitor_x_offset}, Top={monitor_y_offset}, "
              f"Right={monitor_x_offset + self.monitor_width}, Bottom={monitor_y_offset + self.monitor_height}")

        # Set the maximum number of detections
        self.overlay_dll.SetMaxDetections(self.max_detections)
        print(f"[INFO] Set maximum detections to: {self.max_detections}")

        # Start the overlay
        start_result = self.overlay_dll.StartOverlay()
        if start_result != 0:
            print("[ERROR] Failed to start the overlay.")
            sys.exit(1)
        else:
            print("[INFO] Overlay started successfully.")

        # Start the detection thread
        self.detection_thread = threading.Thread(
            target=process_detections,
            args=(self.model, self.overlay_dll, self.monitor_width, self.monitor_height, self.id_gen, self.conf_threshold),
            daemon=True
        )
        self.detection_thread.start()
        print("[INFO] Detection thread started.")

    def update_settings(self, max_detections=None, conf_threshold=None):
        """Update overlay settings dynamically."""
        if max_detections is not None:
            self.max_detections = max_detections
            self.overlay_dll.SetMaxDetections(self.max_detections)
            print(f"[INFO] Updated maximum detections to: {self.max_detections}")

        if conf_threshold is not None:
            self.conf_threshold = conf_threshold
            # Note: To update the confidence threshold, you'd need to adjust the detection thread
            # This could involve passing the new threshold to the thread or restarting it
            # For simplicity, this is left as a placeholder
            print(f"[INFO] Updated confidence threshold to: {self.conf_threshold}")

    def stop(self):
        if self.overlay_dll:
            self.overlay_dll.StopOverlay()
            print("[INFO] Overlay stopped.")
