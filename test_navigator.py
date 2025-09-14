#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the current directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from autonomous_navigator_with_clicking import AutonomousNavigator

async def test_navigation():
    """Test the autonomous web navigator with enhanced screenshot functionality"""
    
    navigator = AutonomousNavigator()
    
    try:
        print("🚀 Starting autonomous web navigation test...")
        print("📸 Enhanced screenshot functionality enabled")
        print("🍪 Cookie banner handling improved")
        print("-" * 50)
        
        # Test with a news website that likely has cookie banners
        test_url = "https://www.bbc.com/news"
        
        print(f"🌐 Navigating to: {test_url}")
        
        # Create a simple research plan to test the navigation
        research_plan = [
            {"intent": "click_first_article", "target": ""},  # Click on the first article
            {"intent": "read_content", "target": ""},         # Read the content
            {"intent": "navigate_back", "target": ""}         # Navigate back
        ]
        
        print("📋 Research plan:", research_plan)
        
        # Use the autonomous_research_session method
        await navigator.autonomous_research_session(
            start_url=test_url,
            research_plan=research_plan
        )
        
        print("\n✅ Test completed successfully!")
        print("📂 Check the debug_screenshots/ directory for debugging images")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("🔍 Check debug_screenshots/ for troubleshooting images")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_navigation())