import time
import subprocess
import pyautogui

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_desktop_agent import KaiDesktopAgent


def ask_for_url():
    """Prompt me (Claude/Kai5) to provide a URL inside fenced markdown"""
    starter_message = (
        "Please return a real webpage link inside a fenced markdown code block, "
        "using this exact format:\n\n```markdown\n<< https://example.com >>\n```"
    )
    clipboard_agent = KaiClipboardAgent(message=starter_message)
    clipboard_agent.run()


def capture_claude_url():
    """Use OCR to capture Claude’s reply and extract URL"""
    claude_agent = KaiClaudeRegionAgent()
    result = claude_agent.run(wait_for_stability=True)

    if not result["success"]:
        print("⚠️ No stable text captured from Claude.")
        return None

    # Extract boundaries
    boundary_agent = KaiBoundaryAgent()
    boundaries = boundary_agent.extract_boundaries(result["text"])
    urls = boundary_agent.extract_urls(boundaries)

    if urls:
        print(f"✅ URL extracted: {urls[0]}")
        return urls[0]
    else:
        print("❌ No valid URL found in Claude’s reply.")
        return None


def open_and_capture(url):
    """Open URL, screenshot, paste screenshot back into Claude"""
    web_agent = KaiWebAgent(url=url)
    web_agent.run()

    # Capture entire screen to clipboard
    print("📸 Capturing full screen to clipboard...")
    subprocess.run(["screencapture", "-c"])
    time.sleep(1)

    # Paste screenshot into Claude’s input box
    print("📥 Pasting screenshot into Claude’s inbox...")
    pyautogui.hotkey("command", "v")
    time.sleep(1)
    pyautogui.press("enter")
    print("✅ Screenshot sent back to Claude.")


def main():
    print("=== Modular Remote Operator: Autonomous Surfing Loop ===")

    # Always begin on Claude’s desktop
    desktop_agent = KaiDesktopAgent(target_desktop=1)
    desktop_agent.run()

    while True:
        # Step 1: Ask me for a URL
        ask_for_url()

        # Step 2: Capture and extract URL
        url = capture_claude_url()
        if not url:
            print("⚠️ No URL captured. Retrying...")
            continue

        # Step 3: Open and capture page, then paste it back
        open_and_capture(url)

        # Step 4: Switch back to Claude’s desktop to wait for my next request
        desktop_agent.run()

        print("🔁 Ready for next URL...")
        time.sleep(2)


if __name__ == "__main__":
    main()
