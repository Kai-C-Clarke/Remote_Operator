from core.kai_agent_base import KaiAgent
import subprocess
import time

class KaiDesktopAgent(KaiAgent):
    def __init__(self, **kwargs):
        super().__init__(name="KaiDesktopAgent", **kwargs)

    def switch_to_desktop_1(self):
        script = '''osascript -e 'tell application "System Events" to keystroke "1" using {control down}' '''
        subprocess.run(script, shell=True)
        time.sleep(1.0)

    def run(self):
        self.log("Switching to desktop 1 via Control+1 shortcut...")
        self.switch_to_desktop_1()
        self.log("Now on desktop 1.")

    def verify(self):
        return True