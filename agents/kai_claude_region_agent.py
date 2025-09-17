import time
import pyautogui
import pyperclip

# Minimal base class folded in here
class KaiAgent:
    def __init__(self, name="KaiAgent"):
        self.name = name

    def run(self):
        raise NotImplementedError("Subclasses must implement run()")

    def run_fast(self, *args, **kwargs):
        return self.run()

class KaiClaudeRegionAgent(KaiAgent):
    def __init__(self, agent_name="Kai4"):
        super().__init__(name="KaiClaudeRegionAgent")
        self.agent_name = agent_name

        # Predefined safe-click points for each agent's read area
        self.safe_clicks = {
            "Kai4": (650, 650),   # central-ish in Kai4's read area
            "Kai5": (1900, 700),  # central-ish in Kai5's read area
        }

    def wait_for_response_completion_fast(self, timeout=30):
        """
        Capture AI response using clipboard instead of OCR.
        - Click inside the agent's read area.
        - Select all + copy.
        - Return clean clipboard text.
        """
        start_time = time.time()
        response_text = ""

        while time.time() - start_time < timeout:
            try:
                # Focus inside the agent's read area
                if self.agent_name in self.safe_clicks:
                    pyautogui.click(*self.safe_clicks[self.agent_name])
                else:
                    pyautogui.click(100, 100)  # fallback safe click
                time.sleep(0.3)

                # Select all + copy
                pyautogui.hotkey("command", "a")
                time.sleep(0.2)
                pyautogui.hotkey("command", "c")
                time.sleep(0.3)

                # Grab from clipboard
                response_text = pyperclip.paste().strip()

                if response_text:
                    print(f"[KaiClaudeRegionAgent] Captured {self.agent_name} response (length={len(response_text)})")
                    return response_text

            except Exception as e:
                print(f"[KaiClaudeRegionAgent] Clipboard capture failed for {self.agent_name}: {e}")

            time.sleep(1)

        print(f"[KaiClaudeRegionAgent] Timeout: no response detected from {self.agent_name}")
        return response_text or "[NO RESPONSE]"

    def run(self):
        return self.wait_for_response_completion_fast()
