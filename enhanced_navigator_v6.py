"""
enhanced_navigator_v6.py
Enhanced navigator with improved prompting and UI scroll management
"""

import time
import subprocess
import pyautogui
import json
from pathlib import Path
from playwright.async_api import async_playwright
import asyncio

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_desktop_agent import KaiDesktopAgent

class MemoryInterface:
    """Simple memory system for storing successful strategies"""
    def __init__(self, memory_file="memory.json"):
        self.memory_file = Path(memory_file)
        self.memory = self.load_memory()
    
    def load_memory(self):
        """Load memory from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Failed to save memory: {e}")
    
    def get_strategy(self, domain, intent):
        """Get successful strategy for domain/intent"""
        key = f"{domain}_{intent}"
        return self.memory.get(key)
    
    def store_strategy(self, domain, intent, strategy, success=True):
        """Store strategy result"""
        key = f"{domain}_{intent}"
        if key not in self.memory:
            self.memory[key] = {"strategies": [], "success_count": 0, "total_count": 0}
        
        self.memory[key]["strategies"].append({
            "strategy": strategy,
            "success": success,
            "timestamp": time.time()
        })
        
        if success:
            self.memory[key]["success_count"] += 1
        self.memory[key]["total_count"] += 1
        
        self.save_memory()

class UIManager:
    """Manages Claude UI scrolling and interaction"""
    
    def __init__(self):
        self.scroll_threshold = 4  # Scroll after 4 cycles
        
    def scroll_claude_up(self):
        """Scroll Claude's chat interface up to show recent responses"""
        try:
            # Click on Claude's chat area first
            claude_chat_x = 1685  # Center of Claude's chat area
            claude_chat_y = 600   # Middle height
            
            pyautogui.click(claude_chat_x, claude_chat_y)
            time.sleep(0.3)
            
            # Scroll up several times to show recent responses
            for _ in range(5):
                pyautogui.scroll(3)  # Scroll up
                time.sleep(0.2)
            
            print("📜 Scrolled Claude UI up to show recent responses")
            return True
            
        except Exception as e:
            print(f"UI scroll failed: {e}")
            return False

class ArticleClicker:
    """DOM-based article clicking with memory"""
    
    def __init__(self):
        self.memory = MemoryInterface()
        self.intents = self.load_intents()
    
    def load_intents(self):
        """Load or create intent definitions"""
        intents_file = Path("intents.json")
        
        if intents_file.exists():
            with open(intents_file, 'r') as f:
                return json.load(f)
        
        # Default intents for common sites
        default_intents = {
            "click_first_article": {
                "primary_selector": "article h2 a, h2 a, .story-link a",
                "timeout": 3000,
                "fallbacks": [
                    {"method": "css", "value": "[data-testid='card-headline'] a"},
                    {"method": "css", "value": ".media__link"},
                    {"method": "css", "value": ".post-title a"},
                    {"method": "css", "value": "h3 a"},
                    {"method": "xpath", "value": "//a[contains(@class, 'storylink')]"}
                ]
            }
        }
        
        # Save default intents
        with open(intents_file, 'w') as f:
            json.dump(default_intents, f, indent=2)
        
        return default_intents
    
    async def click_article(self, page, domain, intent="click_first_article"):
        """Click article using memory-enhanced strategy"""
        print(f"Attempting to click article on {domain} with intent: {intent}")
        
        if intent not in self.intents:
            print(f"Intent {intent} not found")
            return {"success": False, "error": "Intent not found"}
        
        intent_config = self.intents[intent]
        
        # Check memory for successful strategy
        remembered_strategy = self.memory.get_strategy(domain, intent)
        strategies_to_try = []
        
        if remembered_strategy:
            print(f"Found remembered strategy for {domain}/{intent}")
            # Add remembered successful strategies first
            for strategy in remembered_strategy["strategies"]:
                if strategy["success"]:
                    strategies_to_try.append({
                        "type": "memory",
                        "selector": strategy["strategy"],
                        "method": "css"
                    })
        
        # Add primary selector
        strategies_to_try.append({
            "type": "primary",
            "selector": intent_config["primary_selector"],
            "method": "css"
        })
        
        # Add fallback strategies
        for fallback in intent_config.get("fallbacks", []):
            strategies_to_try.append({
                "type": "fallback",
                "selector": fallback["value"],
                "method": fallback["method"]
            })
        
        # Try each strategy
        for strategy in strategies_to_try:
            try:
                success = await self.try_strategy(page, strategy)
                
                if success:
                    print(f"✅ Success with {strategy['type']}: {strategy['selector']}")
                    
                    # Store successful strategy in memory
                    self.memory.store_strategy(domain, intent, strategy['selector'], True)
                    
                    return {
                        "success": True,
                        "strategy": f"{strategy['type']}: {strategy['selector']}",
                        "method": strategy['method']
                    }
                else:
                    print(f"❌ Failed: {strategy['type']} - {strategy['selector']}")
                    # Store failed strategy
                    self.memory.store_strategy(domain, intent, strategy['selector'], False)
                    
            except Exception as e:
                print(f"Error with strategy {strategy['selector']}: {e}")
                continue
        
        return {"success": False, "error": "All strategies failed"}
    
    async def try_strategy(self, page, strategy):
        """Try a specific clicking strategy"""
        try:
            selector = strategy['selector']
            method = strategy['method']
            
            if method == "css":
                element = await page.query_selector(selector)
            elif method == "xpath":
                element = await page.query_selector(f"xpath={selector}")
            else:
                return False
            
            if element and await element.is_visible():
                await element.click()
                await page.wait_for_load_state('networkidle', timeout=5000)
                return True
                
        except Exception as e:
            print(f"Strategy failed: {e}")
            return False
        
        return False

