import ctypes
from ctypes import Structure, c_int, c_uint32, c_char, POINTER
import itertools
from .utils import rgb_to_colorref, encode_label, sanitize_bounding_box
import time
from PIL import Image
from ultralytics import YOLO
from mss import mss

class DetectionBox(Structure):
    _fields_ = [
        ("id", c_int),
        ("x", c_int),
        ("y", c_int),
        ("width", c_int),
        ("height", c_int),
        ("color", c_uint32),      # COLORREF in 0x00BBGGRR format
        ("label", c_char * 50),   # Label for the detection
        ("lastSeen", c_uint32),   # DWORD (milliseconds since system start)
        ("paused", c_int)
    ]

def get_tick_count():
    """Retrieve the number of milliseconds that have elapsed since the system was started."""
    GetTickCount = ctypes.windll.kernel32.GetTickCount
    GetTickCount.restype = ctypes.c_uint32
    return GetTickCount()

def process_detections(model, overlay_dll, monitor_width, monitor_height, id_gen, conf_threshold):
    """Capture the screen, perform detection, and send results to the DLL."""
    with mss() as sct:
        while True:
            start_time = time.time()

            try:
                # Capture the screen
                screenshot = sct.grab({
                    "left": 0,
                    "top": 0,
                    "width": monitor_width,
                    "height": monitor_height
                })
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                # Perform YOLO detection
                results = model(img, verbose=False)

                # Prepare detection boxes
                detection_boxes = []
                current_tick = get_tick_count()

                for det in results[0].boxes:
                    if det.conf < conf_threshold:  # Filter out low-confidence detections
                        continue

                    # Extract bounding box coordinates
                    x1, y1, x2, y2 = map(int, det.xyxy[0])
                    width = x2 - x1
                    height = y2 - y1

                    # Get the label
                    cls_id = int(det.cls[0])
                    label = model.names[cls_id] if cls_id < len(model.names) else "Unknown"

                    # Define color (e.g., green)
                    color = rgb_to_colorref(0, 255, 0)  # Green in COLORREF

                    # Assign a unique ID
                    unique_id = next(id_gen)

                    # Sanitize bounding box
                    sanitized_x, sanitized_y, sanitized_width, sanitized_height = sanitize_bounding_box(
                        x1,
                        y1,
                        x2,
                        y2,
                        monitor_width,
                        monitor_height
                    )

                    # Create DetectionBox instance
                    detection_box = DetectionBox(
                        id=unique_id,
                        x=sanitized_x,
                        y=sanitized_y,
                        width=sanitized_width,
                        height=sanitized_height,
                        color=color,
                        label=encode_label(label),
                        lastSeen=current_tick,
                        paused=0
                    )

                    detection_boxes.append(detection_box)

                # Convert list to ctypes array
                if detection_boxes:
                    DetectionArray = DetectionBox * len(detection_boxes)
                    detections_ctypes = DetectionArray(*detection_boxes)

                    # Update detections in the DLL
                    overlay_dll.UpdateDetections(detections_ctypes, len(detection_boxes))
                    print(f"[INFO] Sent {len(detection_boxes)} detections to the overlay.")
                else:
                    print("[INFO] No detections to send.")

            except Exception as e:
                print(f"[ERROR] Error during detection processing: {e}")

            # Control the loop rate (e.g., 5 FPS)
            elapsed_time = time.time() - start_time
            sleep_time = max(0, (1/5) - elapsed_time)
            time.sleep(sleep_time)
