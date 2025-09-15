#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.kai_direct_typing_agent import KaiDirectTypingAgent
from agents.kai_desktop_agent import KaiDesktopAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_ocr_agent import KaiOCRAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
import logging
import time

# Basic logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger("KaiCoordinator")

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
        desktop_agent.attach_logger(self.logger)
        
        try:
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = target_desktop
        except Exception as e:
            self.logger.error(f"Desktop switching failed: {e}")
            return False

        # Step 2: Inject message into Claude's UI using direct typing
        typing_agent = KaiDirectTypingAgent(message=message)
        typing_agent.attach_logger(self.logger)
        
        try:
            typing_agent.run_with_retry()
        except Exception as e:
            self.logger.error(f"Direct typing failed: {e}")
            return False

        self.logger.info("Completed: Message sent to Claude")
        return True

    def run_full_automation_cycle(self):
        """Complete automation cycle: prompt -> wait for response -> extract URL -> navigate -> capture -> send back"""
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

            # Step 2: Wait for Claude response and extract boundaries
            self.logger.info("Waiting for Claude response...")
            
            ocr_agent = KaiOCRAgent()
            ocr_agent.attach_logger(self.logger)
            
            # Wait for stable response
            response_text = ocr_agent.run(wait_for_stability=True)
            
            if not response_text:
                self.logger.error("No response text captured")
                return False

            # Step 3: Extract boundaries and URLs
            boundary_agent = KaiBoundaryAgent()
            boundary_agent.attach_logger(self.logger)
            
            result = boundary_agent.run(response_text)
            
            if not result['success'] or not result['urls']:
                self.logger.warning("No URLs found in Claude's response")
                return False

            # Step 4: Navigate to URL
            target_url = url_result['urls'][0]
            self.state['last_url'] = target_url
            
            # Switch to browser desktop
            desktop_agent = KaiDesktopAgent(target_desktop=2)
            desktop_agent.attach_logger(self.logger)
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = 2

            # Open URL
            web_agent = KaiWebAgent(url=target_url)
            web_agent.attach_logger(self.logger)
            
            if not web_agent.run_with_retry():
                self.logger.error(f"Failed to navigate to {target_url}")
                return False

            # Step 5: Wait for page load and capture screenshot
            time.sleep(4)  # Wait for page to load
            
            screenshot_ocr = KaiOCRAgent(save_debug=True)
            screenshot_ocr.attach_logger(self.logger)
            screenshot_ocr.run(wait_for_stability=False)  # Just capture, don't wait

            # Step 6: Send screenshot back to Claude
            # Switch back to Claude
            desktop_agent = KaiDesktopAgent(target_desktop=1)
            desktop_agent.attach_logger(self.logger)
            desktop_agent.run_with_retry()
            self.state['current_desktop'] = 1

            # For now, just send a confirmation message
            # In the future, this would send the actual screenshot
            confirmation = f"<< Screenshot captured from {target_url} >>"
            
            if not self.run_send_to_claude_flow(confirmation, target_desktop=1):
                self.logger.error("Failed to send confirmation to Claude")
                return False

            self.logger.info(f"Cycle {self.state['cycle_count']} completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Automation cycle failed: {e}")
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
                    time.sleep(5)  # Wait between cycles
                else:
                    self.logger.warning("Cycle failed, waiting longer before retry...")
                    time.sleep(10)

        except KeyboardInterrupt:
            self.logger.info("Automation stopped by user")
        except Exception as e:
            self.logger.error(f"Critical error in automation: {e}")

if __name__ == "__main__":
    print("KaiCoordinator enhanced script is running...")
    coordinator = KaiCoordinator()
    
    import argparse
    parser = argparse.ArgumentParser(description='Kai Automation System')
    parser.add_argument('--test', action='store_true', help='Run single test message')
    parser.add_argument('--single', action='store_true', help='Run single automation cycle')
    parser.add_argument('--continuous', action='store_true', help='Run continuous automation')
    parser.add_argument('--cycles', type=int, help='Maximum number of cycles for continuous mode')
    
    args = parser.parse_args()
    
    if args.test:
        # Simple test
        success = coordinator.run_send_to_claude_flow("<< https://www.bbc.com/news >>", target_desktop=1)
        print("Test completed successfully" if success else "Test failed")
    elif args.single:
        # Single automation cycle
        success = coordinator.run_full_automation_cycle()
        print("Single cycle completed successfully" if success else "Single cycle failed")
    elif args.continuous:
        # Continuous automation
        coordinator.run_continuous_automation(max_cycles=args.cycles)
    else:
        # Default: run single cycle
        success = coordinator.run_full_automation_cycle()
        print("Single cycle completed successfully" if success else "Single cycle failed")