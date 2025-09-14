import pyautogui
import time
from PIL import Image
import pytesseract
import numpy as np
import cv2
from logger import Logger

class ScreenManager:
    def __init__(self, logger=None):
        self.logger = logger or Logger()

    def take_full_screenshot(self, path=None):
        img = pyautogui.screenshot()
        if path:
            img.save(path)
            self.logger.info(f"Full screenshot saved: {path}")
        return img

    def take_region_screenshot(self, region, path=None):
        img = pyautogui.screenshot(region=region)
        if path:
            img.save(path)
            self.logger.info(f"Region screenshot saved: {path}")
        return img

    def wait_for_claude_response(self, timeout=60):
        """Wait for Claude to finish responding before OCR"""
        self.logger.info("Waiting for Claude response to stabilize...")
        
        last_text = ""
        stable_count = 0
        required_stability = 3
        
        while stable_count < required_stability and timeout > 0:
            img = self.take_full_screenshot()
            current_text = self.extract_text(img)
            
            if current_text == last_text:
                stable_count += 1
                self.logger.info(f"Content stable (count: {stable_count}/{required_stability})")
            else:
                stable_count = 0
                self.logger.info("Content still changing...")
            
            last_text = current_text
            time.sleep(2)
            timeout -= 2
        
        self.logger.info("Claude response stabilized")
        return last_text

    def extract_text(self, img):
        """Enhanced OCR with preprocessing"""
        np_img = np.array(img)
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        
        # Improve contrast
        enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
        
        # Threshold
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Custom config for boundary markers
        custom_config = r'--psm 6 --oem 3 -c tessedit_char_whitelist="<>abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?!:;/-()\n\r"'
        
        text = pytesseract.image_to_string(thresh, config=custom_config)
        return text.strip()