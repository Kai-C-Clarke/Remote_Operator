from core.kai_agent_base import KaiAgent
import subprocess
import time

class KaiDesktopAgent(KaiAgent):
    def __init__(self, direction="right", presses=1, **kwargs):
        """
        direction: "left" or "right"
        presses: how many desktops to move
        """
        super().__init__(name="KaiDesktopAgent", **kwargs)
        self.direction = direction
        self.presses = presses

    def run(self):
        self.log(f"Switching {self.direction} {self.presses} desktop(s)")

        try:
            if self.direction == "right":
                key_code = "124"  # right arrow
            else:
                key_code = "123"  # left arrow

            for i in range(self.presses):
                subprocess.run([
                    "osascript", "-e",
                    f'''tell application "System Events"
                            key code {key_code} using control down
                        end tell'''
                ], check=True)
                time.sleep(0.5)

            time.sleep(1.5)  # let the animation finish
            self.log(f"Switched {self.direction} {self.presses} desktop(s)")
            return True

        except Exception as e:
            self.log(f"Desktop switch failed: {e}")
            return False

    def run_fast(self):
        """Speed-optimized desktop switching"""
        self.log(f"Fast switching {self.direction} {self.presses} desktop(s)")

        try:
            if self.direction == "right":
                key_code = "124"  # right arrow
            else:
                key_code = "123"  # left arrow

            for i in range(self.presses):
                subprocess.run([
                    "osascript", "-e",
                    f'''tell application "System Events"
                            key code {key_code} using control down
                        end tell'''
                ], check=True)
                time.sleep(0.25)  # Reduced from 0.5s

            time.sleep(0.8)  # Reduced from 1.5s
            self.log(f"Fast switched {self.direction} {self.presses} desktop(s)")
            return True

        except Exception as e:
            self.log(f"Fast desktop switch failed: {e}")
            return False

    def verify(self):
        return True