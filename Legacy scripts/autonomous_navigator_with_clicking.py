"""
autonomous_navigator_with_clicking.py
Enhanced navigator that can autonomously click links and interact with pages
"""

import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

# Import your existing components
from agents.kai_link_click_agent import KaiLinkClickAgent
from memory_interface import MemoryInterface
from log_writer import LogWriter
from strategy_scorer import StrategyScorer

class AutonomousNavigator:
    def __init__(self):
        self.intents_file = Path("intents.json")
        self.memory = MemoryInterface("memory.json")
        self.log = LogWriter("logs")
        self.scorer = StrategyScorer("strategy_stats.json")
        self.click_agent = KaiLinkClickAgent()
        
    def load_intents(self):
        """Load intent definitions from JSON"""
        try:
            with open(self.intents_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.intents_file} not found")
            return {}
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        return urlparse(url).netloc
    
    async def autonomous_research_session(self, start_url: str, research_plan: list):
        """
        Execute a research plan - navigate and click through multiple pages
        
        research_plan: list of dicts with 'intent' and optional 'target' keys
        Example: [
            {"intent": "click_first_article"},
            {"intent": "click_read_more"}, 
            {"intent": "click_next_page"}
        ]
        """
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            # Use existing Chrome profile for login preservation
            try:
                context = await browser.new_context(
                    user_data_dir="/Users/jonstiles/Library/Application Support/Google/Chrome/Default"
                )
                page = await context.new_page()
                print("Using existing Chrome profile")
            except Exception as e:
                print(f"Chrome profile access failed: {e}")
                page = await browser.new_page()
                print("Using clean browser session")
            
            # Navigate to starting URL
            await page.goto(start_url)
            await page.wait_for_load_state('networkidle')
            print(f"Started research session at: {start_url}")
            
            # Execute research plan
            for step_num, step in enumerate(research_plan, 1):
                intent_name = step['intent']
                target_text = step.get('target', '')
                
                print(f"\nStep {step_num}: {intent_name}")
                
                # Get intent definition
                intents = self.load_intents()
                if intent_name not in intents:
                    print(f"Intent '{intent_name}' not found in intents.json")
                    continue
                
                intent_data = intents[intent_name]
                
                # If target text provided, customize the intent
                if target_text:
                    intent_data = self._customize_intent_for_target(intent_data, target_text)
                
                domain = self.extract_domain(page.url)
                
                # Perform the click
                result = await self.click_agent.autonomous_click(page, intent_data, domain, intent_name)
                
                # Take screenshot after each step
                screenshot_path = f"research_step_{step_num}_{intent_name}.png"
                await page.screenshot(path=screenshot_path)
                
                result['step'] = step_num
                result['intent'] = intent_name
                result['url_before'] = page.url
                result['screenshot'] = screenshot_path
                
                results.append(result)
                
                if result['success']:
                    print(f"✅ {intent_name} succeeded using: {result['strategy']}")
                    # Wait for page to settle after click
                    await page.wait_for_load_state('networkidle', timeout=10000)
                else:
                    print(f"❌ {intent_name} failed: {result['error']}")
                    # Continue to next step even if this one failed
                
                # Brief pause between actions
                await asyncio.sleep(1)
            
            await browser.close()
        
        return results
    
    def _customize_intent_for_target(self, intent_data: dict, target_text: str):
        """Customize intent to look for specific target text"""
        customized = intent_data.copy()
        
        # Add target-specific fallbacks
        target_fallbacks = [
            {"method": "text-exact", "value": target_text},
            {"method": "text-contains", "value": target_text},
            {"method": "aria-label", "value": target_text}
        ]
        
        # Prepend target fallbacks to existing ones
        customized['fallbacks'] = target_fallbacks + intent_data.get('fallbacks', [])
        
        return customized
    
    async def single_click_operation(self, url: str, intent_name: str, target_text: str = ""):
        """Perform a single click operation on a page"""
        intents = self.load_intents()
        
        if intent_name not in intents:
            print(f"Error: Intent '{intent_name}' not found")
            return None
        
        intent_data = intents[intent_name]
        
        if target_text:
            intent_data = self._customize_intent_for_target(intent_data, target_text)
        
        domain = self.extract_domain(url)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            result = await self.click_agent.autonomous_click(page, intent_data, domain, intent_name)
            
            # Take screenshot
            await page.screenshot(path=f"{intent_name}_result.png")
            
            await browser.close()
        
        return result


async def main():
    """Command line interface and examples"""
    navigator = AutonomousNavigator()
    
    if len(sys.argv) < 2:
        print("Autonomous Navigator with Link Clicking")
        print("\nUsage modes:")
        print("1. Single click: python autonomous_navigator.py single <url> <intent> [target_text]")
        print("2. Research session: python autonomous_navigator.py research <start_url>")
        print("\nExamples:")
        print("python autonomous_navigator.py single https://news.bbc.co.uk click_first_article")
        print("python autonomous_navigator.py single https://example.com click_next_page")
        print("python autonomous_navigator.py research https://www.theguardian.com")
        return
    
    mode = sys.argv[1]
    
    if mode == "single":
        if len(sys.argv) < 4:
            print("Single mode requires: <url> <intent> [target_text]")
            return
        
        url = sys.argv[2]
        intent = sys.argv[3]
        target = sys.argv[4] if len(sys.argv) > 4 else ""
        
        print(f"Single click operation: {intent} on {url}")
        result = await navigator.single_click_operation(url, intent, target)
        print(f"Result: {json.dumps(result, indent=2)}")
    
    elif mode == "research":
        if len(sys.argv) < 3:
            print("Research mode requires: <start_url>")
            return
        
        start_url = sys.argv[2]
        
        # Example research plan - customize as needed
        research_plan = [
            {"intent": "click_first_article"},
            {"intent": "click_read_more"},
            {"intent": "click_next_page"}
        ]
        
        print(f"Starting autonomous research session from: {start_url}")
        print(f"Research plan: {[step['intent'] for step in research_plan]}")
        
        results = await navigator.autonomous_research_session(start_url, research_plan)
        
        print("\n=== Research Session Results ===")
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} Step {result['step']}: {result['intent']} - {result.get('strategy', result.get('error'))}")
    
    else:
        print(f"Unknown mode: {mode}")

if __name__ == "__main__":
    asyncio.run(main())