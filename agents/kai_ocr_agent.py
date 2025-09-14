from core.kai_agent_base import KaiAgent
import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image
import time
import os

class KaiOCRAgent(KaiAgent):
    def __init__(self, region=None, save_debug=True, **kwargs):
        super().__init__(name="KaiOCRAgent", **kwargs)
        self.region = region  # (x, y, width, height) or None for full screen
        self.save_debug = save_debug
        self.debug_dir = "debug_screenshots"
        if save_debug:
            os.makedirs(self.debug_dir, exist_ok=True)
        self.extracted_text = ""

    def wait_for_content_stability(self, timeout=60, stability_checks=3):
        """Wait for content to stabilize before OCR"""
        self.log("Waiting for content to stabilize...")
        
        last_text = ""
        stable_count = 0
        check_interval = 2
        
        while stable_count < stability_checks and timeout > 0:
            # Capture current content
            current_text = self.capture_and_extract()
            
            if current_text == last_text:
                stable_count += 1
                self.log(f"Content stable (count: {stable_count}/{stability_checks})")
            else:
                stable_count = 0
                self.log("Content still changing...")
            
            last_text = current_text
            time.sleep(check_interval)
            timeout -= check_interval
        
        if stable_count >= stability_checks:
            self.log("Content has stabilized")
            self.extracted_text = last_text
            return last_text
        else:
            self.log("Timeout waiting for stability")
            self.extracted_text = last_text
            return last_text

    def capture_and_extract(self):
        """Capture screenshot and extract text"""
        try:
            # Take screenshot
            if self.region:
                img = pyautogui.screenshot(region=self.region)
                self.log(f"Captured region screenshot: {self.region}")
            else:
                img = pyautogui.screenshot()
                self.log("Captured full screenshot")
            
            # Save debug image if requested
            if self.save_debug:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                debug_path = os.path.join(self.debug_dir, f"ocr_capture_{timestamp}.png")
                img.save(debug_path)
                self.log(f"Debug screenshot saved: {debug_path}")
            
            # Extract text
            text = self.extract_text_from_image(img)
            return text
            
        except Exception as e:
            self.log(f"Screenshot capture failed: {e}")
            return ""

    def extract_text_from_image(self, img):
        """Extract text using OCR with preprocessing"""
        try:
            # Convert PIL to numpy array
            img_array = np.array(img)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Enhance contrast
            enhanced = cv2.convertScaleAbs(img_array, alpha=1.2, beta=10)
            
            # Apply threshold for better OCR
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR configuration optimized for boundary markers
            custom_config = r'--psm 6 --oem 3 -c tessedit_char_whitelist="<>abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?!:;/-()\n\r"'
            
            # Extract text
            text = pytesseract.image_to_string(thresh, config=custom_config)
            
            self.log(f"OCR extracted {len(text)} characters")
            return text.strip()
            
        except Exception as e:
            self.log(f"OCR extraction failed: {e}")
            return ""

    def run(self, wait_for_stability=True):
        """Main OCR operation"""
        if wait_for_stability:
            text = self.wait_for_content_stability()
        else:
            text = self.capture_and_extract()
        
        self.extracted_text = text
        self.log(f"OCR operation completed. Text length: {len(text)}")
        
        if text:
            # Log first 100 characters for debugging
            preview = text.replace('\n', ' ')[:100]
            self.log(f"Text preview: {preview}...")
        
        return text

    def get_extracted_text(self):
        """Get the last extracted text"""
        return self.extracted_text

    def verify(self):
        """Verify OCR operation succeeded"""
        return len(self.extracted_text) > 0