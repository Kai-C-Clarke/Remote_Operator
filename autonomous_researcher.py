"""
autonomous_researcher.py
Hybrid: Robust infrastructure + autonomous browsing commands
Combines integrated_navigator reliability with daylong_researcher flexibility
"""

import time
import subprocess
import pyautogui
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright
import asyncio
from datetime import datetime

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from agents.kai_desktop_agent import KaiDesktopAgent

class ResearchLogger:
    """Enhanced logging system for research sessions"""
    def __init__(self, log_dir="research_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_start = datetime.now()
        self.session_log = []
        
    def log_action(self, action_type, url, details, success=True):
        """Log research action"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            "url": url,
            "details": details,
            "success": success
        }
        self.session_log.append(entry)
        
        # Real-time logging
        status = "✅" if success else "❌"
        print(f"[LOG] {status} {action_type}: {details}")
        
    def save_session(self):
        """Save complete session log"""
        session_file = self.log_dir / f"session_{self.session_start.strftime('%Y%m%d_%H%M%S')}.json"
        
        session_data = {
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "total_actions": len(self.session_log),
            "successful_actions": sum(1 for entry in self.session_log if entry["success"]),
            "actions": self.session_log
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"📋 Session saved: {session_file}")

class MemoryInterface:
    """Memory system from integrated_navigator"""
    def __init__(self, memory_file="memory.json"):
        self.memory_file = Path(memory_file)
        self.memory = self.load_memory()
    
    def load_memory(self):
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Memory save failed: {e}")
    
    def get_strategy(self, domain, intent):
        key = f"{domain}_{intent}"
        return self.memory.get(key)
    
    def store_strategy(self, domain, intent, strategy, success=True):
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

class CommandParser:
    """Flexible command parsing for Claude's natural language"""
    
    def __init__(self):
        # Command patterns
        self.patterns = {
            "article_click": [
                r"(?:article|click|find).*?[:\-\s]+(.+)",
                r"(?:read|open)\s+[\"']([^\"']+)[\"']",
                r"(?:show me|find)\s+(.+?article|.+?story)",
                r"click\s+(?:on\s+)?[\"']?([^\"'\n]+)[\"']?"
            ],
            "new_site": [
                r"(?:visit|goto|open|navigate to)\s+(.+)",
                r"(?:new site|next site)[:\s]+(.+)",
                r"<<([^>]+)>>"  # Boundary markers
            ],
            "navigation": [
                r"\b(home|back|return)\b",
                r"go\s+(home|back)"
            ]
        }
    
    def parse_command(self, text):
        """Parse Claude's text into actionable commands"""
        text = text.strip()
        
        # Try article click patterns
        for pattern in self.patterns["article_click"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                if len(query) > 3:  # Avoid too short queries
                    return {
                        "type": "article_click",
                        "query": query,
                        "confidence": 0.8
                    }
        
        # Try new site patterns
        for pattern in self.patterns["new_site"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                site = match.group(1).strip()
                return {
                    "type": "new_site",
                    "url": self.clean_url(site),
                    "confidence": 0.9
                }
        
        # Try navigation patterns
        for pattern in self.patterns["navigation"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                action = match.group(1).lower()
                return {
                    "type": "navigation",
                    "action": action,
                    "confidence": 0.7
                }
        
        # Fallback: try URL extraction from boundary agent
        from agents.kai_boundary_agent import KaiBoundaryAgent
        boundary_agent = KaiBoundaryAgent()
        url_result = boundary_agent.run(text)
        
        if url_result["success"] and url_result["urls"]:
            return {
                "type": "new_site",
                "url": url_result["urls"][0],
                "confidence": 0.6
            }
        
        return None
    
    def clean_url(self, url):
        """Clean and validate URL"""
        url = url.strip()
        url = re.sub(r'^[<>"\'\s]+|[<>"\'\s]+$', '', url)
        
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            elif '.' in url:
                url = 'https://' + url
        
        return url

class ArticleClicker:
    """Robust article clicking with multiple strategies"""
    
    def __init__(self, memory):
        self.memory = memory
        self.intents = self.load_intents()
    
    def load_intents(self):
        """Load or create intent definitions"""
        intents_file = Path("intents.json")
        
        if intents_file.exists():
            with open(intents_file, 'r') as f:
                return json.load(f)
        
        # Comprehensive default intents
        default_intents = {
            "click_first_article": {
                "primary_selector": "article h2 a, h2 a, .story-link a, .storylink",
                "fallbacks": [
                    {"method": "css", "value": "[data-testid='card-headline'] a"},
                    {"method": "css", "value": ".media__link"},
                    {"method": "css", "value": ".post-title a"},
                    {"method": "css", "value": "h3 a"},
                    {"method": "css", "value": ".entry-title a"},
                    {"method": "xpath", "value": "//a[contains(@class, 'storylink')]"}
                ]
            },
            "search_article": {
                "primary_selector": "a[href*='article'], a[href*='story'], a[href*='post']",
                "fallbacks": [
                    {"method": "text_search", "value": "partial_match"},
                    {"method": "css", "value": "article a"},
                    {"method": "css", "value": ".content a"}
                ]
            }
        }
        
        with open(intents_file, 'w') as f:
            json.dump(default_intents, f, indent=2)
        
        return default_intents
    
    async def find_and_click_article(self, page, domain, query=None, intent="click_first_article"):
        """Enhanced article finding with text search and CSS selectors"""
        
        if query:
            # Text-based search for specific articles
            return await self.search_by_text(page, domain, query)
        else:
            # Generic article clicking
            return await self.click_by_selectors(page, domain, intent)
    
    async def search_by_text(self, page, domain, query):
        """Search for articles by text content"""
        try:
            # Get all links
            links = await page.query_selector_all("a")
            
            best_matches = []
            
            for link in links:
                try:
                    if not await link.is_visible():
                        continue
                    
                    text = await link.inner_text()
                    href = await link.get_attribute("href")
                    
                    if not text or not href:
                        continue
                    
                    # Calculate match score
                    text_lower = text.lower()
                    query_lower = query.lower()
                    
                    if query_lower in text_lower:
                        score = len(query_lower) / len(text_lower)
                        best_matches.append({
                            "element": link,
                            "text": text,
                            "href": href,
                            "score": score
                        })
                    
                except Exception:
                    continue
            
            if best_matches:
                # Sort by relevance score
                best_matches.sort(key=lambda x: x["score"], reverse=True)
                best_match = best_matches[0]
                
                await best_match["element"].click()
                await page.wait_for_load_state('networkidle', timeout=8000)
                
                # Store successful strategy
                self.memory.store_strategy(domain, "search_article", f"text:{query}", True)
                
                return {
                    "success": True,
                    "method": "text_search",
                    "article_title": best_match["text"],
                    "url": best_match["href"]
                }
            
            return {"success": False, "error": "No matching articles found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def click_by_selectors(self, page, domain, intent):
        """Click using CSS selectors from intents"""
        if intent not in self.intents:
            return {"success": False, "error": f"Intent {intent} not found"}
        
        intent_config = self.intents[intent]
        
        # Try remembered strategies first
        remembered = self.memory.get_strategy(domain, intent)
        strategies = []
        
        if remembered:
            for strategy in remembered["strategies"]:
                if strategy["success"]:
                    strategies.append({
                        "type": "memory",
                        "selector": strategy["strategy"]
                    })
        
        # Add primary and fallback strategies
        strategies.append({
            "type": "primary",
            "selector": intent_config["primary_selector"]
        })
        
        for fallback in intent_config.get("fallbacks", []):
            strategies.append({
                "type": "fallback",
                "selector": fallback["value"]
            })
        
        # Try each strategy
        for strategy in strategies:
            try:
                element = await page.query_selector(strategy["selector"])
                
                if element and await element.is_visible():
                    text = await element.inner_text()
                    href = await element.get_attribute("href")
                    
                    await element.click()
                    await page.wait_for_load_state('networkidle', timeout=8000)
                    
                    # Store successful strategy
                    self.memory.store_strategy(domain, intent, strategy["selector"], True)
                    
                    return {
                        "success": True,
                        "method": f"{strategy['type']}_selector",
                        "article_title": text[:100],
                        "selector": strategy["selector"]
                    }
                    
            except Exception as e:
                # Store failed strategy
                self.memory.store_strategy(domain, intent, strategy["selector"], False)
                continue
        
        return {"success": False, "error": "All selector strategies failed"}

class AutonomousResearcher:
    """Main researcher class combining all components"""
    
    def __init__(self):
        self.memory = MemoryInterface()
        self.article_clicker = ArticleClicker(self.memory)
        self.command_parser = CommandParser()
        self.logger = ResearchLogger()
        
        self.cycle_count = 0
        self.current_url = None
        self.home_url = None
        self.session_urls = []
    
    def capture_claude_command(self):
        """Capture and parse Claude's command"""
        claude_agent = KaiClaudeRegionAgent()
        stable_text = claude_agent.wait_for_response_completion_fast()
        
        if not stable_text:
            print("No text captured from Claude region.")
            return None
        
        print(f"Captured: {stable_text[:100]}...")
        
        # Parse command
        command = self.command_parser.parse_command(stable_text)
        
        if command:
            print(f"Parsed command: {command['type']} (confidence: {command['confidence']:.1f})")
        else:
            print("Could not parse command")
        
        return command
    
    async def execute_command(self, command):
        """Execute parsed command"""
        if not command:
            return False
        
        try:
            if command["type"] == "new_site":
                return await self.navigate_to_site(command["url"])
            elif command["type"] == "article_click":
                return await self.click_article(command["query"])
            elif command["type"] == "navigation":
                return await self.handle_navigation(command["action"])
            else:
                print(f"Unknown command type: {command['type']}")
                return False
                
        except Exception as e:
            print(f"Command execution failed: {e}")
            return False
    
    async def navigate_to_site(self, url):
        """Navigate to a new website"""
        self.current_url = url
        if not self.home_url:
            self.home_url = url
        
        self.session_urls.append(url)
        
        # Switch to browser
        KaiDesktopAgent(direction="right", presses=1).run_fast()
        time.sleep(0.7)
        
        # Open URL
        web_agent = KaiWebAgent(url=url)
        web_agent.run_fast()
        time.sleep(2.0)
        
        # Capture homepage
        subprocess.run(["screencapture", "-c"], check=True, timeout=8)
        
        self.logger.log_action("navigate", url, f"Opened homepage: {url}")
        return True
    
    async def click_article(self, query):
        """Click on a specific article"""
        if not self.current_url:
            print("No current URL - cannot click article")
            return False
        
        # Switch to browser
        KaiDesktopAgent(direction="right", presses=1).run_fast()
        time.sleep(0.7)
        
        success = False
        article_info = None
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(self.current_url if self.current_url.startswith('http') else f"https://{self.current_url}")
                
                domain = self.current_url.split('/')[2] if '/' in self.current_url else self.current_url
                
                # Try to find and click article
                result = await self.article_clicker.find_and_click_article(page, domain, query)
                
                if result["success"]:
                    success = True
                    article_info = result
                    
                    # Take screenshot of article
                    time.sleep(2)
                    subprocess.run(["screencapture", "-c"], check=True, timeout=8)
                    
                    self.logger.log_action("article_click", self.current_url, 
                                         f"Clicked: {result.get('article_title', query)}", True)
                else:
                    self.logger.log_action("article_click", self.current_url,
                                         f"Failed to find: {query}", False)
                
                await browser.close()
                
        except Exception as e:
            print(f"Article clicking error: {e}")
            self.logger.log_action("article_click", self.current_url, f"Error: {e}", False)
        
        return success
    
    async def handle_navigation(self, action):
        """Handle navigation commands like home/back"""
        if action == "home" and self.home_url:
            return await self.navigate_to_site(self.home_url)
        elif action == "back":
            # Simple back implementation
            print("Back command received (basic implementation)")
            return True
        
        return False
    
    def send_screenshot_to_claude(self, context=""):
        """Send screenshot and context to Claude"""
        # Return to Claude
        KaiDesktopAgent(direction="left", presses=1).run_fast()
        time.sleep(1.0)
        
        try:
            # Send screenshot
            claude_input_x, claude_input_y = 1845, 1280
            pyautogui.click(claude_input_x, claude_input_y)
            time.sleep(0.3)
            
            pyautogui.hotkey("command", "a")
            time.sleep(0.2)
            pyautogui.hotkey("command", "v")
            time.sleep(1.2)
            pyautogui.press("enter")
            time.sleep(0.5)
            
            # Send follow-up with context
            if context:
                follow_up = f"{context} What would you like to explore next?"
            else:
                follow_up = "What article should I click on, or which website should we visit next?"
            
            pyautogui.typewrite(follow_up, interval=0.008)
            time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"Error sending to Claude: {e}")
            return False
    
    async def run_cycle(self):
        """Run one research cycle"""
        self.cycle_count += 1
        print(f"\n=== Research Cycle {self.cycle_count} ===")
        
        # Capture command from Claude
        command = self.capture_claude_command()
        if not command:
            print("No valid command received")
            return False
        
        # Execute command
        success = await self.execute_command(command)
        
        # Send results back to Claude
        if success:
            context = f"Completed: {command['type']}"
        else:
            context = f"Failed: {command['type']}"
        
        self.send_screenshot_to_claude(context)
        
        return success

async def main():
    """Main research session"""
    print("=== Autonomous Researcher - Hybrid Version ===")
    print("Features:")
    print("- Natural language command parsing")
    print("- Robust article clicking with memory")
    print("- Session logging and progress tracking")
    print("- Fallback strategies for reliability")
    print()
    
    researcher = AutonomousResearcher()
    
    # Initial setup
    KaiDesktopAgent(direction="right", presses=1).run_fast()
    time.sleep(1.0)
    
    # Start with initial site
    print("Starting with BBC News...")
    await researcher.navigate_to_site("bbc.co.uk/news")
    researcher.send_screenshot_to_claude("Started research session with BBC News.")
    
    # Main research loop
    try:
        while True:
            success = await researcher.run_cycle()
            
            if not success:
                print("Cycle failed, continuing...")
            
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        print("\nResearch session ending...")
        researcher.logger.save_session()
        print(f"Total cycles completed: {researcher.cycle_count}")
        print(f"Sites visited: {len(set(researcher.session_urls))}")

if __name__ == "__main__":
    asyncio.run(main())