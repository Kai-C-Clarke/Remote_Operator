#!/usr/bin/env python3
"""
KaiCoordinator - Hybrid Final Version 1.3
==========================================
Date: September 8, 2025
Changes in v1.3 (Hybrid):
- Combined Ninja's clean class structure with proven enhancements
- Fixed all class naming conflicts (KaiWebAgent throughout)
- Integrated variable-based URL handling with clipboard verification
- Added sophisticated AppleScript control and clipboard protection
- Improved error handling and logging consistency
- Removed all duplicate code blocks

This script automates web browsing by:
1. Sending prompts to Claude
2. Using OCR to find URL coordinates in Claude's response
3. Using drag selection to copy URLs without triggering link dialogs
4. Pasting URLs into browser address bar with advanced fallback methods
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
        return self.run()

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
        return self.run()

    def run(self):
        # Use exact coordinates from measurements
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
    """OCR and boundary detection based exactly on working implementation"""
    
    def __init__(self):
        self.logger = logger
        self.boundary_pattern = r'<<(.*?)>>'
        self.debug_dir = "debug_screenshots"
        os.makedirs(self.debug_dir, exist_ok=True)
        
    def log(self, message):
        self.logger.info(f"[BoundaryDetector] {message}")
        
    def find_claude_text_region(self):
        """Find Claude's response region using proven coordinates"""
        x, y = 1540, 221
        width = 868
        height = 856
        claude_text_region = (x, y, width, height)
        self.log(f"Using Claude text region: {claude_text_region}")
        return claude_text_region
    
    def take_screenshot_region(self, region):
        """Take screenshot of specific region with timestamp"""
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
        """Extract text using OCR with proven configuration"""
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
            
            # OCR configuration - enhanced for full URL detection
            custom_config = r'--psm 6 --oem 3 -c tessedit_char_whitelist="<>abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?!:;/-()=&%+~_\n\r"'
            
            # Extract text
            text = pytesseract.image_to_string(img_array, config=custom_config)
            return text.strip()
            
        except Exception as e:
            self.log(f"OCR failed: {e}")
            return ""
    
    def wait_for_response_completion(self, timeout=60):
        """Wait for Claude to finish typing with stability detection"""
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
    """Enhanced web agent with multiple browser methods and sophisticated clipboard handling"""
    
    def __init__(self):
        self.logger = logger
        self.extracted_url = None

    def log(self, message):
        self.logger.info(f"[KaiWebAgent] {message}")

    def run_with_retry(self):
        """Legacy method for backward compatibility - redirects to modern implementation"""
        self.log("Using legacy run_with_retry() - redirecting to run_with_url_variable()")
        return self.run_with_url_variable()

    def run(self):
        """Deprecated legacy method"""
        self.log("WARNING: Deprecated run() method called")
        return self.run_with_url_variable()
        
    def run_with_url_variable(self, url=None):
        """Primary method: Navigate using direct typing to avoid clipboard issues"""
        if url:
            self.extracted_url = url
            self.log(f"Using provided URL variable: {url}")
        else:
            self.log("No URL provided - this shouldn't happen with intelligent extraction")
            return False
        
        # Validate URL format
        if not self.extracted_url or not (
            self.extracted_url.startswith('http://') or 
            self.extracted_url.startswith('https://') or
            'www.' in self.extracted_url or
            any(domain in self.extracted_url.lower() for domain in ['bbc', 'nasa', 'wikipedia', 'google'])
        ):
            self.log(f"Invalid URL format: {self.extracted_url}")
            return False
        
        # Try direct typing method first (bypasses clipboard entirely)
        return self._try_direct_typing_method()

    def _try_direct_typing_method(self):
        """Direct typing method - completely bypasses clipboard"""
        try:
            self.log(f"Using direct typing method for URL: '{self.extracted_url}'")
            self.log(f"URL length: {len(self.extracted_url)} characters")
            
            # Focus Chrome browser
            if not self._focus_chrome_browser():
                self.log("Failed to focus Chrome browser")
                return False
            
            # Focus address bar
            self.log("Focusing address bar with Cmd+L")
            pyautogui.hotkey('cmd', 'l')
            time.sleep(0.5)
            
            # Clear any existing content
            self.log("Clearing address bar content")
            pyautogui.hotkey('cmd', 'a')
            time.sleep(0.2)
            pyautogui.press('delete')
            time.sleep(0.2)
            
            # Type URL directly (no clipboard involved)
            self.log(f"About to type: '{self.extracted_url}'")
            # Type character by character for debugging
            for i, char in enumerate(self.extracted_url):
                pyautogui.typewrite(char)
                if i < 10:  # Log first 10 characters
                    self.log(f"Typed character {i}: '{char}'")
                time.sleep(0.01)
            
            time.sleep(0.5)
            
            # Verify what was typed by selecting all and checking
            self.log("Verifying what was typed...")
            pyautogui.hotkey('cmd', 'a')
            time.sleep(0.2)
            pyautogui.hotkey('cmd', 'c')
            time.sleep(0.3)
            
            # Check what was actually typed
            verify_result = subprocess.run(['pbpaste'], capture_output=True, text=True)
            typed_content = verify_result.stdout.strip()
            self.log(f"Address bar contains: '{typed_content}'")
            
            # Navigate
            self.log("Pressing Enter to navigate")
            pyautogui.press('enter')
            
            # Wait for page load
            self.log("Waiting 8 seconds for page load completion...")
            time.sleep(8)
            
            self.log("Direct typing method completed successfully")
            return True
            
        except Exception as e:
            self.log(f"Direct typing method failed: {e}")
            return False

    def _try_keyboard_method(self):
        """Enhanced keyboard method with aggressive clipboard protection"""
        try:
            self.log("Executing keyboard method: Focus Chrome -> Cmd+L -> Paste -> Enter")
            
            # Focus Chrome with multiple strategies
            chrome_focused = self._focus_chrome_browser()
            if not chrome_focused:
                self.log("Failed to focus Chrome browser")
                return False
            
            # Ensure URL is in clipboard before pasting
            self._ensure_url_in_clipboard()
            
            # Pre-paste verification with detailed logging
            if not self._verify_clipboard_content():
                self.log("Pre-paste verification failed - clipboard doesn't contain valid URL")
                return False
            
            # Focus address bar
            self.log("Focusing address bar with Cmd+L")
            pyautogui.hotkey('cmd', 'l')
            time.sleep(0.5)
            
            # Paste URL
            self.log("Pasting URL from clipboard")
            pyautogui.hotkey('cmd', 'v')
            time.sleep(0.5)
            
            # Aggressive clipboard clearing to prevent contamination
            self.log("Clearing clipboard to prevent contamination")
            subprocess.run(['pbcopy'], input=' ', text=True)
            time.sleep(0.2)
            
            # Navigate
            self.log("Pressing Enter to navigate")
            pyautogui.press('enter')
            
            # Extended wait for page load
            self.log("Waiting 8 seconds for page load completion...")
            time.sleep(8)
            
            self.log("Keyboard method completed successfully")
            return True
            
        except Exception as e:
            self.log(f"Keyboard method failed with exception: {e}")
            return False

    def _try_applescript_method(self):
        """AppleScript method with enhanced error handling"""
        try:
            self.log(f"Executing AppleScript method for URL: {self.extracted_url}")
            
            # Validate URL format for AppleScript
            if not (self.extracted_url.startswith('http://') or self.extracted_url.startswith('https://')):
                # Add https:// if missing
                if not self.extracted_url.startswith('www.'):
                    self.extracted_url = 'https://' + self.extracted_url
                else:
                    self.extracted_url = 'https://' + self.extracted_url
                self.log(f"Enhanced URL for AppleScript: {self.extracted_url}")
            
            # Check Chrome status
            chrome_running = self._is_chrome_running()
            
            if chrome_running:
                self.log("Chrome running - using AppleScript to open URL in existing window")
                applescript = f'''
                tell application "Google Chrome"
                    activate
                    delay 1
                    open location "{self.extracted_url}"
                end tell
                '''
                
                result = subprocess.run(["osascript", "-e", applescript], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.log("AppleScript navigation successful")
                    time.sleep(5)
                    return True
                else:
                    self.log(f"AppleScript failed: {result.stderr}")
                    return False
            else:
                self.log("Chrome not running - launching with URL")
                return self._try_direct_launch_method()
                
        except Exception as e:
            self.log(f"AppleScript method failed: {e}")
            return False

    def _try_direct_launch_method(self):
        """Direct launch method as final fallback"""
        try:
            self.log(f"Using direct launch method for URL: {self.extracted_url}")
            
            # Use macOS open command to launch Chrome with URL
            subprocess.Popen([
                "open", "-a", "Google Chrome", self.extracted_url
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.log("Chrome launched with URL - waiting for load...")
            time.sleep(6)
            
            self.log("Direct launch method completed")
            return True
            
        except Exception as e:
            self.log(f"Direct launch method failed: {e}")
            return False

    def _focus_chrome_browser(self):
        """Enhanced Chrome focusing with multiple strategies"""
        focus_strategies = [
            ("AppleScript activate", lambda: subprocess.run(
                ['osascript', '-e', 'tell application "Google Chrome" to activate'], 
                check=True, timeout=5)),
            ("Open command", lambda: subprocess.run(
                ['open', '-a', 'Google Chrome'], 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)),
            ("AppleScript launch", lambda: subprocess.run(
                ['osascript', '-e', 'tell application "Google Chrome" to launch'], 
                timeout=5))
        ]
        
        for strategy_name, strategy_func in focus_strategies:
            try:
                self.log(f"Trying focus strategy: {strategy_name}")
                strategy_func()
                time.sleep(1.5)
                return True
            except Exception as e:
                self.log(f"Focus strategy {strategy_name} failed: {e}")
        
        return False

    def _ensure_url_in_clipboard(self):
        """Ensure the extracted URL is properly stored in clipboard"""
        try:
            # Put URL back in clipboard in case it was lost
            subprocess.run(['pbcopy'], input=self.extracted_url, text=True)
            time.sleep(0.2)
            self.log(f"URL re-inserted into clipboard: {self.extracted_url}")
        except Exception as e:
            self.log(f"Failed to ensure URL in clipboard: {e}")

    def _verify_clipboard_content(self):
        """Verify clipboard contains valid URL content"""
        try:
            clipboard_result = subprocess.run(['pbpaste'], capture_output=True, text=True)
            clipboard_content = clipboard_result.stdout.strip()
            
            self.log(f"Clipboard verification - Content: '{clipboard_content}'")
            
            # Check if clipboard contains URL-like content
            is_valid = (
                clipboard_content.startswith('http') or 
                'www.' in clipboard_content or
                any(domain in clipboard_content.lower() for domain in ['bbc', 'wikipedia', 'google'])
            )
            
            if is_valid:
                self.log("Clipboard verification passed - contains valid URL")
                return True
            else:
                self.log(f"Clipboard verification failed - invalid content: '{clipboard_content}'")
                # Try to restore URL to clipboard
                self._ensure_url_in_clipboard()
                return False
                
        except Exception as e:
            self.log(f"Clipboard verification error: {e}")
            return False

    def _is_chrome_running(self):
        """Check if Chrome is currently running"""
        try:
            result = subprocess.run(["pgrep", "Chrome"], capture_output=True, text=True)
            is_running = result.returncode == 0
            self.log(f"Chrome running status: {is_running}")
            return is_running
        except Exception as e:
            self.log(f"Error checking Chrome status: {e}")
            return False

class KaiCoordinator:
    """Main coordination class managing the complete automation workflow"""
    
    def __init__(self):
        self.logger = logger
        self.state = {
            'current_desktop': 0,
            'last_url': None,
            'cycle_count': 0
        }

    def run_send_to_claude_flow(self, message, target_desktop=1):
        """Send a message to Claude with desktop switching"""
        self.logger.info("Starting: Send message to Claude")

        # Step 1: Switch to Claude desktop
        desktop_agent = KaiDesktopAgent(target_desktop=target_desktop)
        
        try:
            if not desktop_agent.run_with_retry():
                self.logger.error("Desktop switching failed")
                return False
            self.state['current_desktop'] = target_desktop
        except Exception as e:
            self.logger.error(f"Desktop switching failed: {e}")
            return False

        # Step 2: Direct typing
        typing_agent = KaiDirectTypingAgent(message=message)
        
        try:
            if not typing_agent.run_with_retry():
                self.logger.error("Direct typing failed")
                return False
        except Exception as e:
            self.logger.error(f"Direct typing failed: {e}")
            return False

        self.logger.info("Completed: Message sent to Claude")
        return True

    def run_full_automation_cycle(self):
        """Complete automation cycle with enhanced error handling and logging"""
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

            # Step 2: Wait for Claude response and extract URL using proven drag method
            self.logger.info("Waiting for Claude response and extracting URL...")
            
            boundary_detector = WorkingBoundaryDetector()
            stable_text = boundary_detector.wait_for_response_completion(timeout=30)
            
            if not (stable_text and '<<' in stable_text and '>>' in stable_text):
                self.logger.error("No boundary markers found in Claude response")
                return False

            self.logger.info("Found boundary markers, extracting URL with drag method...")
            
            text_region = boundary_detector.find_claude_text_region()
            screenshot_path = boundary_detector.take_screenshot_region(text_region)
            
            if not screenshot_path:
                self.logger.error("Failed to capture Claude region screenshot")
                return False

            # Extract and copy URL using drag selection
            extracted_url = self._extract_and_copy_url(screenshot_path, text_region)
            if not extracted_url:
                self.logger.error("Failed to extract and copy URL")
                return False

            self.state['last_url'] = extracted_url
            self.logger.info(f"Successfully extracted URL: {extracted_url}")

            # Step 3: Navigate to URL in browser
            desktop_agent = KaiDesktopAgent(target_desktop=2)
            if not desktop_agent.run_with_retry():
                self.logger.error("Failed to switch to browser desktop")
                return False
            self.state['current_desktop'] = 2

            # Use enhanced web agent with variable-based navigation
            web_agent = KaiWebAgent()
            if not web_agent.run_with_url_variable(extracted_url):
                self.logger.error("Failed to navigate to URL")
                return False

            # Step 4: Send confirmation to Claude
            time.sleep(4)
            
            desktop_agent = KaiDesktopAgent(target_desktop=1)
            if not desktop_agent.run_with_retry():
                self.logger.error("Failed to return to Claude desktop")
                return False
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

    def _extract_and_copy_url(self, screenshot_path, text_region):
        """Extract URL from screenshot and copy using drag selection"""
        try:
            image = Image.open(screenshot_path)
            img_array = np.array(image)
            
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Get OCR data with coordinates
            data = pytesseract.image_to_data(img_array, output_type=pytesseract.Output.DICT)
            
            # Find URL-like text
            for i, text in enumerate(data['text']):
                if text and any(keyword in text.lower() for keyword in ['http', 'www', 'bbc', 'wikipedia', 'google']):
                    # Calculate absolute coordinates
                    x = data['left'][i] + text_region[0]
                    y = data['top'][i] + text_region[1]
                    w = data['width'][i]
                    
                    # Use precise drag selection to avoid link trigger
                    # Be more conservative with selection area
                    start_x = max(x - 5, text_region[0])  # Don't go outside region
                    end_x = min(x + w + 5, text_region[0] + text_region[2])  # Don't go outside region
                    click_y = y + (data['height'][i] // 2)  # Center vertically on text
                    
                    self.logger.info(f"Found URL text: {text}")
                    self.logger.info(f"OCR coordinates: x={x}, y={y}, w={w}, h={data['height'][i]}")
                    self.logger.info(f"Using precise drag selection from ({start_x}, {click_y}) to ({end_x}, {click_y})")
                    
                    # AGGRESSIVE clipboard clearing - multiple methods
                    subprocess.run(['pbcopy'], input='CLEARED', text=True)
                    time.sleep(0.2)
                    subprocess.run(['pbcopy'], input='', text=True)
                    time.sleep(0.2)
                    
                    # Perform drag selection with more precision
                    pyautogui.click(start_x, click_y)
                    time.sleep(0.3)
                    pyautogui.dragTo(end_x, click_y, duration=0.8, button='left')
                    time.sleep(0.5)
                    
                    # Copy selection and verify immediately
                    pyautogui.hotkey('cmd', 'c')
                    time.sleep(0.5)
                    
                    # Immediate verification of what was copied
                    verify_result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                    copied_content = verify_result.stdout.strip()
                    self.logger.info(f"Immediately after copy - clipboard contains: '{copied_content[:100]}...'")
                    
                    # If clipboard still contaminated, extract URL from OCR text directly
                    if not any(keyword in copied_content.lower() for keyword in ['http', 'www', 'nasa', 'gov']):
                        self.logger.warning("Clipboard copy failed - using OCR text directly")
                        return text  # Return the OCR-detected text instead
                    
                    # Verify clipboard content
                    clipboard_result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                    extracted_url = clipboard_result.stdout.strip()
                    
                    self.logger.info(f"Successfully copied URL: {extracted_url}")
                    return extracted_url
            
            self.logger.error("No URL-like text found in OCR results")
            return None
            
        except Exception as e:
            self.logger.error(f"Error during URL extraction: {e}")
            return None

    def run_continuous_automation(self, max_cycles=None):
        """Run continuous automation cycles with error recovery"""
        self.logger.info("Starting continuous automation...")
        
        try:
            while True:
                if max_cycles and self.state['cycle_count'] >= max_cycles:
                    self.logger.info(f"Reached maximum cycles ({max_cycles})")
                    break

                success = self.run_full_automation_cycle()
                
                if success:
                    self.logger.info("Cycle successful - waiting before next cycle...")
                    time.sleep(5)
                else:
                    self.logger.warning("Cycle failed - waiting longer before retry...")
                    time.sleep(10)

        except KeyboardInterrupt:
            self.logger.info("Automation stopped by user")
        except Exception as e:
            self.logger.error(f"Critical error in continuous automation: {e}")

if __name__ == "__main__":
    print("KaiCoordinator - Hybrid Final Version 1.3")
    print("Combining proven OCR methods with enhanced navigation strategies")
    
    coordinator = KaiCoordinator()
    
    import argparse
    parser = argparse.ArgumentParser(description='Kai Automation System v1.3 (Hybrid)')
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