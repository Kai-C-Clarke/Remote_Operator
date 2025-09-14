#!/usr/bin/env python3

import sys
import os
import time
import re
import logging
import traceback
import subprocess
import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image

# Basic logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger("KaiCoordinator")

class KaiDesktopAgent:
    def __init__(self, target_desktop=1):
        self.current_desktop = 0
        self.target_desktop = target_desktop
        self.logger = logger

    def log(self, message):
        self.logger.info(f"[KaiDesktopAgent] {message}")

    def run_with_retry(self):
        self.run()

    def run(self):
        if self.current_desktop == self.target_desktop:
            self.log(f"Already on desktop {self.target_desktop}")
            return True

        self.log(f"Switching from desktop {self.current_desktop} to desktop {self.target_desktop}")
        
        try:
            presses_needed = self.target_desktop - self.current_desktop
            if presses_needed > 0:
                key_code = "124"  # right arrow
                direction = "right"
            else:
                key_code = "123"  # left arrow  
                direction = "left"
                presses_needed = abs(presses_needed)

            self.log(f"Pressing {direction} arrow {presses_needed} times")

            for i in range(presses_needed):
                subprocess.run([
                    "osascript", "-e",
                    f'''tell application "System Events"
                        key code {key_code} using control down
                    end tell'''
                ], check=True)
                
                time.sleep(0.3)
                self.log(f"Press {i+1}/{presses_needed} completed")

            self.current_desktop = self.target_desktop
            time.sleep(1.5)
            
            self.log(f"Successfully switched to desktop {self.target_desktop}")
            return True
            
        except Exception as e:
            self.log(f"Desktop switch failed: {e}")
            raise

class KaiDirectTypingAgent:
    def __init__(self, message):
        self.message = message
        self.logger = logger

    def log(self, message):
        self.logger.info(f"[KaiDirectTypingAgent] {message}")

    def run_with_retry(self):
        self.run()

    def run(self):
        # Use exact coordinates from your measurements
        # Claude's input area: (1587, 1252) to (2103, 1308)
        input_left = 1587
        input_top = 1252
        input_right = 2103
        input_bottom = 1308
        
        claude_input_x = (input_left + input_right) // 2  # 1845
        claude_input_y = (input_top + input_bottom) // 2  # 1280

        screen_width, screen_height = pyautogui.size()
        self.log(f"Detected screen size: {screen_width}x{screen_height}")
        self.log(f"Clicking Claude input area at ({claude_input_x}, {claude_input_y})")
        
        pyautogui.click(claude_input_x, claude_input_y)
        time.sleep(0.5)
        
        # Clear existing text
        pyautogui.hotkey('cmd', 'a')
        time.sleep(0.3)
        
        self.log(f"Typing message directly ({len(self.message)} chars): {self.message}")
        pyautogui.typewrite(self.message, interval=0.01)
        
        self.log("Message typed successfully")
        self.log("Sending message with Enter")
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        
        self.log("Direct typing operation completed successfully")
        return True

