def rgb_to_colorref(r, g, b):
    """Convert RGB to COLORREF format (0x00BBGGRR)."""
    return (b << 16) | (g << 8) | r

def encode_label(label_text):
    """Ensure label is null-terminated and exactly 50 bytes."""
    encoded = label_text.encode('utf-8')[:49]  # Truncate to 49 bytes
    return encoded + b'\x00' + b'\x00' * (49 - len(encoded))  # Null-terminate and pad

def sanitize_bounding_box(x1, y1, x2, y2, monitor_width, monitor_height):
    """Ensure bounding box fits within monitor bounds and has valid dimensions."""
    print(f"[DEBUG] Before sanitize: ({x1}, {y1}, {x2}, {y2})")
    
    # Clamp coordinates to the monitor bounds
    x1 = max(0, min(monitor_width, x1))
    y1 = max(0, min(monitor_height, y1))
    x2 = max(0, min(monitor_width, x2))
    y2 = max(0, min(monitor_height, y2))
    
    # Ensure minimum width and height
    if x2 <= x1:
        x2 = x1 + 1  # Ensure at least 1-pixel width
    if y2 <= y1:
        y2 = y1 + 1  # Ensure at least 1-pixel height
    
    print(f"[DEBUG] After sanitize: ({x1}, {y1}, {x2}, {y2})\n")
    return x1, y1, x2 - x1, y2 - y1  # Return x, y, width, height
