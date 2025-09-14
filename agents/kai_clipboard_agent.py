from core.kai_agent_base import KaiAgent
import pyperclip
import time
import pyautogui

class KaiClipboardAgent(KaiAgent):
    def __init__(self, message=None, **kwargs):
        super().__init__(name="KaiClipboardAgent", **kwargs)
        self.message = message

    def run(self):
        if not self.message:
            raise ValueError("No message provided for clipboard injection.")

        # Copy message to clipboard
        pyperclip.copy(self.message)
        self.log(f"Copied message to clipboard: {self.message}")
        time.sleep(0.5)

        # Click Claude's input area first
        self.log("Clicking Claude's input area")
        claude_input_x = 1845  # Center of Claude's input
        claude_input_y = 1280
        pyautogui.click(claude_input_x, claude_input_y)
        time.sleep(0.5)
    
        # Clear any existing text
        pyautogui.hotkey("command", "a")
        time.sleep(0.2)

        # Paste message
        self.log("Pasting message into Claude input")
        pyautogui.hotkey("command", "v")
        time.sleep(0.5)

        # Send with Enter
        pyautogui.press("enter")
        self.log("Message sent successfully")
        return True

    def run_fast(self):
        """Speed-optimized clipboard operations"""
        if not self.message:
            raise ValueError("No message provided for fast clipboard injection.")

        # Faster clipboard operations
        pyperclip.copy(self.message)
        self.log(f"Fast copied message to clipboard: {self.message}")
        time.sleep(0.2)  # Reduced from 0.5s

        # Optimized input area clicking
        self.log("Fast clicking Claude's input area")
        claude_input_x = 1845
        claude_input_y = 1280
        pyautogui.click(claude_input_x, claude_input_y)
        time.sleep(0.3)  # Reduced from 0.5s

        # Faster text operations
        pyautogui.hotkey("command", "a")
        time.sleep(0.1)  # Reduced from 0.2s

        pyautogui.hotkey("command", "v")
        time.sleep(0.3)  # Reduced from 0.5s

        pyautogui.press("enter")
        self.log("Fast message sent successfully")
        return True