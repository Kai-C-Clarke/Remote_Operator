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

    def run_send_to_claude_flow(self, message):
        self.logger.info("Starting: Send message to Claude")

        # Step 1: Switch to Desktop 1 (Claude's space)
        desktop_agent = KaiDesktopAgent()
        desktop_agent.attach_logger(self.logger)
        desktop_agent.run_with_retry()

        # Step 2: Inject message into Claude's UI
        clipboard_agent = KaiClipboardAgent(message=message)
        clipboard_agent.attach_logger(self.logger)
        clipboard_agent.run_with_retry()

        self.logger.info("Completed: Message sent to Claude")

if __name__ == "__main__":
    print("KaiCoordinator script is running...")
    coordinator = KaiCoordinator()
    coordinator.run_send_to_claude_flow("Hello Claude, this is a symbolic test message from Kai.")
