"""
doc_loop_navigator.py
Bare bones: Doc <-> AI UI with correct desktop switching
Desktop0 = Terminal (start)
Desktop1 = AI UI
Desktop2 = Google Doc
"""

import time
import pyperclip, pyautogui

from agents.kai_doc_copy_agent import KaiDocCopyAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_desktop_agent import KaiDesktopAgent
from agents.kai_web_agent import KaiWebAgent

GOOGLE_DOC_URL = "https://docs.google.com/document/d/1DZts-qG4cQGoX36UsZ9PkFGa9xKxIcg_d8MH9XD-KqU/edit?tab=t.0"

class DocLoopNavigator:
    def __init__(self):
        self.doc_url = GOOGLE_DOC_URL

    def copy_doc(self):
        """Switch to desktop2 and copy full Google Doc text"""
        KaiDesktopAgent(direction="right", presses=2).run_fast()  # 0 -> 2
        time.sleep(0.7)

        # Ensure Doc is open
        web_agent = KaiWebAgent(url=self.doc_url)
        web_agent.run_fast()
        time.sleep(2)

        # Copy entire Doc
        doc_copy_agent = KaiDocCopyAgent()
        text = doc_copy_agent.run()

        # Back to desktop1 (AI UI)
        KaiDesktopAgent(direction="left", presses=1).run_fast()  # 2 -> 1
        time.sleep(0.7)

        return text

    def paste_into_doc(self, text):
        """Switch to desktop2 and paste text into Google Doc"""
        KaiDesktopAgent(direction="right", presses=1).run_fast()  # 1 -> 2
        time.sleep(0.7)

        web_agent = KaiWebAgent(url=self.doc_url)
        web_agent.run_fast()
        time.sleep(2)

        # Paste into Doc body
        pyautogui.click(600, 360)
        time.sleep(0.4)
        pyperclip.copy(text)
        pyautogui.hotkey("command", "v")
        time.sleep(0.3)
        pyautogui.press("enter")

        # Back to desktop1 (AI UI)
        KaiDesktopAgent(direction="left", presses=1).run_fast()  # 2 -> 1
        time.sleep(0.7)

    def run_cycle(self):
        # 1. Copy doc text
        doc_text = self.copy_doc()
        print("Copied doc length:", len(doc_text))

        # 2. Paste into AI UI (Claude/Kai)
        KaiClipboardAgent(message=doc_text).run_fast()
        time.sleep(1)

        # 3. Capture AI response
        claude_agent = KaiClaudeRegionAgent()
        ai_response = claude_agent.wait_for_response_completion_fast()
        print("AI response:", ai_response[:200])

        # 4. Paste back into Doc
        self.paste_into_doc(ai_response)

        # Optional: return to Terminal (desktop0)
        KaiDesktopAgent(direction="left", presses=1).run_fast()  # 1 -> 0
        time.sleep(0.7)

    def run(self, cycles=3):
        for i in range(cycles):
            print(f"\n--- Cycle {i+1} ---")
            self.run_cycle()
            time.sleep(2)


if __name__ == "__main__":
    navigator = DocLoopNavigator()
    navigator.run(cycles=3)
