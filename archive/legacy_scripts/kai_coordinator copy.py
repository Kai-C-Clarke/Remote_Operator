#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.kai_desktop_agent import KaiDesktopAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
import logging

# Basic logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KaiCoordinator")

class KaiCoordinator:
    def __init__(self):
        self.logger = logger
        self.agents = []

    def run_send_to_claude_flow(self, message, target_desktop=1):
        self.logger.info("Starting: Send message to Claude")

        # Step 1: Switch to specified desktop (Claude's space)
        desktop_agent = KaiDesktopAgent(target_desktop=target_desktop)
        desktop_agent.attach_logger(self.logger)
        
        try:
            desktop_agent.run_with_retry()
        except Exception as e:
            self.logger.error(f"Desktop switching failed: {e}")
            return False

        # Step 2: Inject message into Claude's UI
        clipboard_agent = KaiClipboardAgent(message=message)
        clipboard_agent.attach_logger(self.logger)
        
        try:
            clipboard_agent.run_with_retry()
        except Exception as e:
            self.logger.error(f"Message injection failed: {e}")
            return False

        self.logger.info("Completed: Message sent to Claude")
        return True

if __name__ == "__main__":
    print("KaiCoordinator script is running...")
    coordinator = KaiCoordinator()
    
    # Test with explicit desktop target
    success = coordinator.run_send_to_claude_flow(
        message="<< https://www.bbc.com/news >>", 
        target_desktop=1
    )
    
    if success:
        print("Flow completed successfully")
    else:
        print("Flow failed - check logs")