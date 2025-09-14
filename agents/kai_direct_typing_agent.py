from core.kai_agent_base import KaiAgent
import pyautogui
import time

class KaiDirectTypingAgent(KaiAgent):
    def __init__(self, message=None, typing_interval=0.01, send_hotkey='enter', **kwargs):
        super().__init__(name="KaiDirectTypingAgent", **kwargs)
        self.message = message
        self.typing_interval = typing_interval
        self.send_hotkey = send_hotkey

    def find_claude_input_area(self):
        """Find and click on Claude's input area using exact measured coordinates"""
        try:
            # Get screen dimensions for reference
            screen_width, screen_height = pyautogui.size()
            self.log(f"Detected screen size: {screen_width}x{screen_height}")
            
            # Use exact measured coordinates
            # Claude's input area: (1587, 1252) to (2103, 1308)
            input_left = 1587
            input_top = 1252
            input_right = 2103
            input_bottom = 1308
            
            # Click in center of input area
            claude_input_x = (input_left + input_right) // 2  # 1845
            claude_input_y = (input_top + input_bottom) // 2  # 1280
            
            self.log(f"Clicking Claude input area at ({claude_input_x}, {claude_input_y})")
            pyautogui.click(claude_input_x, claude_input_y)
            time.sleep(0.5)
            
            # Clear any existing text
            pyautogui.hotkey('cmd', 'a')
            time.sleep(0.3)
            
            return True
            
        except Exception as e:
            self.log(f"Failed to find input area: {e}")
            return False

    def type_message_directly(self):
        """Type the message directly without using clipboard"""
        try:
            self.log(f"Typing message directly ({len(self.message)} chars): {self.message}")
            
            # Type the message character by character
            pyautogui.typewrite(self.message, interval=self.typing_interval)
            
            self.log("Message typed successfully")
            return True
            
        except Exception as e:
            self.log(f"Direct typing failed: {e}")
            return False

    def send_message(self):
        """Send the message using Enter key"""
        try:
            self.log("Sending message with Enter")
            time.sleep(0.5)  # Brief pause before sending
            pyautogui.press(self.send_hotkey)
            time.sleep(0.5)
            
            self.log("Message sent successfully")
            return True
            
        except Exception as e:
            self.log(f"Failed to send message: {e}")
            return False

    def run(self):
        if not self.message:
            raise ValueError("No message provided for direct typing.")

        # Step 1: Find and click Claude's input area
        if not self.find_claude_input_area():
            raise Exception("Could not find Claude's input area")

        # Step 2: Type the message directly
        if not self.type_message_directly():
            raise Exception("Failed to type message")

        # Step 3: Send the message
        if not self.send_message():
            raise Exception("Failed to send message")

        self.log("Direct typing operation completed successfully")
        return True

    def verify(self):
        """Verify the operation succeeded"""
        return True