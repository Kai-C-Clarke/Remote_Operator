"""
navigator_v4_speed_optimized.py
Speed-optimized version with dynamic timing and reduced wait cycles
"""

import time
import subprocess
import pyautogui
from pathlib import Path

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_desktop_agent import KaiDesktopAgent


def ask_for_url():
    """Prompt Claude with minimal delay"""
    starter_message = "What website should we visit?"
    clipboard_agent = KaiClipboardAgent(message=starter_message)
    clipboard_agent.run_fast()  # New fast mode


def capture_claude_url():
    """Use OCR with optimized stability detection"""
    claude_agent = KaiClaudeRegionAgent()
    
    # Reduced stability requirements for speed
    stable_text = claude_agent.wait_for_response_completion_fast()
    
    if not stable_text:
        print("No text captured from Claude region.")
        return None

    print(f"Captured text ({len(stable_text)} chars)")
    
    boundary_agent = KaiBoundaryAgent()
    url_result = boundary_agent.run(stable_text)

    if url_result["success"] and url_result["urls"]:
        url = url_result["urls"][0]
        method = url_result.get("method", "unknown")
        print(f"Website extracted via {method}: {url}")
        return url
    else:
        print("No website found in Claude's reply.")
        preview = stable_text.replace('\n', ' ')[:200]
        print(f"Text preview: {preview}...")
        return None


def open_and_capture_fast(url):
    """Optimized navigation with reduced delays"""
    # Faster desktop switching
    print("Switching to browser desktop...")
    KaiDesktopAgent(direction="right", presses=1).run_fast()
    time.sleep(0.7)  # Reduced from 1.0s

    # Open URL with reduced settle time
    web_agent = KaiWebAgent(url=url)
    web_agent.run_fast()

    # Optimized page load wait with early detection
    if wait_for_page_ready(3.0):  # Max 3s vs previous 4s
        print("Page loaded quickly")
    else:
        print("Using fallback timing")
        time.sleep(1.0)  # Reduced fallback

    # Faster screenshot capture
    print("Capturing screenshot...")
    try:
        subprocess.run(
            ["screencapture", "-c"], 
            check=True, 
            timeout=8  # Reduced from 10s
        )
        print("Screenshot captured")
        time.sleep(1.0)  # Reduced from 2.0s
    except subprocess.CalledProcessError as e:
        print(f"Screenshot failed: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("Screenshot timed out")
        return False

    # Faster return to Claude
    print("Returning to Claude...")
    KaiDesktopAgent(direction="left", presses=1).run_fast()
    time.sleep(1.2)  # Reduced from 2.0s

    # Optimized clipboard interaction
    print("Sending screenshot to Claude...")
    try:
        claude_input_x = 1845
        claude_input_y = 1280
        
        pyautogui.click(claude_input_x, claude_input_y)
        time.sleep(0.3)  # Reduced from 1.0s
        
        pyautogui.hotkey("command", "a")
        time.sleep(0.2)  # Reduced from 0.5s
        pyautogui.hotkey("command", "v")
        time.sleep(1.2)  # Reduced from 2.0s
        pyautogui.press("enter")
        time.sleep(0.5)  # Reduced from 1.0s

        print("Screenshot sent to Claude.")

        # Faster follow-up
        follow_up = "What website should we visit next?"
        pyautogui.typewrite(follow_up, interval=0.008)  # Faster typing
        time.sleep(0.3)  # Reduced from 0.5s
        pyautogui.press("enter")
        time.sleep(0.5)  # Reduced from 1.0s

        print("Follow-up sent.")

    except Exception as e:
        print(f"Error sending screenshot: {e}")
        return False

    return True


def wait_for_page_ready(max_wait=3.0):
    """Dynamic page load detection instead of fixed delays"""
    start_time = time.time()
    last_title = ""
    stable_count = 0
    
    while time.time() - start_time < max_wait:
        try:
            # Check if page title has stabilized (basic readiness indicator)
            current_title = pyautogui.getActiveWindow().title if pyautogui.getActiveWindow() else ""
            
            if current_title == last_title and current_title:
                stable_count += 1
                if stable_count >= 2:  # Page title stable for 2 checks
                    return True
            else:
                stable_count = 0
                
            last_title = current_title
            time.sleep(0.3)  # Quick checks
            
        except:
            time.sleep(0.3)
            continue
    
    return False


def main():
    """Main loop with optimized timing"""
    print("=== Speed-Optimized Navigator ===")

    # Quick initial desktop positioning
    KaiDesktopAgent(direction="right", presses=1).run_fast()

    cycle_count = 0
    while True:
        cycle_start = time.time()
        
        # Speed-optimized cycle
        ask_for_url()
        time.sleep(0.5)  # Reduced from 1.0s

        url = capture_claude_url()
        if not url:
            print("No URL captured. Retrying...")
            continue

        success = open_and_capture_fast(url)
        if not success:
            print("Failed to complete browsing cycle")

        cycle_time = time.time() - cycle_start
        cycle_count += 1
        
        print(f"Cycle {cycle_count} completed in {cycle_time:.1f}s")
        print("Ready for next website...")
        time.sleep(1.5)  # Reduced from 3.0s


if __name__ == "__main__":
    main()