import time
import subprocess
import pyautogui

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_desktop_agent import KaiDesktopAgent


def ask_for_url():
    """Prompt Claude to provide a URL in marked format"""
    starter_message = "Provide link: << URL >>"
    clipboard_agent = KaiClipboardAgent(message=starter_message)
    clipboard_agent.run()


def capture_claude_url():
    """Use OCR to capture Claude's reply and extract URL"""
    claude_agent = KaiClaudeRegionAgent()
    
    # Get raw text from OCR
    stable_text = claude_agent.wait_for_response_completion()
    
    if not stable_text:
        print("⚠️ No text captured from Claude region.")
        return None

    print(f"📝 Captured text ({len(stable_text)} chars)")
    
    # Use the updated boundary agent to detect URLs
    boundary_agent = KaiBoundaryAgent()
    url_result = boundary_agent.run(stable_text)

    if url_result["success"] and url_result["urls"]:
        url = url_result["urls"][0]
        method = url_result.get("method", "unknown")
        print(f"✅ URL extracted via {method}: {url}")
        return url
    else:
        print("❌ No valid URL found in Claude's reply.")
        # Debug: show what text was captured
        preview = stable_text.replace('\n', ' ')[:200]
        print(f"📋 Text preview: {preview}...")
        return None


def open_and_capture(url):
    """Open URL, screenshot, paste screenshot back into Claude"""
    # Switch to Desktop 2 BEFORE opening browser
    print("🔄 Switching to Desktop 2 for browser...")
    KaiDesktopAgent(direction="right", presses=1).run()
    time.sleep(1)

    # Open URL on Desktop 2
    web_agent = KaiWebAgent(url=url)
    web_agent.run()

    # Wait for page to fully load
    time.sleep(4)

    # Capture entire screen to clipboard
    print("📸 Capturing full screen to clipboard...")
    try:
        subprocess.run(
            ["screencapture", "-c"], 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=10
        )
        print("Screenshot command completed successfully")
        time.sleep(2)  # Wait for clipboard to update
    except subprocess.CalledProcessError as e:
        print(f"Screenshot failed: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("Screenshot command timed out")
        return False

    # Switch back to Desktop 1 (Claude's desktop) BEFORE pasting
    print("🔄 Switching back to Claude's desktop...")
    KaiDesktopAgent(direction="left", presses=1).run()
    time.sleep(2)  # Extra time for desktop switch

    # Paste screenshot into Claude's input
    print("📥 Pasting screenshot into Claude's inbox...")
    try:
        # Click Claude's input area using exact coordinates
        screen_width, screen_height = pyautogui.size()
        print(f"Screen size detected: {screen_width}x{screen_height}")
        
        claude_input_x = 1845
        claude_input_y = 1280
        
        print(f"Clicking Claude input at ({claude_input_x}, {claude_input_y})")
        pyautogui.click(claude_input_x, claude_input_y)
        time.sleep(1)
        
        # Clear any existing text
        pyautogui.hotkey("command", "a")
        time.sleep(0.5)
        
        # Paste screenshot
        pyautogui.hotkey("command", "v")
        time.sleep(2)  # Wait for image to process

        # Send with Enter
        pyautogui.press("enter")
        time.sleep(1)

        print("✅ Screenshot sent back to Claude.")

        # Add follow-up instruction
        follow_up = (
            "Please read and review this image and provide a follow up URL "
            "in the exact format: **<< https://example.com >>**"
        )
        pyautogui.typewrite(follow_up, interval=0.02)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(1)

        print("📝 Follow-up prompt sent to Claude.")

    except Exception as e:
        print(f"Error while pasting screenshot: {e}")
        return False

    return True


def main():
    print("=== Modular Remote Operator: Corrected Autonomous Surfing Loop ===")

    # Always begin on Claude's desktop (Desktop 1)
    KaiDesktopAgent(direction="right", presses=1).run()

    while True:
        # Step 1: Ask for a URL
        ask_for_url()
        time.sleep(1)

        # Step 2: Capture and extract URL
        url = capture_claude_url()
        if not url:
            print("⚠️ No URL captured. Retrying...")
            continue

        # Step 3: Open on correct desktop, capture, and return screenshot
        success = open_and_capture(url)
        if not success:
            print("❌ Failed to capture and return screenshot")

        print("🔁 Ready for next URL...")
        time.sleep(3)  # Pause before next cycle


if __name__ == "__main__":
    main()
