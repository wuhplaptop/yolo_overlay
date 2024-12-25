from yolo_overlay import YOLOOverlay

def main():
    # Initialize the overlay with default DLL path (bundled)
    overlay = YOLOOverlay(
        model_path=r"C:\path\to\your-model.pt",  # Replace with your model path
        max_detections=150,                      # Optional: Set maximum detections
        conf_threshold=0.6,                      # Optional: Set confidence threshold
        monitor_index=0                           # Optional: Select monitor (0 by default)
    )

    try:
        # Keep the main thread alive while the overlay runs in the background
        while True:
            pass
    except KeyboardInterrupt:
        # Gracefully stop the overlay
        overlay.stop()

if __name__ == "__main__":
    main()
