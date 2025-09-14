# AI Remote Operator – Council Modular Codebase

Welcome to the modular automation system for remote AI web operations.  
Each module is designed for resilience, testability, and clear error reporting.  
This README provides a structured guide for each module: purpose, interface, methods, usage, dependencies, fallback and notification hooks.

---

## Table of Contents

- [logger.py](#loggerpy)
- [desktop_manager.py](#desktop_managerpy)
- [screen_manager.py](#screen_managerpy)
- [claude_ui.py](#claude_uipy)
- [clipboard_manager.py](#clipboard_managerpy)
- [boundary_detector.py](#boundary_detectorpy)
- [web_navigator.py](#web_navigatorpy)
- [main_operator.py](#main_operatorpy)
- [tests/](#tests)
- [config.py (optional)](#configpy-optional)

---

## logger.py

**Purpose:**  
Centralized logging, debug screenshot saving, and user notification for manual intervention.

**Key Methods:**  
- `info(msg)` / `error(msg)` / `warning(msg)`: Log with timestamp.
- `save_screenshot(img, purpose='debug')`: Save screenshots to debug dir, log path.
- `notify(title, message)`: Send macOS user notification (AppleScript), fallback logs.

**Example Usage:**
```python
from logger import Logger
logger = Logger()
logger.info("Cycle started")
logger.save_screenshot(img, purpose="step1")
logger.notify("Manual Action Needed", "Switch to Desktop 2")
```

**Dependencies:**  
- Python stdlib: logging, os, time, subprocess
- macOS: AppleScript (osascript)

**Fallback Points:**  
- If notification fails, logs error and prints to console.

---

## desktop_manager.py

**Purpose:**  
Switch macOS desktops (Spaces), track current, verify successful switch, notify user on failure.

**Key Methods:**  
- `switch_desktop(target)`: Switch to target desktop, log, notify on fail.
- `current_desktop`: Attribute tracking current desktop.
- (Future: `verify_desktop()` for visual confirmation.)

**Example Usage:**
```python
dm = DesktopManager(logger)
if not dm.switch_desktop(2):
    logger.notify("Desktop Switch Failure", "Manual intervention required.")
```

**Dependencies:**  
- subprocess, time
- logger.py

**Fallback Points:**  
- On failure, triggers `Logger.notify`.

---

## screen_manager.py

**Purpose:**  
Screenshot capture (full/region), OCR extraction, preprocessing for OCR reliability.

**Key Methods:**  
- `take_full_screenshot(path=None)`: Capture and return full screen image.
- `take_region_screenshot(region, path=None)`: Capture region.
- `extract_text(img)`: OCR text from image.

**Example Usage:**
```python
sm = ScreenManager(logger)
img = sm.take_full_screenshot()
text = sm.extract_text(img)
```

**Dependencies:**  
- pyautogui, PIL, pytesseract, numpy, cv2
- logger.py

**Fallback Points:**  
- On screenshot/OCR failure, saves image and logs for manual review.

---

## claude_ui.py

**Purpose:**  
Find and focus Claude’s input box, send text/image, verify focus, log actions.

**Key Methods:**  
- `find_input_box()`: Locate input box (default or OCR/template).
- `focus_and_type(text)`: Focus and type text, log.
- (Future: `verify_focus()` for cursor detection.)

**Example Usage:**
```python
cu = ClaudeUI(logger)
cu.focus_and_type("Ready for command!")
```

**Dependencies:**  
- pyautogui
- logger.py

**Fallback Points:**  
- On failure, triggers notification for manual focus.

---

## clipboard_manager.py

**Purpose:**  
Copy screenshot to clipboard, verify clipboard image, retry/fallback to file upload, log all actions.

**Key Methods:**  
- `copy_image_to_clipboard(image_path)`: AppleScript copy, log.
- `verify_clipboard_has_image()`: Check clipboard for image.
- (Future: `fallback_file_upload(image_path)`.)

**Example Usage:**
```python
cm = ClipboardManager(logger)
for attempt in range(3):
    if cm.copy_image_to_clipboard(path) and cm.verify_clipboard_has_image():
        break
else:
    logger
