from core.kai_agent_base import KaiAgent
import pyperclip
import pyautogui
import time

class KaiSimplePasteAgent(KaiAgent):
    def __init__(self, message=None, **kwargs):
        super().__init__(name="KaiSimplePasteAgent", **kwargs)
        self.message = message

    def run(self):
        if not self.message:
            raise ValueError("No message provided for paste")

        # Copy message to clipboard
        pyperclip.copy(self.message)
        self.log(f"Message copied to clipboard: {self.message}")

        time.sleep(0.5)

        # Paste into Claude input and send
        pyautogui.hotkey("command", "v")
        time.sleep(0.5)
        pyautogui.press("enter")

        self.log("Message pasted and sent successfully")
        return True

    def verify(self):
        return True
