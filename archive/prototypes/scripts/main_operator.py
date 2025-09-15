from logger import Logger
from desktop_manager import DesktopManager
from screen_manager import ScreenManager
from claude_ui import ClaudeUI
from clipboard_manager import ClipboardManager
from boundary_detector import BoundaryDetector
from web_navigator import WebNavigator

def run_cycle():
    logger = Logger()
    health = {}
    desktop = DesktopManager(logger)
    screen = ScreenManager(logger)
    claude = ClaudeUI(logger)
    clipboard = ClipboardManager(logger)
    boundaries = BoundaryDetector(logger)
    webnav = WebNavigator(logger)

    # 1. Switch to Claude desktop (1)
    health['desktop'] = desktop.switch_desktop(1)
    if not health['desktop']:
        logger.notify("Desktop Switch Failure", "Manual intervention required.")

    # 2. Send prompt to Claude
    try:
        claude.focus_and_type("Ready for your next webpage operation command! Use <<URL>> format.")
        health['claude_ui'] = True
    except Exception as e:
        health['claude_ui'] = False
        logger.notify("Claude UI Focus Failure", str(e))

    # 3. Screenshot, OCR, extract boundary
    try:
        img = screen.take_full_screenshot()
        text = screen.extract_text(img)
        boundary_contents = boundaries.extract_boundaries(text)
        health['boundary'] = bool(boundary_contents)
    except Exception as e:
        health['boundary'] = False
        logger.notify("OCR/Boundary Failure", str(e))

    # 4. Open URL in browser
    url = boundary_contents[0] if boundary_contents else "https://www.google.com"
    health['browser'] = desktop.switch_desktop(2) and webnav.open_url(url)

    # 5. Copy screenshot to clipboard, switch back, paste/upload
    try:
        img2 = screen.take_full_screenshot()
        img2_path = "debug_screenshots/result.png"
        img2.save(img2_path)
        clipboard_success = clipboard.copy_image_to_clipboard(img2_path) and clipboard.verify_clipboard_has_image()
        if not clipboard_success:
            logger.notify("Clipboard Failure", "Manual upload fallback required.")
        health['clipboard'] = clipboard_success
    except Exception as e:
        health['clipboard'] = False
        logger.notify("Clipboard Failure", str(e))

    desktop.switch_desktop(1)
    # Paste/upload logic here

    # HEALTH CHECK SUMMARY
    print("\n--- HEALTH CHECK ---")
    for k,v in health.items():
        print(f"{k}: {'SUCCESS' if v else 'FAILURE'}")
    logger.info(f"Health check summary: {health}")

if __name__ == "__main__":
    run_cycle()