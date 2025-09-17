from core.kai_agent_base import KaiAgent
import pyautogui
import pyperclip
import time

class KaiDocCopyAgent(KaiAgent):
    def __init__(self, region=None, **kwargs):
        super().__init__(name="KaiDocCopyAgent", **kwargs)
        self.region = region  # Optional: (x, y, width, height)

    def run(self):
        """Copy all text from the active Google Doc tab"""
        try:
            self.log("KaiDocCopyAgent starting")

            # Click somewhere in the doc body to focus
            pyautogui.click(800, 400)  # rough safe mid-doc position
            time.sleep(0.5)

            # Select all + copy
            pyautogui.hotkey("command", "a")
            time.sleep(0.2)
            pyautogui.hotkey("command", "c")
            time.sleep(0.5)

            # Retrieve clipboard
            doc_text = pyperclip.paste()
            self.log(f"Copied {len(doc_text)} characters from doc")
            return doc_text
        except Exception as e:
            self.log(f"Doc copy failed: {e}")
            return ""

    def run_fast(self):
        """Faster select-all and copy"""
        try:
            self.log("KaiDocCopyAgent fast copy starting")

            pyautogui.click(800, 400)  # safe mid-doc position
            time.sleep(0.2)

            pyautogui.hotkey("command", "a")
            time.sleep(0.1)
            pyautogui.hotkey("command", "c")
            time.sleep(0.2)

            doc_text = pyperclip.paste()
            self.log(f"Fast copied {len(doc_text)} characters from doc")
            return doc_text
        except Exception as e:
            self.log(f"Fast doc copy failed: {e}")
            return ""

    def verify(self):
        return True
