"""
kai_link_click_agent.py - Enhanced with Advanced Cookie Handling
Autonomous link clicking with comprehensive cookie consent and pop-up handling
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright, Page
# from memory_interface import MemoryInterface
from log_writer import LogWriter
from strategy_scorer import StrategyScorer

class KaiLinkClickAgent:
    def __init__(self, memory_file="memory.json", logs_dir="logs", stats_file="strategy_stats.json"):
        # self.memory = MemoryInterface(memory_file)
        self.memory = None  # Temporarily disabled
        self.log = LogWriter(logs_dir)
        self.scorer = StrategyScorer(stats_file)
        
        # Comprehensive cookie banner selectors
        self.cookie_selectors = [
            # BBC-specific (from your screenshot)
            "button:has-text('Accept additional cookies')",
            "button:has-text('Reject additional cookies')",
            "button:has-text('Let me choose')",
            
            # Generic accept patterns
            "button:has-text('Accept all')",
            "button:has-text('Accept All')",
            "button:has-text('Accept cookies')",
            "button:has-text('Accept & Continue')",
            "button:has-text('I accept')",
            "button:has-text('Agree and continue')",
            "button:has-text('Allow all')",
            "button:has-text('Continue')",
            "button:has-text('OK')",
            "button:has-text('Got it')",
            "button:has-text('Understood')",
            
            # CSS/ID based selectors
            "[id*='accept'][id*='cookie']",
            "[id*='accept'][id*='consent']",
            "[class*='accept'][class*='cookie']",
            "[class*='accept'][class*='consent']",
            "[data-testid*='accept']",
            "[data-cy*='accept']",
            "[aria-label*='Accept']",
            
            # Common cookie banner frameworks
            ".fc-primary-button",          # OneTrust
            ".fc-button-label",            # OneTrust
            "#onetrust-accept-btn-handler", # OneTrust
            ".ot-pc-refuse-all-handler",   # OneTrust
            ".cmp-btn_accept-all",         # CMP
            ".consent-accept",             # Generic
            ".cookie-accept",              # Generic
            ".gdpr-accept",                # GDPR
            "[data-role='acceptAll']",     # Custom
            
            # Fallback patterns
            "button[title*='Accept']",
            "button[value*='Accept']",
            "a[href*='accept']",
            "input[value*='Accept']"
        ]
        
        # Dismiss/close patterns as backup
        self.dismiss_selectors = [
            "button:has-text('Reject all')",
            "button:has-text('Decline')",
            "button:has-text('No thanks')",
            "button:has-text('Close')",
            "button:has-text('Dismiss')",
            "[aria-label*='Close']",
            "[aria-label*='Dismiss']",
            ".close-button",
            ".modal-close",
            ".popup-close"
        ]

    async def detect_cookie_banners_dom(self, page: Page):
        """Detect cookie banners by analyzing DOM structure"""
        try:
            # Look for common cookie banner containers
            banner_containers = await page.evaluate("""
                () => {
                    const containers = [];
                    
                    // Look for elements with cookie-related text
                    const cookieText = ['cookie', 'consent', 'privacy', 'gdpr', 'tracking'];
                    const elements = document.querySelectorAll('div, section, aside, nav');
                    
                    for (let el of elements) {
                        const text = el.textContent.toLowerCase();
                        const className = el.className.toLowerCase();
                        const id = el.id.toLowerCase();
                        
                        // Check if element contains cookie-related keywords
                        const hasKeyword = cookieText.some(keyword => 
                            text.includes(keyword) || className.includes(keyword) || id.includes(keyword)
                        );
                        
                        // Check if element has buttons (likely interactive)
                        const hasButtons = el.querySelectorAll('button, a').length > 0;
                        
                        if (hasKeyword && hasButtons) {
                            // Get element info
                            const rect = el.getBoundingClientRect();
                            containers.push({
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id,
                                textContent: text.substring(0, 200),
                                hasButtons: el.querySelectorAll('button').length,
                                isVisible: rect.width > 0 && rect.height > 0,
                                position: {
                                    top: rect.top,
                                    bottom: rect.bottom,
                                    left: rect.left,
                                    right: rect.right
                                }
                            });
                        }
                    }
                    
                    return containers;
                }
            """)
            
            self.log.log_event(f"Found {len(banner_containers)} potential cookie containers via DOM analysis")
            for container in banner_containers[:3]:  # Log first 3
                self.log.log_event(f"   Container: {container['tagName']} - {container['textContent'][:50]}...")
            
            return banner_containers
            
        except Exception as e:
            self.log.log_event(f"DOM analysis failed: {str(e)}")
            return []

    async def find_cookie_buttons_in_container(self, page: Page, container_info):
        """Find clickable buttons within a detected container"""
        try:
            # Use the container's position/class/id to find buttons within it
            buttons = await page.evaluate(f"""
                (containerInfo) => {{
                    const buttons = [];
                    
                    // Find the container element
                    let container = null;
                    if (containerInfo.id) {{
                        container = document.getElementById(containerInfo.id);
                    }}
                    if (!container && containerInfo.className) {{
                        const className = containerInfo.className.split(' ')[0];
                        if (className) {{
                            container = document.querySelector('.' + className);
                        }}
                    }}
                    
                    if (container) {{
                        const buttonElements = container.querySelectorAll('button, a[role="button"], input[type="button"]');
                        
                        for (let btn of buttonElements) {{
                            const text = btn.textContent || btn.value || '';
                            const rect = btn.getBoundingClientRect();
                            
                            buttons.push({{
                                text: text.trim(),
                                className: btn.className,
                                id: btn.id,
                                tagName: btn.tagName,
                                isVisible: rect.width > 0 && rect.height > 0,
                                selector: btn.id ? '#' + btn.id : (btn.className ? '.' + btn.className.split(' ')[0] : '')
                            }});
                        }}
                    }}
                    
                    return buttons;
                }}
            """, container_info)
            
            return buttons
            
        except Exception as e:
            self.log.log_event(f"Button search failed: {str(e)}")
            return []

    async def handle_interruptions(self, page: Page, max_attempts=3):
        """Enhanced interruption handling with DOM analysis"""
        self.log.log_event("Checking for page interruptions...")
        
        handled_count = 0
        
        for attempt in range(max_attempts):
            # Wait for any delayed popups
            await asyncio.sleep(1.5)
            
            interruption_found = False
            
            # Strategy 1: Use predefined selectors (fast)
            for selector in self.cookie_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=500):
                        self.log.log_event(f"Found cookie button: {selector}")
                        
                        await element.click(timeout=2000)
                        handled_count += 1
                        interruption_found = True
                        
                        self.log.log_event(f"Successfully clicked cookie button")
                        
                        await page.wait_for_load_state('networkidle', timeout=3000)
                        break
                        
                except Exception:
                    continue
            
            # Strategy 2: DOM analysis (if predefined selectors failed)
            if not interruption_found:
                self.log.log_event("Trying DOM-based detection...")
                
                containers = await self.detect_cookie_banners_dom(page)
                
                for container in containers:
                    if not container['isVisible']:
                        continue
                        
                    buttons = await self.find_cookie_buttons_in_container(page, container)
                    
                    # Look for accept-like buttons
                    for button in buttons:
                        text = button['text'].lower()
                        if any(word in text for word in ['accept', 'allow', 'agree', 'continue', 'ok', 'got it']):
                            try:
                                if button['id']:
                                    selector = f"#{button['id']}"
                                elif button['className']:
                                    selector = f".{button['className'].split()[0]}"
                                else:
                                    continue
                                
                                element = page.locator(selector).first
                                if await element.is_visible(timeout=500):
                                    await element.click(timeout=2000)
                                    handled_count += 1
                                    interruption_found = True
                                    
                                    self.log.log_event(f"DOM-based click successful: {button['text']}")
                                    
                                    await page.wait_for_load_state('networkidle', timeout=3000)
                                    break
                                    
                            except Exception:
                                continue
                    
                    if interruption_found:
                        break
            
            # Strategy 3: Try dismiss buttons as last resort
            if not interruption_found:
                for selector in self.dismiss_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=500):
                            await element.click(timeout=2000)
                            handled_count += 1
                            interruption_found = True
                            
                            self.log.log_event(f"Used dismiss button: {selector}")
                            
                            await page.wait_for_load_state('networkidle', timeout=3000)
                            break
                            
                    except Exception:
                        continue
            
            if not interruption_found:
                break
        
        if handled_count > 0:
            self.log.log_event(f"Successfully handled {handled_count} interruption(s)")
        else:
            self.log.log_event("No interruptions detected or all handling failed")
        
        return handled_count

    async def take_debug_screenshot(self, page: Page, filename="cookie_debug.png"):
        """Take a screenshot for debugging cookie detection with proper error handling"""
        try:
            # Create debug_screenshots directory if it doesn't exist
            debug_dir = Path("debug_screenshots")
            debug_dir.mkdir(exist_ok=True)
            
            # Full path for screenshot
            screenshot_path = debug_dir / filename
            
            # Take screenshot with full page capture
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Verify file was created
            if screenshot_path.exists():
                file_size = screenshot_path.stat().st_size
                self.log.log_event(f"Debug screenshot saved: {screenshot_path} ({file_size} bytes)")
            else:
                self.log.log_event(f"Screenshot file not found after save attempt: {screenshot_path}")
                
        except Exception as e:
            self.log.log_event(f"Screenshot failed: {str(e)}")
            
            # Try alternative approach - save to current directory
            try:
                simple_path = Path(filename)
                await page.screenshot(path=str(simple_path), full_page=True)
                if simple_path.exists():
                    self.log.log_event(f"Fallback screenshot saved: {simple_path}")
                else:
                    self.log.log_event(f"Fallback screenshot also failed: {simple_path}")
            except Exception as e2:
                self.log.log_event(f"Fallback screenshot also failed: {str(e2)}")
                
                # Final attempt - try basic screenshot without full_page
                try:
                    basic_path = Path(f"basic_{filename}")
                    await page.screenshot(path=str(basic_path))
                    if basic_path.exists():
                        self.log.log_event(f"Basic screenshot saved: {basic_path}")
                    else:
                        self.log.log_event("All screenshot attempts failed")
                except Exception as e3:
                    self.log.log_event(f"All screenshot attempts failed: {str(e3)}")
    
    async def find_clickable_element(self, page: Page, intent_data: dict, domain: str, intent_name: str):
        """Find clickable element using multiple strategies with memory prioritization"""
        
        strategies_to_try = []
        
        # Check memory for previously successful strategy (disabled for now)
        if self.memory:
            remembered = self.memory.get(domain, intent_name)
            if remembered:
                # Try remembered strategy first
                strategies_to_try.append({
                    'method': 'memory',
                    'value': remembered['successful_selector'],
                    'priority': 1
                })
                self.log.log_memory_strategy(remembered['successful_selector'])
        
        # Add primary selector
        if 'primary_selector' in intent_data:
            strategies_to_try.append({
                'method': 'primary',
                'value': intent_data['primary_selector'],
                'priority': 2
            })
        
        # Add fallback strategies
        if 'fallbacks' in intent_data:
            for i, fallback in enumerate(intent_data['fallbacks']):
                strategies_to_try.append({
                    'method': fallback.get('method', 'text-contains'),
                    'value': fallback.get('value', ''),
                    'priority': 3 + i
                })
        
        # Sort by priority (memory first)
        strategies_to_try.sort(key=lambda x: x['priority'])
        
        # Try each strategy
        for strategy in strategies_to_try:
            element = await self._try_strategy(page, strategy)
            if element:
                strategy_name = f"{strategy['method']}: {strategy['value']}"
                self.log.log_success(strategy_name)
                
                # Store successful strategy in memory (disabled for now)
                if self.memory:
                    self.memory.store(domain, intent_name, strategy_name)
                self.scorer.record_result(domain, intent_name, strategy_name, success=True)
                
                return element, strategy_name
            else:
                strategy_name = f"{strategy['method']}: {strategy['value']}"
                self.log.log_attempt(strategy_name)
        
        # All strategies failed
        self.scorer.record_result(domain, intent_name, "all_strategies", success=False)
        return None, None
    
    async def _try_strategy(self, page: Page, strategy: dict):
        """Try a specific strategy to find an element"""
        method = strategy['method']
        value = strategy['value']
        
        try:
            if method == 'memory':
                # Parse memory format (e.g., "text-contains: Next")
                if ':' in value:
                    mem_method, mem_value = value.split(':', 1)
                    return await self._try_selector(page, mem_method.strip(), mem_value.strip())
                else:
                    return await self._try_selector(page, 'css', value)
            
            return await self._try_selector(page, method, value)
            
        except Exception as e:
            self.log.log_event(f"Strategy {method}:{value} failed: {str(e)}")
            return None
    
    async def _try_selector(self, page: Page, method: str, value: str):
        """Try specific selector method"""
        timeout = 3000  # 3 second timeout for element finding
        
        try:
            if method == 'text-contains':
                # Find by partial text match
                element = page.locator(f"text={value}").first
                await element.wait_for(timeout=timeout)
                return element
            
            elif method == 'text-exact':
                # Find by exact text match
                element = page.locator(f'text="{value}"').first
                await element.wait_for(timeout=timeout)
                return element
            
            elif method == 'text-regex':
                # Find by regex text match
                element = page.locator(f"text=/{value}/").first
                await element.wait_for(timeout=timeout)
                return element
            
            elif method == 'aria-label':
                # Find by aria-label
                element = page.locator(f'[aria-label*="{value}"]').first
                await element.wait_for(timeout=timeout)
                return element
            
            elif method == 'css':
                # CSS selector
                element = page.locator(value).first
                await element.wait_for(timeout=timeout)
                return element
            
            elif method == 'xpath':
                # XPath selector
                element = page.locator(f"xpath={value}").first
                await element.wait_for(timeout=timeout)
                return element
            
            elif method == 'primary':
                # Try primary selector as CSS first, then as text
                try:
                    element = page.locator(value).first
                    await element.wait_for(timeout=timeout)
                    return element
                except:
                    # Fallback to text search
                    element = page.locator(f"text={value}").first
                    await element.wait_for(timeout=timeout)
                    return element
            
            else:
                self.log.log_event(f"Unknown selector method: {method}")
                return None
                
        except Exception as e:
            # Element not found or timeout
            return None
    
    async def click_element_safely(self, page: Page, element, strategy_name: str):
        """Click element with safety checks"""
        try:
            # Check if element is visible and enabled
            if not await element.is_visible():
                self.log.log_event(f"Element not visible: {strategy_name}")
                return False
            
            if not await element.is_enabled():
                self.log.log_event(f"Element not enabled: {strategy_name}")
                return False
            
            # Scroll element into view if needed
            await element.scroll_into_view_if_needed()
            
            # Small delay to ensure element is ready
            await asyncio.sleep(0.2)
            
            # Click the element
            await element.click()
            
            # Wait for potential navigation or page changes
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            self.log.log_event(f"Successfully clicked: {strategy_name}")
            return True
            
        except Exception as e:
            self.log.log_event(f"Click failed for {strategy_name}: {str(e)}")
            return False
    
    async def autonomous_click(self, page: Page, intent_data: dict, domain: str, intent_name: str):
        """Main autonomous clicking operation with enhanced interruption handling"""
        self.log.start_session(domain, intent_name)
        
        try:
            # Take initial screenshot for debugging
            await self.take_debug_screenshot(page, f"before_interruptions_{domain}_{intent_name}.png")
            
            # Enhanced interruption handling
            await self.handle_interruptions(page)
            
            # Take screenshot after handling interruptions
            await self.take_debug_screenshot(page, f"after_interruptions_{domain}_{intent_name}.png")
            
            # Find the element to click
            element, strategy_name = await self.find_clickable_element(page, intent_data, domain, intent_name)
            
            if not element:
                self.log.log_failure("No clickable element found with any strategy")
                return {
                    'success': False,
                    'strategy': None,
                    'error': 'Element not found'
                }
            
            # Click the element
            click_success = await self.click_element_safely(page, element, strategy_name)
            
            if click_success:
                # After clicking, check for new interruptions
                await self.handle_interruptions(page, max_attempts=2)
                
                # Final screenshot
                await self.take_debug_screenshot(page, f"final_result_{domain}_{intent_name}.png")
                
                self.log.log_success(f"Autonomous click completed: {strategy_name}")
                return {
                    'success': True,
                    'strategy': strategy_name,
                    'url_after_click': page.url
                }
            else:
                self.log.log_failure(f"Click failed: {strategy_name}")
                return {
                    'success': False,
                    'strategy': strategy_name,
                    'error': 'Click operation failed'
                }
                
        except Exception as e:
            self.log.log_failure(f"Autonomous click error: {str(e)}")
            return {
                'success': False,
                'strategy': None,
                'error': str(e)
            }
        finally:
            self.log.save(domain, intent_name)


async def main():
    """Example usage and testing"""
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python kai_link_click_agent.py <url> <intent_name> <target_text>")
        print("Example: python kai_link_click_agent.py https://example.com click_next 'Next page'")
        return
    
    url = sys.argv[1]
    intent_name = sys.argv[2] 
    target_text = sys.argv[3]
    
    # Create simple intent for testing
    intent_data = {
        "primary_selector": target_text,
        "fallbacks": [
            {"method": "text-contains", "value": target_text},
            {"method": "text-exact", "value": target_text},
            {"method": "aria-label", "value": target_text}
        ]
    }
    
    domain = url.split('/')[2]  # Extract domain
    
    agent = KaiLinkClickAgent()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Perform autonomous click
        result = await agent.autonomous_click(page, intent_data, domain, intent_name)
        
        print(f"Click result: {json.dumps(result, indent=2)}")
        
        # Take screenshot of result
        await page.screenshot(path=f"click_result_{intent_name}.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())