#!/usr/bin/env python3

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
import os

try:
    import pytesseract
    from PIL import Image, ImageDraw
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OCR dependencies not available: {e}")
    OCR_AVAILABLE = False

@dataclass
class CookieDetectionResult:
    """Results from cookie banner detection attempt"""
    success: bool
    method: str  # 'dom' or 'ocr' or 'none'
    element_text: str
    coordinates: Optional[Tuple[int, int]]
    log_details: Dict[str, Any]

class IntegratedCookieBannerDetector:
    """
    Cookie banner detector integrated with the existing navigation system.
    Compatible with the current autonomous navigator architecture.
    """
    
    def __init__(self, debug_dir: str = "debug_screenshots"):
        self.debug_dir = debug_dir
        self.setup_logging()
        os.makedirs(debug_dir, exist_ok=True)
        
        # Enhanced cookie-related keywords
        self.cookie_keywords = {
            'container_selectors': [
                # Common cookie banner containers
                "[id*='cookie']", "[class*='cookie']", "[data-*='cookie']",
                "[id*='consent']", "[class*='consent']", "[data-*='consent']",
                "[id*='gdpr']", "[class*='gdpr']", "[data-*='gdpr']",
                "[id*='privacy']", "[class*='privacy']",
                "[role='dialog']", "[role='banner']", "[role='alert']",
                
                # Specific frameworks
                "#CybotCookiebotDialog", "#cookieConsent", "#cookie-banner",
                ".cookie-consent", ".gdpr-consent", ".privacy-notice",
                ".cookie-bar", ".consent-banner"
            ],
            'accept_text_patterns': [
                'accept', 'agree', 'allow', 'ok', 'enable', 'continue', 
                'got it', 'understand', 'proceed', 'yes', 'confirm'
            ]
        }
    
    def setup_logging(self):
        """Configure logging compatible with existing system"""
        self.logger = logging.getLogger('CookieDetector')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def detect_and_handle_cookie_banner(self, page) -> CookieDetectionResult:
        """
        Main entry point compatible with existing navigation system.
        Returns detection result that can be logged with existing infrastructure.
        """
        self.logger.info("Starting integrated cookie banner detection...")
        
        # Step 1: Try DOM-based detection
        dom_result = await self._enhanced_dom_detection(page)
        if dom_result.success:
            self.logger.info(f"✅ Cookie banner handled via DOM: {dom_result.element_text}")
            return dom_result
        
        # Step 2: OCR fallback if available and DOM failed
        if OCR_AVAILABLE:
            self.logger.info("DOM detection failed, attempting OCR fallback")
            ocr_result = await self._ocr_detection(page)
            if ocr_result.success:
                self.logger.info(f"✅ Cookie banner handled via OCR: {ocr_result.element_text}")
                return ocr_result
        else:
            self.logger.info("OCR not available, skipping OCR detection")
        
        # Step 3: No banner found or could not handle
        self.logger.info("No cookie banner detected or unable to handle")
        return CookieDetectionResult(
            success=False,
            method='none',
            element_text='',
            coordinates=None,
            log_details={'dom_attempted': True, 'ocr_attempted': OCR_AVAILABLE}
        )
    
    async def _enhanced_dom_detection(self, page) -> CookieDetectionResult:
        """Enhanced DOM detection with priority-based selection"""
        try:
            self.logger.info("Scanning for cookie containers...")
            
            # Find all potential cookie containers
            containers_found = []
            
            for selector in self.cookie_keywords['container_selectors']:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await self._is_likely_cookie_banner(page, element):
                            containers_found.append(element)
                            self.logger.info(f"Found potential cookie container: {selector}")
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            self.logger.info(f"Found {len(containers_found)} potential cookie containers")
            
            # Try to find and click accept buttons in containers
            for container in containers_found:
                result = await self._find_and_click_accept_button(page, container)
                if result.success:
                    return result
            
            # If no containers found, try direct button search
            self.logger.info("No containers worked, trying direct button search...")
            return await self._direct_button_search(page)
            
        except Exception as e:
            self.logger.error(f"DOM detection error: {e}")
            return CookieDetectionResult(
                success=False,
                method='dom',
                element_text='',
                coordinates=None,
                log_details={'error': str(e)}
            )
    
    async def _is_likely_cookie_banner(self, page, element) -> bool:
        """Check if element is likely a cookie banner"""
        try:
            # Must be visible
            if not await element.is_visible():
                return False
            
            # Check position and size
            box = await element.bounding_box()
            if not box:
                return False
            
            # Get viewport dimensions
            viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
            
            # Likely positions for cookie banners
            is_bottom = box['y'] + box['height'] > viewport['height'] * 0.7
            is_top = box['y'] < viewport['height'] * 0.3
            is_fixed_position = await page.evaluate(
                "(element) => window.getComputedStyle(element).position", 
                element
            ) in ['fixed', 'absolute']
            
            return is_bottom or is_top or is_fixed_position
            
        except Exception:
            return False
    
    async def _find_and_click_accept_button(self, page, container) -> CookieDetectionResult:
        """Find and click accept button within container"""
        try:
            # Look for buttons/links with accept-related text
            button_selectors = [
                "button", "a", "[role='button']", 
                "input[type='button']", "input[type='submit']"
            ]
            
            for selector in button_selectors:
                buttons = await container.query_selector_all(selector)
                
                for button in buttons:
                    if not await button.is_visible():
                        continue
                    
                    # Get button text
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
                    if any(pattern in text_content for pattern in self.cookie_keywords['accept_text_patterns']):
                        # Get coordinates before clicking
                        box = await button.bounding_box()
                        coords = None
                        if box:
                            coords = (box['x'] + box['width']/2, box['y'] + box['height']/2)
                        
                        # Click the button
                        await button.click()
                        
                        # Wait a moment for any animations
                        await page.wait_for_timeout(1000)
                        
                        return CookieDetectionResult(
                            success=True,
                            method='dom',
                            element_text=text_content,
                            coordinates=coords,
                            log_details={
                                'selector': selector,
                                'matched_pattern': [p for p in self.cookie_keywords['accept_text_patterns'] if p in text_content][0]
                            }
                        )
            
            return CookieDetectionResult(
                success=False,
                method='dom',
                element_text='',
                coordinates=None,
                log_details={'container_checked': True, 'no_accept_buttons': True}
            )
            
        except Exception as e:
            return CookieDetectionResult(
                success=False,
                method='dom',
                element_text='',
                coordinates=None,
                log_details={'error': str(e)}
            )
    
    async def _direct_button_search(self, page) -> CookieDetectionResult:
        """Direct search for accept buttons across the entire page"""
        try:
            # Search for buttons with accept-related text anywhere on page
            for pattern in self.cookie_keywords['accept_text_patterns']:
                selectors = [
                    f"button:has-text('{pattern}')",
                    f"a:has-text('{pattern}')",
                    f"[role='button']:has-text('{pattern}')"
                ]
                
                for selector in selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button and await button.is_visible():
                            # Get coordinates and click
                            box = await button.bounding_box()
                            coords = None
                            if box:
                                coords = (box['x'] + box['width']/2, box['y'] + box['height']/2)
                            
                            text = await button.inner_text()
                            await button.click()
                            await page.wait_for_timeout(1000)
                            
                            return CookieDetectionResult(
                                success=True,
                                method='dom',
                                element_text=text.strip(),
                                coordinates=coords,
                                log_details={'direct_search': True, 'pattern': pattern}
                            )
                    except Exception:
                        continue
            
            return CookieDetectionResult(
                success=False,
                method='dom',
                element_text='',
                coordinates=None,
                log_details={'direct_search_failed': True}
            )
            
        except Exception as e:
            return CookieDetectionResult(
                success=False,
                method='dom',
                element_text='',
                coordinates=None,
                log_details={'error': str(e)}
            )
    
    async def _ocr_detection(self, page) -> CookieDetectionResult:
        """OCR-based detection for fallback"""
        if not OCR_AVAILABLE:
            return CookieDetectionResult(
                success=False,
                method='ocr',
                element_text='',
                coordinates=None,
                log_details={'error': 'OCR not available'}
            )
        
        try:
            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.debug_dir}/ocr_detection_{timestamp}.png"
            await page.screenshot(path=screenshot_path)
            
            # Load and process image
            image = Image.open(screenshot_path)
            width, height = image.size
            
            # Define priority regions
            regions = [
                ('bottom', (0, int(height * 0.75), width, height)),
                ('top', (0, 0, width, int(height * 0.25))),
                ('center', (0, int(height * 0.35), width, int(height * 0.65)))
            ]
            
            for region_name, (x1, y1, x2, y2) in regions:
                region_image = image.crop((x1, y1, x2, y2))
                
                # Run OCR
                ocr_data = pytesseract.image_to_data(region_image, output_type=pytesseract.Output.DICT)
                
                # Look for accept button text
                for i, text in enumerate(ocr_data['text']):
                    text_clean = text.strip().lower()
                    if text_clean and any(pattern in text_clean for pattern in self.cookie_keywords['accept_text_patterns']):
                        # Calculate click coordinates
                        rel_x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                        rel_y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                        abs_x = x1 + rel_x
                        abs_y = y1 + rel_y
                        
                        # Click at detected location
                        await page.mouse.click(abs_x, abs_y)
                        await page.wait_for_timeout(1000)
                        
                        return CookieDetectionResult(
                            success=True,
                            method='ocr',
                            element_text=text.strip(),
                            coordinates=(abs_x, abs_y),
                            log_details={
                                'region': region_name,
                                'confidence': ocr_data['conf'][i] if i < len(ocr_data['conf']) else 0
                            }
                        )
            
            return CookieDetectionResult(
                success=False,
                method='ocr',
                element_text='',
                coordinates=None,
                log_details={'regions_scanned': len(regions)}
            )
            
        except Exception as e:
            return CookieDetectionResult(
                success=False,
                method='ocr',
                element_text='',
                coordinates=None,
                log_details={'error': str(e)}
            )

# Integration function for existing navigation system
async def handle_page_interruptions_enhanced(page, debug_dir="debug_screenshots"):
    """
    Enhanced page interruption handler that replaces or supplements existing cookie handling.
    This function can be called from the existing navigation system.
    """
    detector = IntegratedCookieBannerDetector(debug_dir)
    result = await detector.detect_and_handle_cookie_banner(page)
    
    # Return format compatible with existing logging
    return {
        'success': result.success,
        'method': result.method,
        'element_text': result.element_text,
        'coordinates': result.coordinates,
        'details': result.log_details
    }

# Test integration function
async def test_integrated_cookie_detection():
    """Test function to verify integration works with existing system"""
    print("🧪 Testing integrated cookie banner detection...")
    
    # This would be called from your existing test framework
    # Example integration:
    """
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("https://www.bbc.com/news")
        
        # Call the integrated function
        result = await handle_page_interruptions_enhanced(page)
        
        print(f"Detection result: {result}")
        
        await browser.close()
    """
    
    print("✅ Integration test structure ready")
    print("   To test: Call handle_page_interruptions_enhanced(page) from your navigation system")

if __name__ == "__main__":
    asyncio.run(test_integrated_cookie_detection())