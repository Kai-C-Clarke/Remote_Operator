#!/usr/bin/env python3
"""
Quick test script to find the exact coordinates for Claude's input area
"""

import pyautogui
import time

def test_coordinates():
    """Test different coordinate combinations to find Claude's input"""
    
    screen_width, screen_height = pyautogui.size()
    print(f"Screen size: {screen_width}x{screen_height}")
    
    # Based on your Claude region (1540, 221, 868, 856)
    claude_left = 1540
    claude_top = 221
    claude_width = 868
    claude_height = 856
    claude_right = claude_left + claude_width  # 2408
    claude_bottom = claude_top + claude_height  # 1077
    
    print(f"Claude region: x={claude_left}-{claude_right}, y={claude_top}-{claude_bottom}")
    
    # Test different Y positions for input area
    test_coordinates = [
        (claude_left + claude_width//2, claude_bottom - 50),  # 50px from bottom of Claude region
        (claude_left + claude_width//2, claude_bottom + 30),  # 30px below Claude region
        (claude_left + claude_width//2, claude_bottom + 80),  # 80px below Claude region
        (claude_left + claude_width//2, screen_height - 100), # 100px from screen bottom
        (claude_left + claude_width//2, screen_height - 150), # 150px from screen bottom
    ]
    
    print("\nTesting coordinate options:")
    for i, (x, y) in enumerate(test_coordinates):
        print(f"{i+1}: ({x}, {y})")
    
    print("\nManual test:")
    print("1. Switch to desktop 1 with Claude visible")
    print("2. Run this script")
    print("3. Watch where the red circle appears")
    print("4. Press Ctrl+C to stop")
    
    try:
        for i, (x, y) in enumerate(test_coordinates):
            print(f"\nTesting position {i+1}: ({x}, {y})")
            print("Red circle will appear in 3 seconds...")
            time.sleep(3)
            
            # Draw a red circle at the test position
            pyautogui.moveTo(x, y)
            pyautogui.click(x, y)
            
            time.sleep(2)
            print("Did the click hit Claude's input area? (Check visually)")
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    print("Claude Input Coordinate Finder")
    print("=" * 40)
    test_coordinates()
