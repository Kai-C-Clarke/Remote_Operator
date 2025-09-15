"""
autonomous_navigator_with_clicking.py
Enhanced navigator that can autonomously click links and interact with pages
Now includes integrated hybrid cookie banner detection
"""

import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from datetime import datetime
import logging
from typing import Dict, Any, Optional

# Import your existing components
from agents.kai_link_click_agent import KaiLinkClickAgent
from memory_interface import MemoryInterface
from log_writer import LogWriter
from strategy_scorer import StrategyScorer

# Import the enhanced cookie detection
try:
    import pytesseract
    from PIL import Image, ImageDraw
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OCR dependencies not available for cookie detection: {e}")
    OCR_AVAILABLE = False

class EnhancedCookieDetector:
    """Integrated cookie banner detector for the autonomous navigator"""
    
    def __init__(self, debug_dir: str = "debug_screenshots"):
        self.debug_dir = debug_dir
        self.logger = logging.getLogger('CookieDetector')
        
        # Enhanced cookie keywords
        self.cookie_keywords = {
            'container_selectors': [
                "[id*='cookie']", "[class*='cookie']", "[data-*='cookie']",
                "[id*='consent']", "[class*='consent']", "[data-*='consent']",
                "[id*='gdpr']", "[class*='gdpr']", "[data-*='gdpr']",
                "[id*='privacy']", "[class*='privacy']",
                "[role='dialog']", "[role='banner']", "[role='alert']",
                "#CybotCookiebotDialog", "#cookieConsent", "#cookie-banner",
                ".cookie-consent", ".gdpr-consent", ".privacy-notice",
                ".cookie-bar", ".consent-banner"
            ],
            'accept_patterns': [
                'accept', 'agree', 'allow', 'ok', 'enable', 'continue', 
                'got it', 'understand', 'proceed', 'yes', 'confirm'
            ]
        }
    
    async def detect_and_handle_cookies(self, page) -> Dict[str, Any]:
        """Main cookie detection and handling method"""
        self.logger.info("🍪 Starting enhanced cookie banner detection...")
        
        # Take before screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        before_screenshot = f"{self.debug_dir}/before_cookie_handling_{timestamp}.png"
        await page.screenshot(path=before_screenshot)
        self.logger.info(f"Debug screenshot saved: {before_screenshot}")
        
        # Try DOM-based detection first
        dom_result = await self._dom_detection(page)
        if dom_result['success']:
            after_screenshot = f"{self.debug_dir}/after_cookie_dom_{timestamp}.png"
            await page.screenshot(path=after_screenshot)
            self.logger.info(f"✅ Cookie banner handled via DOM: {dom_result['element_text']}")
            return dom_result
        
        # Try OCR fallback if available
        if OCR_AVAILABLE:
            self.logger.info("DOM detection failed, attempting OCR fallback...")
            ocr_result = await self._ocr_detection(page, before_screenshot)
            if ocr_result['success']:
                after_screenshot = f"{self.debug_dir}/after_cookie_ocr_{timestamp}.png"
                await page.screenshot(path=after_screenshot)
                self.logger.info(f"✅ Cookie banner handled via OCR: {ocr_result['element_text']}")
                return ocr_result
        
        # No banner found or couldn't handle
        self.logger.info("No cookie banner detected or unable to handle")
        return {
            'success': False,
            'method': 'none',
            'element_text': '',
            'coordinates': None,
            'details': {'dom_tried': True, 'ocr_available': OCR_AVAILABLE}
        }
    
    async def _dom_detection(self, page) -> Dict[str, Any]:
        """Enhanced DOM-based cookie banner detection"""
        try:
            self.logger.info("Scanning for cookie containers via DOM...")
            containers_found = []
            
            # Find potential cookie containers
            for selector in self.cookie_keywords['container_selectors']:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await self._is_likely_cookie_banner(page, element):
                            containers_found.append(element)
                            self.logger.info(f"Found potential cookie container: {selector}")
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
            
            self.logger.info(f"Found {len(containers_found)} potential cookie containers")
            
            # Try to find accept buttons in containers
            for container in containers_found:
                result = await self._find_accept_button_in_container(page, container)
                if result['success']:
                    return result
            
            # Direct button search if containers didn't work
            return await self._direct_button_search(page)
            
        except Exception as e:
            self.logger.error(f"DOM detection error: {e}")
            return {
                'success': False,
                'method': 'dom',
                'element_text': '',
                'coordinates': None,
                'details': {'error': str(e)}
            }
    
    async def _is_likely_cookie_banner(self, page, element) -> bool:
        """Check if element looks like a cookie banner"""
        try:
            if not await element.is_visible():
                return False
            
            box = await element.bounding_box()
            if not box:
                return False
            
            viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
            
            # Check position - banners are usually at bottom, top, or fixed
            is_bottom = box['y'] + box['height'] > viewport['height'] * 0.7
            is_top = box['y'] < viewport['height'] * 0.3
            position = await page.evaluate("(element) => window.getComputedStyle(element).position", element)
            is_fixed = position in ['fixed', 'absolute']
            
            return is_bottom or is_top or is_fixed
            
        except Exception:
            return False
    
    async def _find_accept_button_in_container(self, page, container) -> Dict[str, Any]:
        """Find and click accept button within a container"""
        try:
            button_selectors = ["button", "a", "[role='button']", "input[type='button']", "input[type='submit']"]
            
            for selector in button_selectors:
                buttons = await container.query_selector_all(selector)
                
                for button in buttons:
                    if not await button.is_visible():
                        continue
                    
                    # Get button text from multiple sources
                    text_content = ""
                    try:
                        text_content = (await button.inner_text()).lower().strip()
                        if not text_content:
                            text_content = (await button.get_attribute('value') or '').lower().strip()
                        if not text_content:
                            text_content = (await button.get_attribute('aria-label') or '').lower().strip()
                    except:
                        continue
                    
                    # Check if text matches accept patterns
                    if any(pattern in text_content for pattern in self.cookie_keywords['accept_patterns']):
                        box = await button.bounding_box()
                        coords = (box['x'] + box['width']/2, box['y'] + box['height']/2) if box else None
                        
                        await button.click()
                        await page.wait_for_timeout(1000)  # Wait for animation
                        
                        return {
                            'success': True,
                            'method': 'dom',
                            'element_text': text_content,
                            'coordinates': coords,
                            'details': {'selector': selector, 'container_based': True}
                        }
            
            return {
                'success': False,
                'method': 'dom',
                'element_text': '',
                'coordinates': None,
                'details': {'container_checked': True, 'no_buttons_found': True}
            }
            
        except Exception as e:
            return {
                'success': False,
                'method': 'dom',
                'element_text': '',
                'coordinates': None,
                'details': {'error': str(e)}
            }
    
    async def _direct_button_search(self, page) -> Dict[str, Any]:
        """Direct search for accept buttons across entire page"""
        try:
            for pattern in self.cookie_keywords['accept_patterns']:
                selectors = [
                    f"button:has-text('{pattern}')",
                    f"a:has-text('{pattern}')",
                    f"[role='button']:has-text('{pattern}')"
                ]
                
                for selector in selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button and await button.is_visible():
                            box = await button.bounding_box()
                            coords = (box['x'] + box['width']/2, box['y'] + box['height']/2) if box else None
                            
                            text = await button.inner_text()
                            await button.click()
                            await page.wait_for_timeout(1000)
                            
                            return {
                                'success': True,
                                'method': 'dom',
                                'element_text': text.strip(),
                                'coordinates': coords,
                                'details': {'direct_search': True, 'pattern': pattern}
                            }
                    except Exception:
                        continue
            
            return {
                'success': False,
                'method': 'dom',
                'element_text': '',
                'coordinates': None,
                'details': {'direct_search_failed': True}
            }
            
        except Exception as e:
            return {
                'success': False,
                'method': 'dom',
                'element_text': '',
                'coordinates': None,
                'details': {'error': str(e)}
            }
    
    async def _ocr_detection(self, page, screenshot_path: str) -> Dict[str, Any]:
        """OCR-based detection for fallback"""
        if not OCR_AVAILABLE:
            return {
                'success': False,
                'method': 'ocr',
                'element_text': '',
                'coordinates': None,
                'details': {'error': 'OCR not available'}
            }
        
        try:
            image = Image.open(screenshot_path)
            width, height = image.size
            
            # Priority regions for scanning
            regions = [
                ('bottom', (0, int(height * 0.75), width, height)),
                ('top', (0, 0, width, int(height * 0.25))),
                ('center', (0, int(height * 0.35), width, int(height * 0.65)))
            ]
            
            for region_name, (x1, y1, x2, y2) in regions:
                region_image = image.crop((x1, y1, x2, y2))
                ocr_data = pytesseract.image_to_data(region_image, output_type=pytesseract.Output.DICT)
                
                for i, text in enumerate(ocr_data['text']):
                    text_clean = text.strip().lower()
                    if text_clean and any(pattern in text_clean for pattern in self.cookie_keywords['accept_patterns']):
                        # Calculate click coordinates
                        rel_x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                        rel_y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                        abs_x = x1 + rel_x
                        abs_y = y1 + rel_y
                        
                        await page.mouse.click(abs_x, abs_y)
                        await page.wait_for_timeout(1000)
                        
                        return {
                            'success': True,
                            'method': 'ocr',
                            'element_text': text.strip(),
                            'coordinates': (abs_x, abs_y),
                            'details': {'region': region_name, 'confidence': ocr_data['conf'][i] if i < len(ocr_data['conf']) else 0}
                        }
            
            return {
                'success': False,
                'method': 'ocr',
                'element_text': '',
                'coordinates': None,
                'details': {'regions_scanned': len(regions)}
            }
            
        except Exception as e:
            return {
                'success': False,
                'method': 'ocr',
                'element_text': '',
                'coordinates': None,
                'details': {'error': str(e)}
            }

