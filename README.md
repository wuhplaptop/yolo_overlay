
# YOLO Overlay

YOLO Overlay is a Python package that combines YOLO object detection and a custom DLL written in C to overlay real-time detection boxes on a Windows display. This project is ideal for applications requiring on-screen visualization of YOLO detections in real-time, such as live monitoring, gaming, or augmented reality scenarios.

The project utilizes:
- **YOLOv8** for object detection.
- **MSS** for screen capturing.
- A **custom C DLL** to create an overlay window and render detection boxes on the user's display.

---

## Features
- Real-time YOLO detections directly overlaid on your display.
- Adjustable confidence thresholds and bounding box limits.
- Supports multiple monitors with custom resolutions.
- Lightweight and efficient implementation leveraging ctypes and a DLL.

---

## Installation
1. **Install the Python Package:**
   ```bash
   pip install yolo-overlay
   ```

2. **Ensure the Required DLL File:**
   The `overlay-yolo.dll` file is included in the package and is automatically loaded. If you want to use a custom DLL, ensure it's accessible in your system path or specify its path during initialization.

3. **Install Required Python Dependencies:**
   The required dependencies are automatically installed with the package. These include:
   - `ultralytics`
   - `mss`
   - `Pillow`
   - `screeninfo`

---

## Usage
### Basic Example
```python
from yolo_overlay import YOLOOverlay

# Path to YOLO model
model_path = "path/to/yolo_model.pt"

# Initialize YOLO overlay
overlay = YOLOOverlay(
    model_path=model_path,
    dll_path=None,  # Optional custom DLL path
    max_detections=100,
    conf_threshold=0.5,
    monitor_index=0  # Use the primary monitor
)

try:
    print("Running YOLO Overlay. Press Ctrl+C to stop.")
    while True:
        pass  # Keep the script running
except KeyboardInterrupt:
    overlay.stop()
```

---

## Required Files
1. **DLL File:**
   - `overlay-yolo.dll`: This file is used to create the overlay window and handle rendering. The default file is included in the package under the `resources` folder.

2. **Python Files:**
   - `detection.py`: Handles detection processing and communicates with the DLL.
   - `overlay.py`: Manages the overlay lifecycle and threading.
   - `utils.py`: Utility functions for color encoding, bounding box sanitization, and label encoding.

---

## Documentation
### Functions
- **`YOLOOverlay` Class**
  - `__init__(model_path, dll_path=None, max_detections=100, conf_threshold=0.5, monitor_index=0)`: Initializes the overlay.
  - `stop()`: Stops the overlay.

- **`DetectionBox` (C Structure)**
  - Contains fields for detection ID, coordinates, dimensions, color, label, and more.

- **DLL Exported Functions**
  - `StartOverlay()`: Starts the overlay.
  - `StopOverlay()`: Stops the overlay.
  - `UpdateDetections(DetectionBox*, int)`: Updates detections on the overlay.
  - `SetTargetMonitorRect(int, int, int, int)`: Sets the target monitor dimensions.
  - `SetMaxDetections(int)`: Adjusts the maximum number of detections.

### Configuration
- **Confidence Threshold:** Adjust using the `conf_threshold` parameter.
- **Monitor Selection:** Use `monitor_index` to select which monitor to target.
- **Max Detections:** Configure with the `max_detections` parameter or through the DLL API.

---

## Development Notes
- **Operating System:** Windows-only due to the use of Windows APIs for rendering the overlay.
- **Model Support:** Ensure you have a valid `.pt` file trained with YOLO.
- **Python Version:** Python 3.8 or later.

---

## Troubleshooting
- **No Overlay Displayed:**
  - Ensure your system meets the requirements (Windows OS).
  - Verify the DLL file path.
  - Check if the monitor index is correct.

- **Performance Issues:**
  - Lower the detection confidence threshold.
  - Optimize the YOLO model by using a lightweight version.


