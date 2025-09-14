from core.kai_agent_base import KaiAgent
import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image
import time
import os
import re

class KaiClaudeRegionAgent(KaiAgent):
    def __init__(self, **kwargs):
        super().__init__(name="KaiClaudeRegionAgent", **kwargs)
        # Use exact coordinates from working script
        self.claude_region = (1533, 217, 839, 881)  # (x, y, width, height)
        self.boundary_pattern = r'<<(.*?)>>'
        self.debug_dir = "debug_screenshots"
        os.makedirs(self.debug_dir, exist_ok=True)

    def take_screenshot_region(self, region):
        """Take screenshot of specific region - exactly like working script"""
        try:
            x, y, w, h = region
            img = pyautogui.screenshot(region=(x, y, w, h))
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.debug_dir, f"claude_region_{timestamp}.png")
            img.save(screenshot_path)
            
            self.log(f"Claude region screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.log(f"Claude region screenshot failed: {e}")
            return None

    def extract_text_from_image(self, image_path):
        """Extract text using OCR with preprocessing - exactly like working script"""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Improve contrast for better OCR - CRITICAL STEP
            img_array = cv2.convertScaleAbs(img_array, alpha=1.2, beta=10)
            
            # Apply threshold - CRITICAL STEP
            _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR configuration with proper character whitelist for URLs - EXACT FROM WORKING SCRIPT
            custom_config = r'--psm 6 --oem 3 -c tessedit_char_whitelist="<>abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?!:;/-()\n\r_"'
            
            # Extract text
            text = pytesseract.image_to_string(img_array, config=custom_config)
            return text.strip()
            
        except Exception as e:
            self.log(f"OCR failed: {e}")
            return ""

    def wait_for_response_completion(self, timeout=60):
        """Wait for Claude to finish typing - exactly like working script"""
        self.log("Waiting for Claude response completion before OCR...")
        start_time = time.time()
        
        last_text = ""
        stable_count = 0
        required_stability = 3  # 3 consecutive identical reads = content is stable
        check_interval = 2  # Check every 2 seconds
        
        while time.time() - start_time < timeout:
            # Get current text from Claude's response area
            screenshot_path = self.take_screenshot_region(self.claude_region)
            
            if screenshot_path:
                current_text = self.extract_text_from_image(screenshot_path)
                
                if current_text == last_text:
                    stable_count += 1
                    self.log(f"Claude content stable (count: {stable_count}/{required_stability})")
                    
                    if stable_count >= required_stability:
                        self.log("Claude response appears complete - content has stabilized")
                        return current_text
                else:
                    stable_count = 0  # Reset if content changed
                    self.log("Claude content still changing - waiting for completion...")
                
                last_text = current_text
            
            time.sleep(check_interval)
        
        self.log("Timeout waiting for Claude content stability - proceeding with current text")
        return last_text

    def wait_for_response_completion_fast(self, timeout=30):
        """Speed-optimized response completion detection"""
        self.log("Fast waiting for Claude response completion...")
        start_time = time.time()
        
        last_text = ""
        stable_count = 0
        required_stability = 2  # Reduced from 3
        check_interval = 1.0  # Reduced from 2.0s
        
        while time.time() - start_time < timeout:
            screenshot_path = self.take_screenshot_region(self.claude_region)
            
            if screenshot_path:
                current_text = self.extract_text_from_image(screenshot_path)
                
                if current_text == last_text:
                    stable_count += 1
                    self.log(f"Fast content stable (count: {stable_count}/{required_stability})")
                    
                    if stable_count >= required_stability:
                        self.log("Fast response completion detected")
                        return current_text
                else:
                    stable_count = 0
                    self.log("Content still changing - fast monitoring...")
                
                last_text = current_text
            
            time.sleep(check_interval)
        
        self.log("Fast timeout - proceeding with current text")
        return last_text

    def scan_for_boundary_markers(self, text):
        """Scan text for boundary markers - exactly like working script"""
        if not text:
            self.log("No text provided for boundary scanning")
            return None
            
        # Look for boundary markers in the text
        boundaries = re.findall(self.boundary_pattern, text, re.DOTALL)
        
        if boundaries:
            self.log(f"Found {len(boundaries)} boundary marker(s) in Claude content")
            
            # Return the content of all boundaries found
            boundary_contents = []
            for boundary in boundaries:
                content = boundary.strip()
                if content:
                    boundary_contents.append(content)
                    self.log(f"Stable boundary content: {content}")
            
            if boundary_contents:
                return boundary_contents
        
        # Log what we're seeing for debugging
        if text.strip():
            preview = text.replace('\n', ' ')[:100]
            self.log(f"Claude text preview: {preview}...")
        
        self.log("No boundary markers found in Claude content")
        return None

    def run(self, wait_for_stability=True):
        """Main operation - capture Claude's region and extract boundaries"""
        self.log("Starting Claude region capture and boundary detection")
        
        if wait_for_stability:
            # Wait for Claude response to stabilize
            stable_text = self.wait_for_response_completion()
        else:
            # Just capture current content
            screenshot_path = self.take_screenshot_region(self.claude_region)
            if screenshot_path:
                stable_text = self.extract_text_from_image(screenshot_path)
            else:
                stable_text = ""
        
        self.log(f"Claude region OCR completed. Text length: {len(stable_text)}")
        
        if stable_text:
            # Look for boundary markers
            boundary_contents = self.scan_for_boundary_markers(stable_text)
            
            if boundary_contents:
                self.log(f"Successfully extracted boundaries: {boundary_contents}")
                return {
                    'text': stable_text,
                    'boundaries': boundary_contents,
                    'success': True
                }
            else:
                self.log("No boundaries found in Claude response")
                return {
                    'text': stable_text,
                    'boundaries': [],
                    'success': False
                }
        else:
            self.log("No text captured from Claude region")
            return {
                'text': "",
                'boundaries': [],
                'success': False
            }

    def verify(self):
        """Verify operation succeeded"""
        return True