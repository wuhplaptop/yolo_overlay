#include <windows.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <stdarg.h>

// Structure to represent a detection box with tracking
typedef struct {
    int id;            // Unique tracking ID
    int x, y, width, height;
    COLORREF color;    // Box color in 0x00BBGGRR format
    char label[50];    // Label for the detection
    DWORD lastSeen;    // Last update timestamp (milliseconds since system start)
    int paused;        // Pause state (1 = paused, 0 = active)
} DetectionBox;

// Global variables
static DetectionBox* detections = NULL;  // Dynamic array of detections
static int detectionCount = 0;
static int maxDetections = 100;           // Default max detections
static HWND hwnd = NULL;
static HANDLE overlayThread = NULL;
static int isRunning = 0;
static int showLabels = 1;
static int debugMode = 1; // Enable debugging by default
static int detectionTimeoutMs = 2000; // Default timeout for detections
static COLORREF transparentColor = RGB(255, 0, 255); // Bright magenta for transparency
static RECT targetMonitorRect = {0, 0, 2560, 1440}; // Default monitor rect (updated via Python)
CRITICAL_SECTION cs; // Critical section for thread safety

// Function prototypes
LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam);
void DrawDetections(HWND hwnd);
DWORD WINAPI OverlayThread(LPVOID lpParam);
void DebugLog(const char* format, ...);

// Exported functions
#ifdef __cplusplus
extern "C" {
#endif

__declspec(dllexport) int StartOverlay();
__declspec(dllexport) void StopOverlay();
__declspec(dllexport) void UpdateDetections(DetectionBox* newDetections, int count);
__declspec(dllexport) void SetTargetMonitorRect(int left, int top, int right, int bottom);
__declspec(dllexport) void SetMaxDetections(int max);

#ifdef __cplusplus
}
#endif

// Internal debugging function
void DebugLog(const char* format, ...) {
    if (debugMode) {
        char buffer[512];
        va_list args;
        va_start(args, format);
        vsnprintf(buffer, sizeof(buffer), format, args);
        va_end(args);
        OutputDebugStringA(buffer);
    }
}

// DLL entry point
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
        case DLL_PROCESS_ATTACH:
            InitializeCriticalSection(&cs);
            DebugLog("DLL Loaded: Process attached.\n");
            // Allocate initial detections array
            detections = (DetectionBox*)malloc(sizeof(DetectionBox) * maxDetections);
            if (detections == NULL) {
                DebugLog("Failed to allocate memory for detections.\n");
                return FALSE;
            }
            memset(detections, 0, sizeof(DetectionBox) * maxDetections);
            break;
        case DLL_PROCESS_DETACH:
            StopOverlay();
            if (detections) {
                free(detections);
                detections = NULL;
            }
            DeleteCriticalSection(&cs);
            DebugLog("DLL Unloaded: Process detached.\n");
            break;
    }
    return TRUE;
}

// Set target monitor rectangle
__declspec(dllexport) void SetTargetMonitorRect(int left, int top, int right, int bottom) {
    EnterCriticalSection(&cs);
    targetMonitorRect.left = left;
    targetMonitorRect.top = top;
    targetMonitorRect.right = right;
    targetMonitorRect.bottom = bottom;
    LeaveCriticalSection(&cs);

    char debugMsg[256];
    sprintf_s(debugMsg, sizeof(debugMsg), "Target monitor rectangle updated: (%d, %d, %d, %d)\n", left, top, right, bottom);
    DebugLog(debugMsg);
}

// Set maximum number of detections
__declspec(dllexport) void SetMaxDetections(int max) {
    if (max <= 0) {
        DebugLog("SetMaxDetections called with invalid value. Must be > 0.\n");
        return;
    }

    EnterCriticalSection(&cs);

    // Reallocate detections array
    DetectionBox* newDetections = (DetectionBox*)realloc(detections, sizeof(DetectionBox) * max);
    if (newDetections == NULL) {
        DebugLog("Failed to reallocate memory for detections.\n");
        LeaveCriticalSection(&cs);
        return;
    }

    detections = newDetections;
    maxDetections = max;

    // Initialize new slots if the array has grown
    if (maxDetections > detectionCount) {
        memset(&detections[detectionCount], 0, sizeof(DetectionBox) * (maxDetections - detectionCount));
    }

    // If the array has shrunk, adjust detectionCount
    if (detectionCount > maxDetections) {
        detectionCount = maxDetections;
    }

    LeaveCriticalSection(&cs);

    char debugMsg[256];
    sprintf_s(debugMsg, sizeof(debugMsg), "Max detections set to %d.\n", maxDetections);
    DebugLog(debugMsg);
}

// Start the overlay
__declspec(dllexport) int StartOverlay() {
    if (isRunning) {
        DebugLog("Overlay already running.\n");
        return 0; // Already running
    }
    isRunning = 1;

    overlayThread = CreateThread(NULL, 0, OverlayThread, NULL, 0, NULL);
    if (!overlayThread) {
        isRunning = 0;
        DWORD errorCode = GetLastError();
        char errorMsg[256];
        sprintf_s(errorMsg, sizeof(errorMsg), "Failed to create overlay thread. Error code: %lu\n", errorCode);
        DebugLog(errorMsg);
        return -1;
    }

    DebugLog("Overlay started successfully.\n");
    return 0;
}

