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
        """Find and click on Claude's input area using specific coordinates"""
        try:
            # Get screen dimensions for reference
            screen_width, screen_height = pyautogui.size()
            self.log(f"Detected screen size: {screen_width}x{screen_height}")
            
            # Use coordinates based on your working script
            # Your working script uses Claude region (1540, 221, 868, 856)
            # Input area is typically at bottom of Claude's region
            claude_left = 1540
            claude_width = 868
            claude_input_x = claude_left + (claude_width // 2)  # Center of Claude's area
            claude_input_y = screen_height - 150  # Near bottom as before
            
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