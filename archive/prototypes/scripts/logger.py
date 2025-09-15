import logging
import os
import time
import subprocess

class Logger:
    def __init__(self, log_file='webpage_operator.log', debug_dir='debug_screenshots'):
        os.makedirs(debug_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.debug_dir = debug_dir

    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def warning(self, msg): self.logger.warning(msg)

    def save_screenshot(self, img, purpose='debug'):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.debug_dir, f"{purpose}_{timestamp}.png")
        img.save(path)
        self.info(f"Debug screenshot saved: {path}")
        return path

    def notify(self, title, message):
        """Send macOS notification for manual intervention or critical error."""
        try:
            applescript = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", applescript], check=True)
            self.info(f"User notified: {title} - {message}")
        except Exception as e:
            self.error(f"Notification failed: {e}")