import subprocess
from logger import Logger

class ClipboardManager:
    def __init__(self, logger=None):
        self.logger = logger or Logger()

    def copy_image_to_clipboard(self, image_path):
        applescript = f'''
        tell application "System Events"
            set the clipboard to (read (POSIX file "{image_path}") as «class PNGf»)
        end tell
        '''
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True)
        success = result.returncode == 0
        self.logger.info("Image copied to clipboard" if success else "Clipboard copy failed")
        return success

    def verify_clipboard_has_image(self):
        applescript = '''
        tell application "System Events"
            set clipboardInfo to the clipboard info
            set clipboardType to (clipboardInfo as string)
            return clipboardType
        end tell
        '''
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        return "image" in result.stdout.lower()