from core.kai_agent_base import KaiAgent
import subprocess
import pyperclip
import time

class KaiClipboardAgent(KaiAgent):
    def __init__(self, message=None, paste_hotkey='cmd+v', send_hotkey='enter', **kwargs):
        super().__init__(name="KaiClipboardAgent", **kwargs)
        self.message = message
        self.paste_hotkey = paste_hotkey
        self.send_hotkey = send_hotkey

    def run(self):
        if not self.message:
            raise ValueError("No message provided for clipboard injection.")

        self.log(f"Copying message to clipboard...")
        pyperclip.copy(self.message)
        time.sleep(0.5)

        self.log(f"Sending paste keystroke: {self.paste_hotkey}")
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'])
        time.sleep(0.3)

        self.log(f"Sending enter keystroke...")
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'])
        self.log("Message injected via clipboard.")

    def verify(self):
        # Optional: implement OCR confirmation later
        return True