class AutonomousNavigator:
    def __init__(self):
        self.intents_file = Path("intents.json")
        self.memory = MemoryInterface("memory.json")
        self.log = LogWriter("logs")
        self.scorer = StrategyScorer("strategy_stats.json")
        self.click_agent = KaiLinkClickAgent()
        self.cookie_detector = EnhancedCookieDetector("debug_screenshots")
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
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
    
    async def handle_page_interruptions(self, page) -> Dict[str, Any]:
        """Handle cookie banners and other page interruptions"""
        return await self.cookie_detector.detect_and_handle_cookies(page)
    
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
            
            # Handle initial page interruptions (cookies, etc.)
            interruption_result = await self.handle_page_interruptions(page)
            if interruption_result['success']:
                print(f"✅ Page interruptions handled: {interruption_result['method']}")
            
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
                    
                    # Handle any new interruptions after navigation
                    await self.handle_page_interruptions(page)
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
            
            # Handle page interruptions first
            await self.handle_page_interruptions(page)
            
            result = await self.click_agent.autonomous_click(page, intent_data, domain, intent_name)
            
            # Take screenshot
            await page.screenshot(path=f"{intent_name}_result.png")
            
            await browser.close()
        
        return result

async def main():
    """Command line interface and examples"""
    navigator = AutonomousNavigator()
    
    if len(sys.argv) < 2:
        print("Autonomous Navigator with Enhanced Cookie Detection")
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
            {"intent": "read_content"},
            {"intent": "navigate_back"}
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