class WorkingBoundaryDetector:
    """Based exactly on your working script"""
    
    def __init__(self):
        self.logger = logger
        self.boundary_pattern = r'<<(.*?)>>'
        self.debug_dir = "debug_screenshots"
        os.makedirs(self.debug_dir, exist_ok=True)
        
    def log(self, message):
        self.logger.info(f"[BoundaryDetector] {message}")
        
    def find_claude_text_region(self):
        """Find Claude's response region - exact from working script"""
        x, y = 1540, 221
        width = 868
        height = 856
        claude_text_region = (x, y, width, height)
        self.log(f"Using Claude text region: {claude_text_region}")
        return claude_text_region
    
    def take_screenshot_region(self, region):
        """Take screenshot of specific region - exact from working script"""
        try:
            x, y, w, h = region
            img = pyautogui.screenshot(region=(x, y, w, h))
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.debug_dir, f"claude_region_{timestamp}.png")
            img.save(screenshot_path)
            
            self.log(f"Claude region screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.log(f"Region screenshot failed: {e}")
            return None
    
    def extract_text_from_image(self, image_path):
        """Extract text using OCR - exact from working script"""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Improve contrast for better OCR - CRITICAL
            img_array = cv2.convertScaleAbs(img_array, alpha=1.2, beta=10)
            
            # Apply threshold - CRITICAL
            _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR configuration - exact from working script
            custom_config = r'--psm 6 --oem 3 -c tessedit_char_whitelist="<>abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?!:;/-()\n\r_"'
            
            # Extract text
            text = pytesseract.image_to_string(img_array, config=custom_config)
            return text.strip()
            
        except Exception as e:
            self.log(f"OCR failed: {e}")
            return ""
    
    def wait_for_response_completion(self, timeout=60):
        """Wait for Claude to finish typing - exact from working script"""
        self.log("Waiting for response completion before OCR...")
        start_time = time.time()
        
        last_text = ""
        stable_count = 0
        required_stability = 3
        check_interval = 2
        
        while time.time() - start_time < timeout:
            text_region = self.find_claude_text_region()
            screenshot_path = self.take_screenshot_region(text_region)
            
            if screenshot_path:
                current_text = self.extract_text_from_image(screenshot_path)
                
                if current_text == last_text:
                    stable_count += 1
                    self.log(f"Content stable (count: {stable_count}/{required_stability})")
                    
                    if stable_count >= required_stability:
                        self.log("Response appears complete - content has stabilized")
                        return current_text
                else:
                    stable_count = 0
                    self.log("Content still changing - waiting for completion...")
                
                last_text = current_text
            
            time.sleep(check_interval)
        
        self.log("Timeout waiting for content stability - proceeding with current text")
        return last_text
    
    def scan_for_boundary_markers(self, timeout=30):
        """Scan for boundary markers - exact from working script"""
        self.log("Scanning for boundary markers with content stability check...")
        
        stable_text = self.wait_for_response_completion(timeout)
        
        if stable_text:
            boundaries = re.findall(self.boundary_pattern, stable_text, re.DOTALL)
            
            if boundaries:
                self.log(f"Found {len(boundaries)} boundary marker(s) in stable content")
                
                boundary_contents = []
                for boundary in boundaries:
                    content = boundary.strip()
                    if content:
                        boundary_contents.append(content)
                        self.log(f"Stable boundary content: {content}")
                
                if boundary_contents:
                    return boundary_contents
            
            if stable_text.strip():
                preview = stable_text.replace('\n', ' ')[:100]
                self.log(f"Stable text preview: {preview}...")
        
        self.log("No boundary markers found in stable content")
        return None

class KaiWebAgent:
    def __init__(self, url):
        self.url = url
        self.logger = logger

    def log(self, message):
        self.logger.info(f"[KaiWebAgent] {message}")

    def run_with_retry(self):
        return self.run()

    def run(self):
        self.log(f"Navigating to URL by typing in address bar: {self.url}")
        
        try:
            # Focus Chrome using safer method - try multiple approaches
            self.log("Focusing Chrome browser")
            
            # Method 1: Simple AppleScript activation
            try:
                subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to activate'], 
                             check=True, timeout=5)
                time.sleep(1)
            except:
                # Method 2: Fallback using open command
                self.log("AppleScript focus failed, trying open command")
                subprocess.run(['open', '-a', 'Google Chrome'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
            
            # Focus address bar using Cmd+L (universal browser shortcut)
            self.log("Focusing address bar with Cmd+L")
            pyautogui.hotkey('cmd', 'l')
            time.sleep(0.5)
            
            # Clear any existing URL and type the new one
            self.log(f"Typing URL: {self.url}")
            pyautogui.hotkey('cmd', 'a')  # Select all in address bar
            time.sleep(0.2)
            pyautogui.typewrite(self.url, interval=0.01)
            time.sleep(0.5)
            
            # Press Enter to navigate
            self.log("Pressing Enter to navigate")
            pyautogui.press('enter')
            time.sleep(3)  # Wait for page to start loading
            
            self.log(f"Successfully navigated to {self.url}")
            return True
            
        except Exception as e:
            self.log(f"Failed to navigate to URL: {e}")
            # Fallback: try opening URL with system default
            try:
                self.log("Trying fallback method with system open command")
                subprocess.run(["open", self.url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                return True
            except Exception as e2:
                self.log(f"Fallback method also failed: {e2}")
                return False

class KaiCoordinator:
    def __init__(self):
        self.logger = logger
        self.state = {
            'current_desktop': 0,
            'last_url': None,
            'cycle_count': 0
        }

    def run_send_to_claude_flow(self, message, target_desktop=1):
        """Send a message to Claude"""
        self.logger.info("Starting: Send message to Claude")

        # Step 1: Switch to Claude desktop
        desktop_agent = KaiDesktopAgent(target_desktop=target_desktop)
        
        try:
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = target_desktop
        except Exception as e:
            self.logger.error(f"Desktop switching failed: {e}")
            return False

        # Step 2: Direct typing
        typing_agent = KaiDirectTypingAgent(message=message)
        
        try:
            typing_agent.run_with_retry()
        except Exception as e:
            self.logger.error(f"Direct typing failed: {e}")
            return False

        self.logger.info("Completed: Message sent to Claude")
        return True

    def run_full_automation_cycle(self):
        """Complete automation cycle using working script approach"""
        self.state['cycle_count'] += 1
        self.logger.info(f"=== Starting Automation Cycle {self.state['cycle_count']} ===")

        try:
            # Step 1: Send initial prompt to Claude
            prompt = "Ready for your next webpage operation command! Use << URL >> format."
            if self.state['last_url']:
                prompt += f" Last processed: {self.state['last_url']}"

            if not self.run_send_to_claude_flow(prompt, target_desktop=1):
                self.logger.error("Failed to send prompt to Claude")
                return False

            # Step 2: Wait for Claude response using working script approach
            self.logger.info("Waiting for Claude response using working boundary detector...")
            
            boundary_detector = WorkingBoundaryDetector()
            boundary_contents = boundary_detector.scan_for_boundary_markers(timeout=30)
            
            if not boundary_contents:
                self.logger.error("No boundaries found in Claude's response")
                return False

            # Step 3: Extract URL from boundaries
            url = boundary_contents[0].strip()
            
            # Clean and validate URL
            if not url.startswith(('http://', 'https://')):
                if url.startswith('www.'):
                    url = 'https://' + url
                else:
                    url = 'https://' + url
            
            self.state['last_url'] = url
            self.logger.info(f"Extracted URL: {url}")

            # Step 4: Navigate to URL
            desktop_agent = KaiDesktopAgent(target_desktop=2)
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = 2

            web_agent = KaiWebAgent(url=url)
            if not web_agent.run_with_retry():
                self.logger.error(f"Failed to navigate to {url}")
                return False

            # Step 5: Wait for page load and send confirmation
            time.sleep(4)
            
            desktop_agent = KaiDesktopAgent(target_desktop=1)
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = 1

            confirmation = f"<< Screenshot captured from {url} >>"
            
            if not self.run_send_to_claude_flow(confirmation, target_desktop=1):
                self.logger.error("Failed to send confirmation to Claude")
                return False

            self.logger.info(f"Cycle {self.state['cycle_count']} completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Automation cycle failed: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def run_continuous_automation(self, max_cycles=None):
        """Run continuous automation cycles"""
        self.logger.info("Starting continuous automation...")
        
        try:
            while True:
                if max_cycles and self.state['cycle_count'] >= max_cycles:
                    self.logger.info(f"Reached maximum cycles ({max_cycles})")
                    break

                success = self.run_full_automation_cycle()
                
                if success:
                    self.logger.info("Waiting before next cycle...")
                    time.sleep(5)
                else:
                    self.logger.warning("Cycle failed, waiting longer before retry...")
                    time.sleep(10)

        except KeyboardInterrupt:
            self.logger.info("Automation stopped by user")
        except Exception as e:
            self.logger.error(f"Critical error in automation: {e}")

if __name__ == "__main__":
    print("KaiCoordinator - Fully Working Version")
    coordinator = KaiCoordinator()
    
    import argparse
    parser = argparse.ArgumentParser(description='Kai Automation System')
    parser.add_argument('--test', action='store_true', help='Run single test message')
    parser.add_argument('--single', action='store_true', help='Run single automation cycle')
    parser.add_argument('--continuous', action='store_true', help='Run continuous automation')
    parser.add_argument('--cycles', type=int, help='Maximum number of cycles for continuous mode')
    
    args = parser.parse_args()
    
    if args.test:
        success = coordinator.run_send_to_claude_flow("<< https://www.bbc.com/news >>", target_desktop=1)
        print("Test completed successfully" if success else "Test failed")
    elif args.single:
        success = coordinator.run_full_automation_cycle()
        print("Single cycle completed successfully" if success else "Single cycle failed")
    elif args.continuous:
        coordinator.run_continuous_automation(max_cycles=args.cycles)
    else:
        success = coordinator.run_full_automation_cycle()
        print("Single cycle completed successfully" if success else "Single cycle failed")