// Stop the overlay
__declspec(dllexport) void StopOverlay() {
    if (!isRunning) return;

    isRunning = 0;

    if (hwnd) PostMessage(hwnd, WM_CLOSE, 0, 0);
    if (overlayThread) {
        WaitForSingleObject(overlayThread, INFINITE);
        CloseHandle(overlayThread);
        overlayThread = NULL;
    }

    DebugLog("Overlay stopped.\n");
}

// Utility function to calculate Intersection over Union (IoU)
float CalculateIoU(DetectionBox a, DetectionBox b) {
    int x1 = max(a.x, b.x);
    int y1 = max(a.y, b.y);
    int x2 = min(a.x + a.width, b.x + b.width);
    int y2 = min(a.y + a.height, b.y + b.height);

    int intersectionArea = max(0, x2 - x1) * max(0, y2 - y1);
    int aArea = a.width * a.height;
    int bArea = b.width * b.height;

    if (aArea + bArea - intersectionArea == 0) return 0.0f;

    return (float)intersectionArea / (float)(aArea + bArea - intersectionArea);
}

// Update detection data with merging based on unique IDs and handle multiple boxes
__declspec(dllexport) void UpdateDetections(DetectionBox* newDetections, int count) {
    if (newDetections == NULL || count <= 0) return;

    DWORD now = GetTickCount();
    EnterCriticalSection(&cs);

    for (int i = 0; i < count && i < maxDetections; i++) {
        int det_id = newDetections[i].id;
        int found = 0;

        // Search for existing detection with same ID
        for (int j = 0; j < detectionCount; j++) {
            if (detections[j].id == det_id) {
                // Update existing detection
                detections[j] = newDetections[i];
                detections[j].lastSeen = now;
                detections[j].paused = 0; // Ensure detections are active upon update

                char debugMsg[256];
                sprintf_s(debugMsg, sizeof(debugMsg), "Detection updated - ID: %d, X: %d, Y: %d, W: %d, H: %d, Label: %s\n",
                        detections[j].id, detections[j].x, detections[j].y,
                        detections[j].width, detections[j].height, detections[j].label);
                DebugLog(debugMsg);
                found = 1;
                break;
            }
        }

        if (!found) {
            // Check for overlapping detections using IoU
            int shouldAdd = 1;
            for (int j = 0; j < detectionCount; j++) {
                float iou = CalculateIoU(newDetections[i], detections[j]);
                if (iou > 0.5f) { // Threshold can be adjusted
                    // Consider this detection as duplicate, choose to keep the one with higher confidence if available
                    // For simplicity, we'll skip adding this detection
                    shouldAdd = 0;
                    DebugLog("Duplicate detection detected based on IoU. Skipping addition.\n");
                    break;
                }
            }

            if (shouldAdd) {
                // Add new detection
                if (detectionCount < maxDetections) {
                    detections[detectionCount] = newDetections[i];
                    detections[detectionCount].lastSeen = now;
                    detections[detectionCount].paused = 0; // Ensure detections are active upon update

                    char debugMsg[256];
                    sprintf_s(debugMsg, sizeof(debugMsg), "New detection added - ID: %d, X: %d, Y: %d, W: %d, H: %d, Label: %s\n",
                            detections[detectionCount].id, detections[detectionCount].x, detections[detectionCount].y,
                            detections[detectionCount].width, detections[detectionCount].height, detections[detectionCount].label);
                    DebugLog(debugMsg);
                    detectionCount++;
                } else {
                    // Maximum detections reached
                    char debugMsg[256];
                    sprintf_s(debugMsg, sizeof(debugMsg), "Maximum detections reached. Cannot add detection ID: %d\n", det_id);
                    DebugLog(debugMsg);
                }
            }
        }
    }

    LeaveCriticalSection(&cs);

    if (hwnd) {
        DebugLog("Redrawing overlay window with updated detections.\n");
        InvalidateRect(hwnd, NULL, TRUE);
        UpdateWindow(hwnd);
    }
}

