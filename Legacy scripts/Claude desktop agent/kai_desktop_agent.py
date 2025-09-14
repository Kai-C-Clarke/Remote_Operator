from core.kai_agent_base import KaiAgent
import subprocess
import time

class KaiDesktopAgent(KaiAgent):
    def __init__(self, target_desktop=1, **kwargs):
        super().__init__(name="KaiDesktopAgent", **kwargs)
        self.current_desktop = 0  # Assume we start on desktop 0
        self.target_desktop = target_desktop

    def run(self):
        self.log(f"Switching from desktop {self.current_desktop} to desktop {self.target_desktop}")

        if self.current_desktop == self.target_desktop:
            self.log(f"Already on desktop {self.target_desktop}")
            return True

        try:
            # Calculate direction and number of presses needed
            presses_needed = self.target_desktop - self.current_desktop
            
            if presses_needed > 0:
                key_code = "124"  # right arrow
                direction = "right"
            else:
                key_code = "123"  # left arrow  
                direction = "left"
                presses_needed = abs(presses_needed)

            self.log(f"Pressing {direction} arrow {presses_needed} times")

            # Execute the key presses
            for i in range(presses_needed):
                subprocess.run([
                    "osascript", "-e",
                    f'''tell application "System Events"
                        key code {key_code} using control down
                    end tell'''
                ], check=True)
                
                time.sleep(0.3)  # Small delay between presses
                self.log(f"Press {i+1}/{presses_needed} completed")

            # Update current desktop
            self.current_desktop = self.target_desktop
            time.sleep(1.5)  # Wait for desktop switch to complete
            
            self.log(f"Successfully switched to desktop {self.target_desktop}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Desktop switch failed with subprocess error: {e}")
            raise
        except Exception as e:
            self.log(f"Unexpected error during desktop switch: {e}")
            raise

    def verify(self):
        return True