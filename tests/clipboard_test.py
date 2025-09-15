#!/usr/bin/env python3
"""
Simple test script to debug clipboard copy/paste issues
"""

import pyperclip
import time

def test_clipboard():
    """Test clipboard operations with the exact message"""
    
    # The exact message from the coordinator
    test_message = "Ready for your next webpage operation command! Use << URL >> format."
    
    print(f"Testing clipboard with message ({len(test_message)} chars):")
    print(f"Message: {test_message}")
    print()
    
    # Test 1: Basic copy/paste
    print("Test 1: Basic pyperclip copy/paste")
    pyperclip.copy(test_message)
    time.sleep(1)
    
    result = pyperclip.paste()
    print(f"Result ({len(result)} chars): {result}")
    print(f"Match: {result == test_message}")
    print()
    
    # Test 2: Check for truncation
    if result != test_message:
        print("ISSUE FOUND: Message was truncated!")
        print(f"Expected: {test_message}")
        print(f"Got:      {result}")
        print(f"Missing:  {test_message[len(result):]}")
    else:
        print("SUCCESS: Clipboard copy/paste working correctly")

if __name__ == "__main__":
    test_clipboard()
