from core.kai_agent_base import KaiAgent
import subprocess
import pyperclip
import time
import pyautogui

class KaiClipboardAgent(KaiAgent):
    def __init__(self, message=None, paste_hotkey='cmd+v', send_hotkey='enter', find_input=True, **kwargs):
        super().__init__(name="KaiClipboardAgent", **kwargs)
        self.message = message
        self.paste_hotkey = paste_hotkey
        self.send_hotkey = send_hotkey
        self.find_input = find_input

    def find_claude_input_area(self):
        """Find and click on Claude's input area using exact measured coordinates"""
        try:
            # Get screen dimensions for reference
            screen_width, screen_height = pyautogui.size()
            self.log(f"Detected screen size: {screen_width}x{screen_height}")
            
            # Use your exact measured coordinates
            # Claude's input area: (1587, 1252) to (2103, 1308)
            input_left = 1587
            input_top = 1252
            input_right = 2103
            input_bottom = 1308
            
            # Click in center of input area
            claude_input_x = (input_left + input_right) // 2  # 1845
            claude_input_y = (input_top + input_bottom) // 2  # 1280
            
            self.log(f"Clicking Claude input area at ({claude_input_x}, {claude_input_y})")
            pyautogui.click(claude_input_x, claude_input_y)
            time.sleep(0.5)
            
            # Clear any existing text
            pyautogui.hotkey('cmd', 'a')
            time.sleep(0.2)
            
            return True
            
        except Exception as e:
            self.log(f"Failed to find input area: {e}")
            return False

    def run(self):
        if not self.message:
            raise ValueError("No message provided for clipboard injection.")

        # Find Claude's input area if requested
        if self.find_input:
            if not self.find_claude_input_area():
                self.log("Warning: Could not find input area, proceeding anyway")

        self.log(f"Copying message to clipboard: {self.message[:50]}...")
        pyperclip.copy(self.message)
        time.sleep(0.5)

        # Verify clipboard content
        clipboard_content = pyperclip.paste()
        if clipboard_content != self.message:
            raise Exception("Clipboard copy verification failed")

        self.log(f"Pasting content using {self.paste_hotkey}")
        try:
            # Use pyautogui for more reliable key combinations
            pyautogui.hotkey('cmd', 'v')
            time.sleep(0.5)
        except Exception as e:
            # Fallback to AppleScript
            self.log("Pyautogui failed, using AppleScript fallback")
            subprocess.run(["osascript", "-e", 
                'tell application "System Events" to keystroke "v" using command down'], 
                check=True)
            time.sleep(0.5)

        self.log("Sending message with Enter")
        try:
            pyautogui.press('enter')
            time.sleep(0.3)
        except Exception as e:
            # Fallback to AppleScript
            subprocess.run(["osascript", "-e", 
                'tell application "System Events" to key code 36'], 
                check=True)

        self.log("Message injected via clipboard successfully")
        return True

    def verify(self):
        # Could add OCR verification here later
        return True