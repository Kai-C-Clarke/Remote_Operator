import time
import subprocess
import pyautogui

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_desktop_agent import KaiDesktopAgent


def ask_for_url():
    """Prompt Claude with natural language for a website"""
    starter_message = "What website should we visit?"
    clipboard_agent = KaiClipboardAgent(message=starter_message)
    clipboard_agent.run()


def capture_claude_url():
    """Use OCR to capture Claude's reply and extract any website mention"""
    claude_agent = KaiClaudeRegionAgent()
    
    # Get raw text from OCR
    stable_text = claude_agent.wait_for_response_completion()
    
    if not stable_text:
        print("No text captured from Claude region.")
        return None

    print(f"Captured text ({len(stable_text)} chars)")
    
    # Use the boundary agent to detect any website references
    boundary_agent = KaiBoundaryAgent()
    url_result = boundary_agent.run(stable_text)

    if url_result["success"] and url_result["urls"]:
        url = url_result["urls"][0]
        method = url_result.get("method", "unknown")
        print(f"Website extracted via {method}: {url}")
        return url
    else:
        print("No website found in Claude's reply.")
        # Debug: show what text was captured
        preview = stable_text.replace('\n', ' ')[:200]
        print(f"Text preview: {preview}...")
        return None


def open_and_capture(url):
    """Open URL, screenshot, paste screenshot back into Claude"""
    # Switch to Desktop 2 for browser
    print("Switching to browser desktop...")
    KaiDesktopAgent(direction="right", presses=1).run()
    time.sleep(1)

    # Open URL
    web_agent = KaiWebAgent(url=url)
    web_agent.run()

    # Wait for page to load
    time.sleep(4)

    # Capture screen to clipboard
    print("Capturing screenshot...")
    try:
        subprocess.run(
            ["screencapture", "-c"], 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=10
        )
        print("Screenshot captured successfully")
        time.sleep(2)
    except subprocess.CalledProcessError as e:
        print(f"Screenshot failed: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("Screenshot timed out")
        return False

    # Switch back to Claude's desktop
    print("Returning to Claude...")
    KaiDesktopAgent(direction="left", presses=1).run()
    time.sleep(2)

    # Paste screenshot into Claude
    print("Sending screenshot to Claude...")
    try:
        screen_width, screen_height = pyautogui.size()
        print(f"Screen size: {screen_width}x{screen_height}")
        
        claude_input_x = 1845
        claude_input_y = 1280
        
        print(f"Clicking Claude input at ({claude_input_x}, {claude_input_y})")
        pyautogui.click(claude_input_x, claude_input_y)
        time.sleep(1)
        
        # Clear and paste
        pyautogui.hotkey("command", "a")
        time.sleep(0.5)
        pyautogui.hotkey("command", "v")
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(1)

        print("Screenshot sent to Claude.")

        # Natural follow-up
        follow_up = "What website should we visit next?"
        pyautogui.typewrite(follow_up, interval=0.02)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(1)

        print("Follow-up sent.")

    except Exception as e:
        print(f"Error sending screenshot: {e}")
        return False

    return True


def main():
    print("=== Natural Language Remote Operator ===")

    # Start on Claude's desktop
    KaiDesktopAgent(direction="right", presses=1).run()

    while True:
        # Ask for website
        ask_for_url()
        time.sleep(1)

        # Extract website from response
        url = capture_claude_url()
        if not url:
            print("No website captured. Retrying...")
            continue

        # Visit website and return screenshot
        success = open_and_capture(url)
        if not success:
            print("Failed to complete browsing cycle")

        print("Ready for next website...")
        time.sleep(3)


if __name__ == "__main__":
    main()