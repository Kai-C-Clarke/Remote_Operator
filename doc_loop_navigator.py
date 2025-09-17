import time
from datetime import datetime

# Agents
from agents.kai_doc_copy_agent import KaiDocCopyAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_desktop_agent import KaiDesktopAgent
from agents.kai_web_agent import KaiWebAgent

GOOGLE_DOC_URL = "https://docs.google.com/document/d/1DZts-qG4cQGoX36UsZ9PkFGa9xKxIcg_d8MH9XD-KqU/edit?tab=t.0"

SEED_TEXT = """# AI Council Dialogue Log
*(Seeded at start if doc is empty)*

**Prompt:** Explore the idea of developing an *enquiring mind* for AI.
How might this be achieved? What qualities or processes would support it?
"""

class DocLoopNavigator:
    def __init__(self):
        self.agent_toggle = True  # True = Kai4, False = Kai5

    def get_agent_name(self):
        return "Kai4" if self.agent_toggle else "Kai5"

    def seed_if_empty(self, doc_text: str):
        """Insert seed into the Google Doc if it's empty."""
        if not doc_text.strip():
            print("[NAVIGATOR] Doc is empty — inserting seed text")
            KaiClipboardAgent(message=SEED_TEXT).run_fast()
            KaiDesktopAgent(direction="left", presses=1).run_fast()
            return SEED_TEXT
        return doc_text

    def run_cycle(self):
        agent_name = self.get_agent_name()
        print(f"\n--- Cycle ({agent_name}) ---")

        # Switch to doc (desktop2 assumed)
        KaiDesktopAgent(direction="right", presses=2).run_fast()
        KaiWebAgent(url=GOOGLE_DOC_URL).run_fast()

        # Copy text from doc
        doc_copy_agent = KaiDocCopyAgent()
        doc_text = doc_copy_agent.run_fast()
        print(f"[NAVIGATOR] Copied doc length: {len(doc_text)}")

        # Seed if empty
        doc_text = self.seed_if_empty(doc_text)

        # Back to desktop1
        KaiDesktopAgent(direction="left", presses=1).run_fast()

        # Send snippet to current agent
        snippet = doc_text[-2000:] if len(doc_text) > 2000 else doc_text
        print(f"[NAVIGATOR] Sending snippet to {agent_name}, length={len(snippet)}")
        KaiClipboardAgent(message=snippet).run_fast()
        region_agent = KaiClaudeRegionAgent()
        ai_response = region_agent.run_fast()

        # Append response into doc with label + timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{agent_name} • {timestamp}\n{ai_response}\n----------------------------------------\n"

        KaiDesktopAgent(direction="right", presses=1).run_fast()
        KaiWebAgent(url=GOOGLE_DOC_URL).run_fast()
        KaiClipboardAgent(message=entry).run_fast()
        KaiDesktopAgent(direction="left", presses=1).run_fast()

        print(f"[NAVIGATOR] {agent_name} response appended to Doc")

        # Toggle for next cycle
        self.agent_toggle = not self.agent_toggle

    def run(self, cycles=4):
        for _ in range(cycles):
            self.run_cycle()
            time.sleep(1)


if __name__ == "__main__":
    navigator = DocLoopNavigator()
    navigator.run(cycles=4)