class EnhancedNavigator:
    """Enhanced navigator with article clicking and UI management"""
    
    def __init__(self):
        self.article_clicker = ArticleClicker()
        self.ui_manager = UIManager()
        self.cycle_count = 0
    
    def ask_for_url(self):
        """Initial prompt to Claude"""
        starter_message = "What website should we visit?"
        clipboard_agent = KaiClipboardAgent(message=starter_message)
        clipboard_agent.run_fast()
    
    def ask_for_action(self, has_clicked_article=False):
        """Improved action prompt after screenshot"""
        if has_clicked_article:
            action_message = "I found and clicked on an article from this website. Would you like me to open another link within this webpage, or navigate to a different website?"
        else:
            action_message = "Here's the current webpage. Would you like me to open a link within this webpage, or navigate to another website?"
        
        clipboard_agent = KaiClipboardAgent(message=action_message)
        clipboard_agent.run_fast()
    
    def capture_claude_url(self):
        """Use OCR with optimized stability detection"""
        claude_agent = KaiClaudeRegionAgent()
        stable_text = claude_agent.wait_for_response_completion_fast()
        
        if not stable_text:
            print("No text captured from Claude region.")
            return None
        
        print(f"Captured text ({len(stable_text)} chars)")
        
        boundary_agent = KaiBoundaryAgent()
        url_result = boundary_agent.run(stable_text)
        
        if url_result["success"] and url_result["urls"]:
            url = url_result["urls"][0]
            method = url_result.get("method", "unknown")
            print(f"Website extracted via {method}: {url}")
            return url
        else:
            print("No website found in Claude's reply.")
            return None
    
    def manage_ui_scroll(self):
        """Handle UI scrolling after threshold cycles"""
        if self.cycle_count > 0 and self.cycle_count % self.ui_manager.scroll_threshold == 0:
            print(f"🔄 Cycle {self.cycle_count}: Managing UI scroll...")
            self.ui_manager.scroll_claude_up()
            time.sleep(1.0)  # Brief pause after scrolling
    
    async def enhanced_browse_and_capture(self, url):
        """Enhanced browsing with article clicking"""
        # Switch to browser desktop
        print("Switching to browser desktop...")
        KaiDesktopAgent(direction="right", presses=1).run_fast()
        time.sleep(0.7)
        
        # Open URL
        web_agent = KaiWebAgent(url=url)
        web_agent.run_fast()
        
        # Wait for page load
        time.sleep(2.0)
        
        # Take initial screenshot
        print("Taking initial screenshot...")
        try:
            subprocess.run(["screencapture", "-c"], check=True, timeout=8)
            print("Initial screenshot captured")
        except Exception as e:
            print(f"Initial screenshot failed: {e}")
            return False, False
        
        # NOW ADD ARTICLE CLICKING
        domain = url.split('/')[2] if '/' in url else url
        article_clicked = False
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url)
                await page.wait_for_load_state('networkidle')
                
                # Try to click an article
                click_result = await self.article_clicker.click_article(page, domain)
                
                if click_result["success"]:
                    print(f"✅ Successfully clicked article: {click_result['strategy']}")
                    article_clicked = True
                    
                    # Wait for article to load
                    time.sleep(3)
                    
                    # Take article screenshot
                    print("Taking article screenshot...")
                    subprocess.run(["screencapture", "-c"], check=True, timeout=8)
                    print("Article screenshot captured")
                else:
                    print(f"❌ Article clicking failed: {click_result.get('error', 'Unknown error')}")
                    # Continue with homepage screenshot
                
            except Exception as e:
                print(f"Browser automation error: {e}")
            finally:
                await browser.close()
        
        # Return to Claude
        print("Returning to Claude...")
        KaiDesktopAgent(direction="left", presses=1).run_fast()
        time.sleep(1.2)
        
        # Send screenshot to Claude
        print("Sending screenshot to Claude...")
        try:
            claude_input_x = 1845
            claude_input_y = 1280
            
            pyautogui.click(claude_input_x, claude_input_y)
            time.sleep(0.3)
            
            pyautogui.hotkey("command", "a")
            time.sleep(0.2)
            pyautogui.hotkey("command", "v")
            time.sleep(1.2)
            pyautogui.press("enter")
            time.sleep(0.5)
            
            print("Screenshot sent to Claude.")
            
            # IMPROVED ACTION PROMPT
            self.ask_for_action(article_clicked)
            
        except Exception as e:
            print(f"Error sending screenshot: {e}")
            return False, False
        
        return True, article_clicked
    
    async def run_cycle(self):
        """Run one complete enhanced navigation cycle"""
        cycle_start = time.time()
        self.cycle_count += 1
        
        print(f"\n=== Cycle {self.cycle_count} ===")
        
        # Manage UI scrolling
        self.manage_ui_scroll()
        
        # First cycle: ask for URL, subsequent: capture response
        if self.cycle_count == 1:
            self.ask_for_url()
            time.sleep(0.5)
        
        # Capture Claude's response
        url = self.capture_claude_url()
        if not url:
            print("No URL captured. Retrying...")
            return False
        
        # Enhanced browsing with article clicking
        success, article_clicked = await self.enhanced_browse_and_capture(url)
        
        cycle_time = time.time() - cycle_start
        status = "✅" if success else "❌"
        article_status = "📰" if article_clicked else "🏠"
        
        print(f"{status} Cycle {self.cycle_count} completed in {cycle_time:.1f}s {article_status}")
        
        return success

async def main():
    """Main loop with enhanced navigation and UI management"""
    print("=== Enhanced Navigator v6 with UI Management ===")
    print("Features:")
    print("- Article clicking with memory learning")
    print("- Improved action prompts")
    print("- UI scroll management every 4 cycles")
    print("- DOM-based content exploration")
    print()
    
    navigator = EnhancedNavigator()
    
    # Initial desktop positioning
    KaiDesktopAgent(direction="right", presses=1).run_fast()
    
    while True:
        success = await navigator.run_cycle()
        
        if not success:
            print("Cycle failed, continuing...")
        
        print("Ready for next action...")
        time.sleep(1.5)

if __name__ == "__main__":
    asyncio.run(main())