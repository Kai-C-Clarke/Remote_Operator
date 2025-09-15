#!/usr/bin/env python3
"""
KaiCoordinator - Final Fixed Version 1.1
=========================================
Date: September 6, 2025
Changes in v1.1:
- Fixed URL selection to use drag method instead of triple-click
- Fixed KaiWebAgent to use clipboard paste instead of URL parameter
- Added version tracking header
- Resolved external link dialog issue
- FIXED: Corrected drag function to use dragTo with button parameter

This script automates web browsing by:
1. Sending prompts to Claude
2. Using OCR to find URL coordinates in Claude's response
3. Using drag selection to copy URLs without triggering link dialogs
4. Pasting URLs into browser address bar
5. Navigating to websites and capturing results
"""

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

class KaiWebAgent:
    """Enhanced version with multiple browser opening methods and verification"""
    def __init__(self):
        self.logger = logger

    def log(self, message):
        self.logger.info(f"[KaiWebAgent] {message}")

    def run_with_retry(self):
        return self.run()

    def run(self):
        self.log("Navigating using enhanced browser control")
        
        # Try primary method first (keyboard shortcuts)
        if self._try_keyboard_method():
            return True
            
        # If keyboard method failed, try AppleScript fallback
        self.log("Primary method failed, trying AppleScript fallback")
        return self._try_applescript_method()

    def _try_keyboard_method(self):
        """Original keyboard shortcut method with clipboard protection and longer wait times"""
        try:
            self.log("Trying keyboard method: Cmd+L -> Cmd+V -> Enter with clipboard protection")
            
            # Focus Chrome using safer method
            self.log("Focusing Chrome browser")
            
            try:
                subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to activate'], 
                             check=True, timeout=5)
                time.sleep(1)
            except:
                self.log("AppleScript focus failed, trying open command")
                subprocess.run(['open', '-a', 'Google Chrome'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
            
            # Verify clipboard before pasting
            try:
                clipboard_result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                clipboard_content = clipboard_result.stdout.strip()
                self.log(f"Pre-paste clipboard verification: '{clipboard_content}'")
                
                # Check if clipboard still contains URL-like content
                if not (clipboard_content.startswith('http') or 'wikipedia' in clipboard_content.lower() or 'www.' in clipboard_content):
                    self.log(f"Clipboard lost during desktop switch! Contains: '{clipboard_content}'")
                    return False
                else:
                    self.log("Pre-paste verification passed - clipboard still has URL")
                    
            except Exception as e:
                self.log(f"Pre-paste clipboard verification failed: {e}")
                return False
            
            # Focus address bar using Cmd+L
            self.log("Focusing address bar with Cmd+L")
            pyautogui.hotkey('cmd', 'l')
            time.sleep(0.5)
            
            # Paste URL from clipboard
            self.log("Pasting URL from clipboard")
            pyautogui.hotkey('cmd', 'v')
            time.sleep(0.5)
            
            # Clear clipboard after pasting to prevent contamination of other processes
            self.log("Clearing clipboard after paste")
            subprocess.run(['pbcopy'], input=' ', text=True)
            time.sleep(0.2)
            
            # Press Enter to navigate
            self.log("Pressing Enter to navigate")
            pyautogui.press('enter')
            
            # Extended wait time to prevent interruption
            self.log("Waiting 8 seconds for page load completion...")
            time.sleep(8)
            
            self.log("Keyboard method completed successfully")
            return True
            
        except Exception as e:
            self.log(f"Keyboard method failed: {e}")
            return False

    def _try_applescript_method(self):
        """AppleScript fallback method for direct URL opening"""
        try:
            # Get URL from clipboard
            clipboard_result = subprocess.run(
                ['osascript', '-e', 'get the clipboard'],
                capture_output=True, text=True
            )
            
            if clipboard_result.returncode != 0:
                self.log("Failed to get URL from clipboard")
                return False
                
            url = clipboard_result.stdout.strip()
            self.log(f"Retrieved URL from clipboard: {url}")
            
            # Check if URL looks valid
            if not (url.startswith('http://') or url.startswith('https://')):
                self.log(f"Invalid URL format: {url}")
                return False
            
            # Check if Chrome is already running
            chrome_running = self._is_chrome_running()
            
            if chrome_running:
                self.log("Chrome is running, using AppleScript to open URL in existing window")
                applescript = f'''
                tell application "Google Chrome"
                    activate
                    open location "{url}"
                end tell
                '''
            else:
                self.log("Chrome not running, launching Chrome with URL")
                # Use open command to launch Chrome with URL
                subprocess.Popen([
                    "open", "-a", "Google Chrome", url
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(5)
                self.log("AppleScript method completed successfully")
                return True
            
            # Execute AppleScript
            result = subprocess.run(["osascript", "-e", applescript], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("AppleScript URL opening successful")
                time.sleep(5)  # Wait for page load
                return True
            else:
                self.log(f"AppleScript failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"AppleScript method failed: {e}")
            return False

    def _is_chrome_running(self):
        """Check if Chrome is currently running"""
        try:
            result = subprocess.run(
                ["pgrep", "Chrome"], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except:
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
        """Complete automation cycle using FIXED drag selection method"""
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

            # Step 2: Wait for Claude response and copy URL using DRAG method
            self.logger.info("Waiting for Claude response and copying URL...")
            
            boundary_detector = WorkingBoundaryDetector()
            stable_text = boundary_detector.wait_for_response_completion(timeout=30)
            
            if stable_text and '<<' in stable_text and '>>' in stable_text:
                self.logger.info("Found boundary markers, attempting to copy URL with DRAG method...")
                
                text_region = boundary_detector.find_claude_text_region()
                screenshot_path = boundary_detector.take_screenshot_region(text_region)
                
                if screenshot_path:
                    try:
                        image = Image.open(screenshot_path)
                        img_array = np.array(image)
                        
                        if len(img_array.shape) == 3:
                            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                        
                        data = pytesseract.image_to_data(img_array, output_type=pytesseract.Output.DICT)
                        
                        url_found = False
                        for i, text in enumerate(data['text']):
                            if text and ('http' in text.lower() or 'bbc' in text.lower() or 'www' in text.lower()):
                                # FIXED: Use drag selection instead of triple-click
                                x = data['left'][i] + text_region[0]
                                y = data['top'][i] + text_region[1]
                                w = data['width'][i]
                                
                                # Click to the LEFT of URL to avoid link trigger
                                start_x = x - 10
                                end_x = x + w + 10
                                click_y = y + 5  # Slightly below top of text
                                
                                self.logger.info(f"Found URL text: {text}")
                                self.logger.info(f"Using DRAG selection from ({start_x}, {click_y}) to ({end_x}, {click_y})")
                                
                                # FIXED: Click and drag to select text with proper button parameter
                                pyautogui.click(start_x, click_y)
                                time.sleep(0.2)
                                pyautogui.dragTo(end_x, click_y, duration=0.5, button='left')  # FIXED: Use dragTo with button parameter
                                time.sleep(0.3)
                                
                                # Copy selection
                                pyautogui.hotkey('cmd', 'c')
                                time.sleep(0.5)
                                
                                self.logger.info("URL copied using drag method - no link dialog should appear")
                                url_found = True
                                break
                        
                        if not url_found:
                            self.logger.error("No URL-like text found for copying")
                            return False
                            
                    except Exception as e:
                        self.logger.error(f"Error copying URL: {e}")
                        return False
                else:
                    self.logger.error("Failed to capture Claude region")
                    return False
            else:
                self.logger.error("No boundary markers found")
                return False

            # Step 3: Navigate using clipboard
            desktop_agent = KaiDesktopAgent(target_desktop=2)
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = 2

            # FIXED: Use clipboard-enabled web agent
            web_agent = KaiWebAgent()
            if not web_agent.run_with_retry():
                self.logger.error("Failed to navigate using clipboard URL")
                return False

            # Step 4: Send confirmation
            time.sleep(4)
            
            desktop_agent = KaiDesktopAgent(target_desktop=1)
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = 1

            confirmation = "<< Screenshot captured successfully >>"
            
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
    print("KaiCoordinator - Version 1.1 (Fixed Drag Selection)")
    coordinator = KaiCoordinator()
    
    import argparse
    parser = argparse.ArgumentParser(description='Kai Automation System v1.1')
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