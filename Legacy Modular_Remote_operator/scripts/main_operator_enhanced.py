#!/usr/bin/env python3
"""
AI Remote Operator - Complete Workflow
Enhanced main operator that orchestrates all modules into a working system.
"""

import time
import sys
import traceback
from pathlib import Path

from logger import Logger
from desktop_manager import DesktopManager
from screen_manager import ScreenManager
from claude_ui import ClaudeUI
from clipboard_manager import ClipboardManager
from boundary_detector import BoundaryDetector
from web_navigator import WebNavigator
import config

class OperationState:
    """Track the current state of the operation"""
    def __init__(self):
        self.cycle_count = 0
        self.last_url = None
        self.last_boundary_content = []
        self.health_status = {}
        self.should_continue = True
        self.manual_intervention_needed = False

class AIRemoteOperator:
    """Main orchestrator that coordinates all modules"""
    
    def __init__(self):
        self.logger = Logger()
        self.state = OperationState()
        
        # Initialize all modules
        self.desktop = DesktopManager(self.logger)
        self.screen = ScreenManager(self.logger)
        self.claude = ClaudeUI(self.logger)
        self.clipboard = ClipboardManager(self.logger)
        self.boundaries = BoundaryDetector(self.logger)
        self.webnav = WebNavigator(self.logger)
        
        self.logger.info("AI Remote Operator initialized")

    def run_continuous_cycle(self, max_cycles=None):
        """Run the operation in continuous cycles"""
        self.logger.info("Starting continuous operation cycle")
        
        try:
            while self.state.should_continue:
                if max_cycles and self.state.cycle_count >= max_cycles:
                    self.logger.info(f"Reached maximum cycles ({max_cycles})")
                    break
                
                self.state.cycle_count += 1
                self.logger.info(f"=== Starting Cycle {self.state.cycle_count} ===")
                
                success = self.run_single_cycle()
                
                if not success and self.state.manual_intervention_needed:
                    self.handle_manual_intervention()
                
                # Wait between cycles
                if self.state.should_continue:
                    self.logger.info(f"Cycle {self.state.cycle_count} complete. Waiting {config.CYCLE_DELAY}s...")
                    time.sleep(config.CYCLE_DELAY)
                    
        except KeyboardInterrupt:
            self.logger.info("Operation stopped by user")
        except Exception as e:
            self.logger.error(f"Critical error in main loop: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            self.cleanup()

    def run_single_cycle(self):
        """Execute one complete operation cycle"""
        health = {}
        
        try:
            # Step 1: Prepare Claude desktop and send prompt
            health['claude_setup'] = self.setup_claude_interaction()
            
            # Step 2: Wait for Claude response and capture it
            health['claude_response'] = self.capture_claude_response()
            
            # Step 3: Process boundaries from Claude's response
            health['boundary_processing'] = self.process_boundaries()
            
            # Step 4: Execute web navigation if URL found
            health['web_navigation'] = self.execute_web_navigation()
            
            # Step 5: Capture result and send back to Claude
            health['result_capture'] = self.capture_and_send_result()
            
            # Step 6: Health check and reporting
            self.state.health_status = health
            self.report_cycle_health(health)
            
            # Determine if cycle was successful
            critical_steps = ['claude_setup', 'claude_response', 'boundary_processing']
            success = all(health.get(step, False) for step in critical_steps)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in cycle {self.state.cycle_count}: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def setup_claude_interaction(self):
        """Step 1: Switch to Claude and send prompt"""
        self.logger.info("Step 1: Setting up Claude interaction")
        
        # Switch to Claude desktop
        if not self.desktop.switch_desktop(config.DESKTOP_CLAUDE):
            self.logger.notify("Desktop Switch Failed", "Cannot switch to Claude desktop")
            return False
        
        # Send prompt to Claude
        try:
            prompt = config.PROMPT_TEXT
            if self.state.last_url:
                prompt += f" Last processed: {self.state.last_url}"
            
            self.claude.focus_and_type(prompt)
            self.logger.info("Prompt sent to Claude successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send prompt to Claude: {e}")
            self.logger.notify("Claude UI Error", "Cannot interact with Claude interface")
            return False

    def capture_claude_response(self):
        """Step 2: Wait for and capture Claude's response with stability check"""
        self.logger.info("Step 2: Waiting for stable Claude response")
        
        try:
            # Use the new stability-based waiting method
            response_text = self.screen.wait_for_claude_response()
            self.logger.info(f"Captured stable Claude response: {len(response_text)} characters")
            
            if len(response_text) < 50:
                self.logger.warning("Claude response appears too short, possible OCR issue")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to capture Claude response: {e}")
            return False

    def process_boundaries(self):
        """Step 3: Extract and process boundary markers from Claude's response"""
        self.logger.info("Step 3: Processing boundary markers")
        
        try:
            # Get latest screenshot for boundary detection
            img = self.screen.take_full_screenshot()
            text = self.screen.extract_text(img)
            
            # Extract boundaries
            boundary_contents = self.boundaries.extract_boundaries(text)
            self.state.last_boundary_content = boundary_contents
            
            if boundary_contents:
                self.logger.info(f"Found {len(boundary_contents)} boundaries: {boundary_contents}")
                return True
            else:
                self.logger.info("No boundaries found in Claude's response")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to process boundaries: {e}")
            return False

    def execute_web_navigation(self):
        """Step 4: Navigate to URL if found in boundaries"""
        self.logger.info("Step 4: Executing web navigation")
        
        if not self.state.last_boundary_content:
            self.logger.info("No boundaries to process, skipping web navigation")
            return True  # Not an error, just nothing to do
        
        try:
            # Get the first URL-like boundary
            url = self.state.last_boundary_content[0]
            
            # Basic URL validation
            if not (url.startswith('http://') or url.startswith('https://')):
                if not url.startswith('www.'):
                    url = 'https://' + url
                else:
                    url = 'https://' + url
            
            self.state.last_url = url
            self.logger.info(f"Navigating to: {url}")
            
            # Switch to browser desktop
            if not self.desktop.switch_desktop(config.DESKTOP_BROWSER):
                self.logger.notify("Desktop Switch Failed", "Cannot switch to browser desktop")
                return False
            
            # Open URL
            if not self.webnav.open_url(url):
                self.logger.error(f"Failed to open URL: {url}")
                return False
            
            # Wait for page to load
            time.sleep(config.PAGE_LOAD_WAIT)
            
            self.logger.info("Web navigation completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed web navigation: {e}")
            return False

    def capture_and_send_result(self):
        """Step 5: Capture result and send back to Claude"""
        self.logger.info("Step 5: Capturing and sending result")
        
        try:
            # Take screenshot of browser result
            result_img = self.screen.take_full_screenshot()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            result_path = Path(config.SCREENSHOT_PATH) / f"result_cycle_{self.state.cycle_count}_{timestamp}.png"
            result_img.save(result_path)
            
            # Copy to clipboard with retry logic
            clipboard_success = False
            for attempt in range(config.RETRY_ATTEMPTS):
                if self.clipboard.copy_image_to_clipboard(str(result_path)):
                    if self.clipboard.verify_clipboard_has_image():
                        clipboard_success = True
                        break
                    else:
                        self.logger.warning(f"Clipboard verify failed, attempt {attempt + 1}")
                else:
                    self.logger.warning(f"Clipboard copy failed, attempt {attempt + 1}")
                time.sleep(0.5)
            
            if not clipboard_success:
                self.logger.notify("Clipboard Failed", "Manual image upload required")
                self.state.manual_intervention_needed = True
                return False
            
            # Switch back to Claude
            if not self.desktop.switch_desktop(config.DESKTOP_CLAUDE):
                return False
            
            # Paste the image (Cmd+V)
            time.sleep(0.5)
            import pyautogui
            pyautogui.hotkey('cmd', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            
            self.logger.info("Result sent to Claude successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to capture and send result: {e}")
            return False

    def report_cycle_health(self, health):
        """Report the health status of the current cycle"""
        self.logger.info("=== CYCLE HEALTH REPORT ===")
        total_steps = len(health)
        successful_steps = sum(1 for v in health.values() if v)
        
        for step, success in health.items():
            status = "✓ SUCCESS" if success else "✗ FAILURE"
            self.logger.info(f"{step}: {status}")
        
        success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
        self.logger.info(f"Overall Success Rate: {success_rate:.1f}% ({successful_steps}/{total_steps})")
        
        # Critical failure detection
        if success_rate < 60:
            self.logger.notify("Low Success Rate", f"Cycle success rate: {success_rate:.1f}%")

    def handle_manual_intervention(self):
        """Handle cases requiring manual intervention"""
        self.logger.info("Manual intervention required")
        self.logger.notify("Manual Intervention", "Check logs and assist as needed")
        
        # Wait for user to fix issues
        response = input("\nManual intervention needed. Continue? (y/n/q): ").lower()
        if response == 'q':
            self.state.should_continue = False
        elif response == 'n':
            time.sleep(30)  # Wait before retrying
        
        self.state.manual_intervention_needed = False

    def cleanup(self):
        """Clean up resources and final reporting"""
        self.logger.info("=== OPERATION SUMMARY ===")
        self.logger.info(f"Total cycles completed: {self.state.cycle_count}")
        self.logger.info(f"Last processed URL: {self.state.last_url}")
        
        if self.state.health_status:
            overall_health = sum(1 for v in self.state.health_status.values() if v)
            total_checks = len(self.state.health_status)
            self.logger.info(f"Final health status: {overall_health}/{total_checks} checks passed")
        
        self.logger.info("AI Remote Operator shutdown complete")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Remote Operator')
    parser.add_argument('--cycles', type=int, help='Maximum number of cycles to run')
    parser.add_argument('--single', action='store_true', help='Run single cycle only')
    args = parser.parse_args()
    
    operator = AIRemoteOperator()
    
    try:
        if args.single:
            operator.logger.info("Running single cycle mode")
            success = operator.run_single_cycle()
            operator.logger.info(f"Single cycle completed: {'SUCCESS' if success else 'FAILURE'}")
        else:
            operator.run_continuous_cycle(max_cycles=args.cycles)
    except Exception as e:
        operator.logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()