// Draw the detections
void DrawDetections(HWND hwnd) {
    PAINTSTRUCT ps;
    HDC hdc = BeginPaint(hwnd, &ps);
    DebugLog("BeginPaint called.\n");

    HDC memDC = CreateCompatibleDC(hdc);
    if (!memDC) {
        DebugLog("Failed to create compatible DC.\n");
        EndPaint(hwnd, &ps);
        return;
    }

    int screenWidth = targetMonitorRect.right - targetMonitorRect.left;
    int screenHeight = targetMonitorRect.bottom - targetMonitorRect.top;
    HBITMAP memBitmap = CreateCompatibleBitmap(hdc, screenWidth, screenHeight);

    if (!memBitmap) {
        DebugLog("Failed to create compatible bitmap.\n");
        DeleteDC(memDC);
        EndPaint(hwnd, &ps);
        return;
    }

    SelectObject(memDC, memBitmap);

    // Fill with transparent color for background
    HBRUSH backgroundBrush = CreateSolidBrush(transparentColor);
    RECT fullScreen = { 0, 0, screenWidth, screenHeight };
    FillRect(memDC, &fullScreen, backgroundBrush);
    DeleteObject(backgroundBrush);
    DebugLog("Filled background with transparent color.\n");

    // Draw detections
    EnterCriticalSection(&cs);
    DebugLog("Entered critical section for drawing.\n");

    DebugLog("Number of detections to draw: %d\n", detectionCount);

    DWORD now = GetTickCount();

    for (int i = 0; i < detectionCount; i++) {
        // Check if detection has timed out
        if ((now - detections[i].lastSeen) > detectionTimeoutMs) {
            detections[i].paused = 1;
            DebugLog("Detection ID %d timed out and is paused.\n", detections[i].id);
            continue;
        }

        if (detections[i].paused) {
            DebugLog("Detection ID %d is paused. Skipping.\n", detections[i].id);
            continue;
        }

        HPEN pen = CreatePen(PS_SOLID, 4, detections[i].color); // Pen color for the box
        if (!pen) {
            DebugLog("Failed to create pen for detection ID %d.\n", detections[i].id);
            continue;
        }
        SelectObject(memDC, pen);

        // Select a NULL_BRUSH to prevent filling the rectangle
        HBRUSH hOldBrush = (HBRUSH)SelectObject(memDC, GetStockObject(NULL_BRUSH));
        if (!hOldBrush) {
            DebugLog("Failed to select NULL_BRUSH for detection ID %d.\n", detections[i].id);
        }

        // Correct Coordinate Assignment
        int x = detections[i].x;
        int y = detections[i].y;
        int w = x + detections[i].width;
        int h = y + detections[i].height;

        // Clamp coordinates to the overlay window bounds
        x = max(0, min(screenWidth, x));
        y = max(0, min(screenHeight, y));
        w = max(0, min(screenWidth, w));
        h = max(0, min(screenHeight, h));

        // Log adjusted coordinates
        char debugMsg[256];
        sprintf_s(debugMsg, sizeof(debugMsg), "Drawing rect: ID=%d, X=%d, Y=%d, W=%d, H=%d\n",
                detections[i].id, x, y, w, h);
        DebugLog(debugMsg);

        // Draw rectangle
        Rectangle(memDC, x, y, w, h);
        DebugLog("Rectangle drawn.\n");

        // Restore the old brush
        SelectObject(memDC, hOldBrush);

        // Clean up the pen
        DeleteObject(pen);

        if (showLabels) {
            SetBkMode(memDC, TRANSPARENT);
            SetTextColor(memDC, detections[i].color);
            // Ensure label is null-terminated
            size_t labelLength = strnlen(detections[i].label, sizeof(detections[i].label));
            TextOutA(memDC, x, y - 20, detections[i].label, (int)labelLength);
            DebugLog("Label drawn for detection ID %d.\n", detections[i].id);
        }
    }

    LeaveCriticalSection(&cs);
    DebugLog("Left critical section after drawing.\n");

    // BitBlt to the screen
    if (!BitBlt(hdc, 0, 0, screenWidth, screenHeight, memDC, 0, 0, SRCCOPY)) {
        DebugLog("BitBlt failed.\n");
    } else {
        DebugLog("BitBlt succeeded.\n");
    }

    DeleteObject(memBitmap);
    DeleteDC(memDC);
    EndPaint(hwnd, &ps);
    DebugLog("EndPaint called.\n");
}


// Window procedure
LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
        case WM_PAINT:
            DebugLog("WM_PAINT triggered.\n");
            DrawDetections(hwnd);
            break;
        case WM_DESTROY:
            DebugLog("WM_DESTROY received. Posting quit message.\n");
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hwnd, uMsg, wParam, lParam);
    }
    return 0;
}

// Overlay thread function
DWORD WINAPI OverlayThread(LPVOID lpParam) {
    WNDCLASSA wc = { 0 };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = GetModuleHandle(NULL);
    wc.lpszClassName = "OverlayWindow";

    if (!RegisterClassA(&wc)) {
        DebugLog("Failed to register window class.\n");
        return -1;
    }

    hwnd = CreateWindowExA(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TRANSPARENT, // Layered, topmost, and transparent
        "OverlayWindow",
        "YOLO Overlay",
        WS_POPUP,
        targetMonitorRect.left,
        targetMonitorRect.top,
        targetMonitorRect.right - targetMonitorRect.left,
        targetMonitorRect.bottom - targetMonitorRect.top,
        NULL, NULL, wc.hInstance, NULL);

    if (!hwnd) {
        DebugLog("Failed to create overlay window.\n");
        return -1;
    }

    // Set layered window attributes with color key for transparency
    if (!SetLayeredWindowAttributes(hwnd, transparentColor, 255, LWA_COLORKEY)) {
        DebugLog("Failed to set layered window attributes.\n");
    }

    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);

    DebugLog("Overlay window created and shown successfully.\n");

    // Message loop
    MSG msg = { 0 };
    while (isRunning && GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    hwnd = NULL;
    DebugLog("Overlay thread exiting.\n");
    return 0;
}
