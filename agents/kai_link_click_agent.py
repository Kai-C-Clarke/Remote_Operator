import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import base64
import io
from PIL import Image
import pytesseract

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KaiLinkClickAgent:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Load intents configuration
        self.intents = self._load_intents()
        
        # Action handlers mapping
        self.action_handlers = {
            'click': self._handle_click_action,
            'extract_text': self._handle_extract_text_action,
            'navigate': self._handle_navigate_action
        }
        
        # Method handlers for fallback strategies
        self.method_handlers = {
            'css': self._try_css_method,
            'xpath': self._try_xpath_method,
            'text-contains': self._try_text_contains_method,
            'browser_back': self._try_browser_back_method,
            'coordinate': self._try_coordinate_method
        }
        
        # Click strategies with success tracking
        self.click_strategies = {
            'primary': self._click_primary_strategy,
            'coordinate': self._click_coordinate_strategy,
            'xpath': self._click_xpath_strategy,
            'css_selector': self._click_css_selector_strategy
        }
        self.strategy_stats = {strategy: {'attempts': 0, 'successes': 0} for strategy in self.click_strategies}

    def _load_intents(self) -> Dict[str, Any]:
        """Load intents from JSON configuration file"""
        try:
            # Try to load missing_intents.json first, then intents.json
            for filename in ["missing_intents.json", "intents.json"]:
                intents_path = Path(filename)
                if intents_path.exists():
                    with open(intents_path, 'r') as f:
                        intents = json.load(f)
                        logger.info(f"Loaded intents from {filename}")
                        return intents
            
            # Return default intents if no file exists
            logger.warning("No intent configuration file found, using defaults")
            return {
                "navigate_to_article": {
                    "description": "Navigate to and click on a specific article link",
                    "action_type": "click",
                    "parameters": {
                        "target_description": "string - description of the article to find and click",
                        "selector_hints": "optional array - CSS selectors to try",
                        "text_hints": "optional array - text patterns to match"
                    }
                },
                "read_content": {
                    "description": "Extract and analyze main content from the current page",
                    "primary": "article, main, .content, .story-body, .post-content",
                    "fallbacks": [
                        {"method": "css", "value": "[role='main']"},
                        {"method": "css", "value": ".article-content"},
                        {"method": "css", "value": "body"}
                    ],
                    "action_type": "extract_text",
                    "timeout": 10000,
                    "min_content_length": 50,
                    "max_content_length": 5000
                },
                "navigate_back": {
                    "description": "Navigate back to the previous page",
                    "primary": "browser_back",
                    "fallbacks": [
                        {"method": "css", "value": "[aria-label*='back' i]"},
                        {"method": "text-contains", "value": "Back"},
                        {"method": "browser_back", "value": ""}
                    ],
                    "action_type": "navigate",
                    "timeout": 5000,
                    "verify_navigation": True
                }
            }
        except Exception as e:
            logger.error(f"Error loading intents: {e}")
            return {}

    async def start_browser(self):
        """Initialize browser and context"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
        
        # Set up request/response logging
        self.page.on('request', lambda request: logger.debug(f"Request: {request.method} {request.url}"))
        self.page.on('response', lambda response: logger.debug(f"Response: {response.status} {response.url}"))

    async def stop_browser(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def execute_intent(self, intent_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific intent with given parameters"""
        if intent_name not in self.intents:
            return {
                'success': False,
                'error': f'Unknown intent: {intent_name}',
                'intent': intent_name,
                'timestamp': time.time()
            }
        
        intent_config = self.intents[intent_name]
        action_type = intent_config.get('action_type')
        
        if action_type not in self.action_handlers:
            return {
                'success': False,
                'error': f'Unknown action type: {action_type}',
                'intent': intent_name,
                'action_type': action_type,
                'timestamp': time.time()
            }
        
        # Merge intent parameters with provided parameters
        merged_params = intent_config.copy()
        if parameters:
            merged_params.update(parameters)
        
        logger.info(f"Executing intent '{intent_name}' with action type '{action_type}'")
        
        try:
            handler = self.action_handlers[action_type]
            result = await handler(merged_params)
            result.update({
                'intent': intent_name,
                'action_type': action_type,
                'timestamp': time.time()
            })
            return result
        except Exception as e:
            logger.error(f"Error executing intent '{intent_name}': {e}")
            return {
                'success': False,
                'error': str(e),
                'intent': intent_name,
                'action_type': action_type,
                'timestamp': time.time()
            }

    async def _handle_extract_text_action(self, intent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text extraction using primary + fallback strategy"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            timeout = intent_config.get('timeout', 10000)
            min_length = intent_config.get('min_content_length', 50)
            max_length = intent_config.get('max_content_length', 5000)
            
            # Wait for page to be ready
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            
            extracted_content = ""
            method_used = None
            
            # Try primary selectors first
            primary = intent_config.get('primary', '')
            if primary:
                if primary == "browser_back":
                    # Special case - this shouldn't be used for extract_text
                    pass
                else:
                    # Split comma-separated selectors
                    primary_selectors = [s.strip() for s in primary.split(',')]
                    extracted_content, method_used = await self._extract_with_selectors(primary_selectors, max_length)
            
            # If primary failed, try fallbacks
            if not extracted_content.strip() and 'fallbacks' in intent_config:
                for fallback in intent_config['fallbacks']:
                    method = fallback.get('method')
                    value = fallback.get('value')
                    
                    if method == 'css' and value:
                        content, used = await self._extract_with_selectors([value], max_length)
                        if content.strip():
                            extracted_content = content
                            method_used = f"css: {value}"
                            break
                    elif method == 'xpath' and value:
                        try:
                            element = await self.page.query_selector(f"xpath={value}")
                            if element:
                                content = await element.inner_text()
                                if content.strip():
                                    extracted_content = content[:max_length]
                                    method_used = f"xpath: {value}"
                                    break
                        except Exception as e:
                            logger.debug(f"XPath fallback failed: {e}")
                            continue
            
            # Validate content length
            if len(extracted_content.strip()) < min_length:
                return {
                    'success': False,
                    'error': f'Content too short: {len(extracted_content.strip())} < {min_length}',
                    'content_length': len(extracted_content.strip()),
                    'min_required': min_length
                }
            
            # Get page metadata
            page_title = await self.page.title()
            page_url = self.page.url
            
            return {
                'success': True,
                'content': extracted_content.strip(),
                'title': page_title,
                'url': page_url,
                'content_length': len(extracted_content.strip()),
                'method_used': method_used,
                'min_length_met': len(extracted_content.strip()) >= min_length,
                'message': f'Successfully extracted {len(extracted_content.strip())} characters using {method_used}'
            }
            
        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to extract text content'
            }

    async def _extract_with_selectors(self, selectors: List[str], max_length: int) -> tuple:
        """Extract content using a list of CSS selectors"""
        exclude_selectors = [
            'nav', 'header', 'footer', '.ad', '.advertisement', 
            '.social-share', '.comments', '.sidebar', 'script', 'style'
        ]
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector.strip())
                if elements:
                    combined_content = ""
                    for element in elements:
                        # Remove excluded elements
                        for exclude_selector in exclude_selectors:
                            try:
                                excluded_elements = await element.query_selector_all(exclude_selector)
                                for excluded in excluded_elements:
                                    await excluded.evaluate('el => el.remove()')
                            except:
                                pass
                        
                        # Extract text content
                        text = await element.inner_text()
                        if text.strip():
                            combined_content += text.strip() + "\n\n"
                    
                    if combined_content.strip():
                        return combined_content[:max_length], f"css: {selector}"
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        return "", None

    async def _handle_navigate_action(self, intent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle navigation using primary + fallback strategy"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            timeout = intent_config.get('timeout', 5000)
            verify_navigation = intent_config.get('verify_navigation', True)
            original_url = self.page.url
            
            # Try primary method first
            primary = intent_config.get('primary', 'browser_back')
            
            if primary == 'browser_back':
                result = await self._try_browser_back_method("", timeout)
                if result['success']:
                    return self._verify_navigation_result(result, original_url, verify_navigation, "browser_back")
            
            # If primary failed, try fallbacks
            if 'fallbacks' in intent_config:
                for fallback in intent_config['fallbacks']:
                    method = fallback.get('method')
                    value = fallback.get('value', '')
                    
                    if method in self.method_handlers:
                        result = await self.method_handlers[method](value, timeout)
                        if result['success']:
                            return self._verify_navigation_result(result, original_url, verify_navigation, f"{method}: {value}")
            
            return {
                'success': False,
                'error': 'All navigation methods failed',
                'original_url': original_url,
                'message': 'Could not navigate back using any available method'
            }
            
        except Exception as e:
            logger.error(f"Error in navigation: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Navigation failed with exception'
            }

    def _verify_navigation_result(self, result: Dict[str, Any], original_url: str, verify: bool, method_used: str) -> Dict[str, Any]:
        """Verify that navigation actually occurred"""
        if not verify:
            result['method_used'] = method_used
            return result
        
        current_url = self.page.url
        if current_url != original_url:
            result.update({
                'navigation_verified': True,
                'original_url': original_url,
                'new_url': current_url,
                'method_used': method_used
            })
        else:
            result.update({
                'success': False,
                'navigation_verified': False,
                'error': 'Navigation did not change URL',
                'original_url': original_url,
                'current_url': current_url,
                'method_used': method_used
            })
        
        return result

    async def _try_css_method(self, selector: str, timeout: int) -> Dict[str, Any]:
        """Try to find and click element using CSS selector"""
        try:
            element = await self.page.query_selector(selector)
            if element and await element.is_visible():
                await element.scroll_into_view_if_needed()
                await element.click()
                await asyncio.sleep(1)  # Wait for navigation
                return {
                    'success': True,
                    'url': self.page.url,
                    'title': await self.page.title(),
                    'message': f'Successfully clicked element with selector: {selector}'
                }
            return {'success': False, 'error': f'Element not found or not visible: {selector}'}
        except Exception as e:
            return {'success': False, 'error': f'CSS method failed: {e}'}

    async def _try_xpath_method(self, xpath: str, timeout: int) -> Dict[str, Any]:
        """Try to find and click element using XPath"""
        try:
            element = await self.page.query_selector(f"xpath={xpath}")
            if element and await element.is_visible():
                await element.scroll_into_view_if_needed()
                await element.click()
                await asyncio.sleep(1)  # Wait for navigation
                return {
                    'success': True,
                    'url': self.page.url,
                    'title': await self.page.title(),
                    'message': f'Successfully clicked element with XPath: {xpath}'
                }
            return {'success': False, 'error': f'Element not found or not visible: {xpath}'}
        except Exception as e:
            return {'success': False, 'error': f'XPath method failed: {e}'}

    async def _try_text_contains_method(self, text: str, timeout: int) -> Dict[str, Any]:
        """Try to find and click element containing specific text"""
        try:
            # Look for clickable elements containing the text
            selectors = ['a', 'button', '[role="button"]', '[onclick]']
            
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    element_text = await element.inner_text()
                    if text.lower() in element_text.lower().strip():
                        if await element.is_visible():
                            await element.scroll_into_view_if_needed()
                            await element.click()
                            await asyncio.sleep(1)  # Wait for navigation
                            return {
                                'success': True,
                                'url': self.page.url,
                                'title': await self.page.title(),
                                'message': f'Successfully clicked element containing text: {text}'
                            }
            
            return {'success': False, 'error': f'No clickable element found containing text: {text}'}
        except Exception as e:
            return {'success': False, 'error': f'Text-contains method failed: {e}'}

    async def _try_browser_back_method(self, value: str, timeout: int) -> Dict[str, Any]:
        """Try to navigate back using browser history"""
        try:
            # Check if we can go back
            can_go_back = await self.page.evaluate('() => window.history.length > 1')
            if not can_go_back:
                return {
                    'success': False,
                    'error': 'Cannot navigate back - no history available'
                }
            
            # Navigate back
            await self.page.go_back(timeout=timeout)
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            
            return {
                'success': True,
                'url': self.page.url,
                'title': await self.page.title(),
                'message': 'Successfully navigated back using browser history'
            }
        except Exception as e:
            return {'success': False, 'error': f'Browser back method failed: {e}'}

    async def _try_coordinate_method(self, coordinates: str, timeout: int) -> Dict[str, Any]:
        """Try to click at specific coordinates"""
        try:
            if ',' in coordinates:
                x, y = map(int, coordinates.split(','))
                await self.page.mouse.click(x, y)
                await asyncio.sleep(1)  # Wait for navigation
                return {
                    'success': True,
                    'url': self.page.url,
                    'title': await self.page.title(),
                    'message': f'Successfully clicked at coordinates: {coordinates}'
                }
            return {'success': False, 'error': f'Invalid coordinates format: {coordinates}'}
        except Exception as e:
            return {'success': False, 'error': f'Coordinate method failed: {e}'}

    async def _handle_click_action(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle click actions with multi-strategy approach (legacy support)"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        target_description = parameters.get('target_description', '')
        selector_hints = parameters.get('selector_hints', [])
        text_hints = parameters.get('text_hints', [])
        
        logger.info(f"Attempting to find and click: {target_description}")
        
        # Wait for page to be ready
        await self.page.wait_for_load_state('networkidle', timeout=10000)
        
        # Take screenshot for debugging
        screenshot_data = await self._take_screenshot()
        
        # Handle cookie banners first
        await self._handle_cookie_banners()
        
        # Try multiple strategies to find and click the target
        strategies_to_try = ['primary', 'coordinate', 'xpath', 'css_selector']
        
        for strategy in strategies_to_try:
            self.strategy_stats[strategy]['attempts'] += 1
            logger.info(f"Trying {strategy} strategy")
            
            try:
                success = await self.click_strategies[strategy](
                    target_description, selector_hints, text_hints
                )
                
                if success:
                    self.strategy_stats[strategy]['successes'] += 1
                    await asyncio.sleep(2)  # Wait for navigation/page changes
                    
                    return {
                        'success': True,
                        'strategy_used': strategy,
                        'target_description': target_description,
                        'url_after_click': self.page.url,
                        'screenshot': screenshot_data,
                        'message': f'Successfully clicked using {strategy} strategy'
                    }
            except Exception as e:
                logger.warning(f"{strategy} strategy failed: {e}")
                continue
        
        return {
            'success': False,
            'target_description': target_description,
            'strategies_attempted': strategies_to_try,
            'screenshot': screenshot_data,
            'error': 'All click strategies failed',
            'message': f'Could not find or click target: {target_description}'
        }

    async def _click_primary_strategy(self, target_description: str, selector_hints: List[str], text_hints: List[str]) -> bool:
        """Primary strategy: Look for links and buttons containing target text"""
        try:
            # Common selectors for clickable elements
            clickable_selectors = [
                'a[href]',
                'button',
                '[role="button"]',
                '[onclick]',
                '.btn',
                '.button',
                '.link'
            ] + selector_hints
            
            for selector in clickable_selectors:
                elements = await self.page.query_selector_all(selector)
                
                for element in elements:
                    element_text = await element.inner_text()
                    element_text_lower = element_text.lower().strip()
                    target_lower = target_description.lower().strip()
                    
                    # Check if element text matches target description
                    if (target_lower in element_text_lower or 
                        any(hint.lower() in element_text_lower for hint in text_hints) or
                        any(word in element_text_lower for word in target_lower.split())):
                        
                        logger.info(f"Found matching element with text: '{element_text[:100]}'")
                        
                        # Ensure element is visible and clickable
                        if await element.is_visible():
                            await element.scroll_into_view_if_needed()
                            await element.click()
                            return True
            
            return False
        except Exception as e:
            logger.error(f"Primary strategy error: {e}")
            return False

    async def _click_coordinate_strategy(self, target_description: str, selector_hints: List[str], text_hints: List[str]) -> bool:
        """Coordinate strategy: Use OCR to find text and click coordinates"""
        try:
            screenshot = await self.page.screenshot()
            
            # Use OCR to find text locations
            image = Image.open(io.BytesIO(screenshot))
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            target_words = target_description.lower().split()
            
            for i, text in enumerate(ocr_data['text']):
                if text.strip() and any(word in text.lower() for word in target_words):
                    x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                    y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                    
                    logger.info(f"OCR found '{text}' at coordinates ({x}, {y})")
                    await self.page.mouse.click(x, y)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Coordinate strategy error: {e}")
            return False

    async def _click_xpath_strategy(self, target_description: str, selector_hints: List[str], text_hints: List[str]) -> bool:
        """XPath strategy: Use XPath expressions to find elements"""
        try:
            # Generate XPath expressions for common patterns
            xpath_expressions = [
                f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_description.lower()}')]",
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_description.lower()}')]",
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_description.lower()}') and (@href or @onclick or contains(@class, 'btn') or contains(@class, 'button'))]"
            ]
            
            for xpath in xpath_expressions:
                try:
                    element = await self.page.query_selector(f"xpath={xpath}")
                    if element and await element.is_visible():
                        await element.scroll_into_view_if_needed()
                        await element.click()
                        return True
                except Exception:
                    continue
            
            return False
        except Exception as e:
            logger.error(f"XPath strategy error: {e}")
            return False

    async def _click_css_selector_strategy(self, target_description: str, selector_hints: List[str], text_hints: List[str]) -> bool:
        """CSS selector strategy: Try specific CSS selectors"""
        try:
            # Generate CSS selectors based on common patterns
            css_selectors = selector_hints + [
                f'a[title*="{target_description}" i]',
                f'button[title*="{target_description}" i]',
                f'[aria-label*="{target_description}" i]',
                f'[data-title*="{target_description}" i]'
            ]
            
            for selector in css_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        await element.scroll_into_view_if_needed()
                        await element.click()
                        return True
                except Exception:
                    continue
            
            return False
        except Exception as e:
            logger.error(f"CSS selector strategy error: {e}")
            return False

    async def _handle_cookie_banners(self):
        """Detect and handle cookie consent banners"""
        try:
            # Wait a moment for cookie banners to appear
            await asyncio.sleep(1)
            
            # First try DOM-based detection
            cookie_selectors = [
                '[id*="cookie" i] button',
                '[class*="cookie" i] button',
                '[id*="consent" i] button',
                '[class*="consent" i] button',
                'button[id*="accept" i]',
                'button[class*="accept" i]',
                '.cookie-banner button',
                '.consent-banner button',
                '#cookieConsent button',
                '[data-testid*="cookie" i] button',
                '[data-testid*="consent" i] button'
            ]
            
            accept_text_patterns = [
                'accept all', 'accept cookies', 'allow all', 'agree',
                'ok', 'continue', 'accept', 'allow', 'agree all'
            ]
            
            for selector in cookie_selectors:
                try:
                    buttons = await self.page.query_selector_all(selector)
                    for button in buttons:
                        if await button.is_visible():
                            button_text = (await button.inner_text()).lower().strip()
                            if any(pattern in button_text for pattern in accept_text_patterns):
                                logger.info(f"Found cookie consent button: '{button_text}'")
                                await button.click()
                                await asyncio.sleep(1)
                                return True
                except Exception:
                    continue
            
            # Fallback to OCR if DOM-based detection fails
            screenshot = await self.page.screenshot()
            image = Image.open(io.BytesIO(screenshot))
            ocr_text = pytesseract.image_to_string(image).lower()
            
            if any(word in ocr_text for word in ['cookie', 'consent', 'privacy']):
                logger.info("Cookie banner detected via OCR, attempting to find accept button")
                
                # Try to find and click accept button using OCR coordinates
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                for i, text in enumerate(ocr_data['text']):
                    if text.strip().lower() in accept_text_patterns:
                        x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                        y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                        
                        logger.info(f"OCR found accept button '{text}' at ({x}, {y})")
                        await self.page.mouse.click(x, y)
                        await asyncio.sleep(1)
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error handling cookie banners: {e}")
            return False

    async def _take_screenshot(self) -> str:
        """Take a screenshot and return as base64 string"""
        try:
            screenshot = await self.page.screenshot()
            return base64.b64encode(screenshot).decode()
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return ""

    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """Navigate to a specific URL"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            page_title = await self.page.title()
            final_url = self.page.url
            
            # Handle any cookie banners that appear
            await self._handle_cookie_banners()
            
            return {
                'success': True,
                'url': final_url,
                'title': page_title,
                'message': f'Successfully navigated to {final_url}'
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to navigate to {url}'
            }

    def get_strategy_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get success statistics for each click strategy"""
        stats = {}
        for strategy, data in self.strategy_stats.items():
            attempts = data['attempts']
            successes = data['successes']
            success_rate = (successes / attempts * 100) if attempts > 0 else 0
            
            stats[strategy] = {
                'attempts': attempts,
                'successes': successes,
                'success_rate': f"{success_rate:.1f}%"
            }
        
        return stats

