import pyautogui
from logger import Logger

class ClaudeUI:
    def __init__(self, logger=None):
        self.logger = logger or Logger()

    def find_input_box(self):
        # TODO: Use OCR or template matching to find the input box region
        # For now, return default coordinates
        screen_width, screen_height = pyautogui.size()
        return (screen_width // 2, screen_height - 150)

    def focus_and_type(self, text):
        x, y = self.find_input_box()
        pyautogui.click(x, y)
        pyautogui.hotkey('cmd', 'a')
        pyautogui.typewrite(text, interval=0.02)
        pyautogui.press('enter')
        self.logger.info(f"Typed text in Claude UI: {text}")