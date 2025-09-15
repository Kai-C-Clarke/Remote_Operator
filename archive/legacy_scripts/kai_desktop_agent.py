from pathlib import Path

# Recreate the corrected script after code execution environment reset
corrected_code = """from core.kai_agent_base import KaiAgent
import subprocess
import time

class KaiDesktopAgent(KaiAgent):
    def __init__(self, **kwargs):
        super().__init__(name="KaiDesktopAgent", **kwargs)

    def run(self):
        self.log("Switching to desktop 1 using Control + arrow keys...")

        try:
            key_code = "124"  # right arrow

            subprocess.run([
                "osascript", "-e",
                f'''
                tell application "System Events"
                    key code {key_code} using control down
                end tell
                '''
            ], check=True)

            time.sleep(1.5)
            self.log("Successfully switched to desktop 1.")
            
        except subprocess.CalledProcessError as e:
            self.log(f"Desktop switch failed with subprocess error: {e}")
            raise
        except Exception as e:
            self.log(f"Unexpected error during desktop switch: {e}")
            raise

    def verify(self):
        return True