# Example usage and testing functions
async def test_autonomous_cycle():
    """Test the complete autonomous navigation cycle with new intent structure"""
    agent = KaiLinkClickAgent(headless=False)
    
    try:
        await agent.start_browser()
        
        # Step 1: Navigate to BBC News
        nav_result = await agent.navigate_to_url("https://www.bbc.com/news")
        print(f"Navigation result: {nav_result}")
        
        if nav_result['success']:
            # Step 2: Click on an article (using legacy click action)
            click_result = await agent.execute_intent(
                "navigate_to_article",
                {"target_description": "politics"}
            )
            print(f"Click result: {click_result}")
            
            if click_result['success']:
                # Step 3: Read the content (using new intent structure)
                read_result = await agent.execute_intent("read_content")
                print(f"Read result: {read_result}")
                print(f"Content length: {read_result.get('content_length', 0)} characters")
                print(f"Method used: {read_result.get('method_used', 'N/A')}")
                
                # Step 4: Navigate back (using new intent structure)
                back_result = await agent.execute_intent("navigate_back")
                print(f"Navigate back result: {back_result}")
                print(f"Navigation method: {back_result.get('method_used', 'N/A')}")
                
                # Print strategy statistics
                print("\nStrategy Statistics:")
                stats = agent.get_strategy_stats()
                for strategy, data in stats.items():
                    print(f"  {strategy}: {data['success_rate']} ({data['successes']}/{data['attempts']})")
    
    finally:
        await agent.stop_browser()

if __name__ == "__main__":
    asyncio.run(test_autonomous_cycle())