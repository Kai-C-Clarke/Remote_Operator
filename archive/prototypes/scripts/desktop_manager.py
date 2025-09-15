import subprocess
import time
from logger import Logger

class DesktopManager:
    def __init__(self, logger=None):
        self.current_desktop = 0
        self.logger = logger or Logger()

    def switch_desktop(self, target_desktop):
        if self.current_desktop == target_desktop:
            self.logger.info(f"Already on desktop {target_desktop}")
            return True
        try:
            direction = 124 if target_desktop > self.current_desktop else 123
            presses = abs(target_desktop - self.current_desktop)
            for _ in range(presses):
                subprocess.run([
                    "osascript", "-e",
                    f'''tell application "System Events"
                        key code {direction} using control down
                    end tell'''
                ], check=True)
                time.sleep(0.3)
            self.current_desktop = target_desktop
            time.sleep(1.5)
            self.logger.info(f"Switched to desktop {target_desktop}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch desktop: {e}")
            return False