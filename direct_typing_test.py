#!/usr/bin/env python3
"""
Simple test script to verify direct typing works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.kai_desktop_agent import KaiDesktopAgent
from agents.kai_direct_typing_agent import KaiDirectTypingAgent
import logging

# Basic logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger("DirectTypingTest")

def test_direct_typing():
    """Test direct typing functionality"""
    print("Direct Typing Test")
    print("=" * 30)
    
    # Step 1: Switch to desktop 1
    print("Step 1: Switching to desktop 1...")
    desktop_agent = KaiDesktopAgent(target_desktop=1)
    desktop_agent.attach_logger(logger)
    
    try:
        desktop_agent.run_with_retry()
        print("✓ Desktop switch successful")
    except Exception as e:
        print(f"✗ Desktop switch failed: {e}")
        return False

    # Step 2: Test direct typing
    print("\nStep 2: Testing direct typing...")
    test_message = "Ready for your next webpage operation command! Use << URL >> format."
    
    typing_agent = KaiDirectTypingAgent(message=test_message, typing_interval=0.01)
    typing_agent.attach_logger(logger)
    
    try:
        typing_agent.run_with_retry()
        print("✓ Direct typing successful")
        print(f"✓ Message sent: {test_message}")
        return True
    except Exception as e:
        print(f"✗ Direct typing failed: {e}")
        return False

if __name__ == "__main__":
    print("This will:")
    print("1. Switch to desktop 1")
    print("2. Click Claude's input area at (1845, 1280)")
    print("3. Type the test message directly")
    print("4. Send with Enter")
    print()
    
    input("Make sure Claude is visible on desktop 1, then press Enter to continue...")
    
    success = test_direct_typing()
    
    if success:
        print("\n🎉 Direct typing test completed successfully!")
    else:
        print("\n❌ Direct typing test failed!")
