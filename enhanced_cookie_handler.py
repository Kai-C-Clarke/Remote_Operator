"""
Enhanced cookie banner detection and handling
Uses both visual and DOM-based detection strategies
"""

import asyncio
from playwright.async_api import Page

class EnhancedCookieHandler:
    def __init__(self, log_writer=None):
        self.log = log_writer
        
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
            
            if self.log:
                self.log.log_event(f"🔍 Found {len(banner_containers)} potential cookie containers via DOM analysis")
                for container in banner_containers[:3]:  # Log first 3
                    self.log.log_event(f"   Container: {container['tagName']} - {container['textContent'][:50]}...")
            
            return banner_containers
            
        except Exception as e:
            if self.log:
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
                        container = document.querySelector('.{containerInfo.className.split()[0]}');
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
                                selector: btn.id ? `#${{btn.id}}` : `.${{{btn.className.split(' ')[0]}}}`
                            }});
                        }}
                    }}
                    
                    return buttons;
                }}
            """, container_info)
            
            return buttons
            
        except Exception as e:
            if self.log:
                self.log.log_event(f"Button search failed: {str(e)}")
            return []

    async def handle_interruptions_enhanced(self, page: Page, max_attempts=3):
        """Enhanced interruption handling with DOM analysis"""
        if self.log:
            self.log.log_event("🚧 Enhanced interruption detection starting...")
        
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
                        if self.log:
                            self.log.log_event(f"🎯 Found cookie button: {selector}")
                        
                        await element.click(timeout=2000)
                        handled_count += 1
                        interruption_found = True
                        
                        if self.log:
                            self.log.log_event(f"✅ Successfully clicked cookie button")
                        
                        await page.wait_for_load_state('networkidle', timeout=3000)
                        break
                        
                except Exception:
                    continue
            
            # Strategy 2: DOM analysis (if predefined selectors failed)
            if not interruption_found:
                if self.log:
                    self.log.log_event("🔬 Trying DOM-based detection...")
                
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
                                    
                                    if self.log:
                                        self.log.log_event(f"✅ DOM-based click successful: {button['text']}")
                                    
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
                            
                            if self.log:
                                self.log.log_event(f"✅ Used dismiss button: {selector}")
                            
                            await page.wait_for_load_state('networkidle', timeout=3000)
                            break
                            
                    except Exception:
                        continue
            
            if not interruption_found:
                break
        
        if handled_count > 0:
            if self.log:
                self.log.log_event(f"🎯 Successfully handled {handled_count} interruption(s)")
        else:
            if self.log:
                self.log.log_event("✅ No interruptions detected or all handling failed")
        
        return handled_count

    async def take_debug_screenshot(self, page: Page, filename="cookie_debug.png"):
        """Take a screenshot for debugging cookie detection"""
        try:
            await page.screenshot(path=filename, full_page=True)
            if self.log:
                self.log.log_event(f"📸 Debug screenshot saved: {filename}")
        except Exception as e:
            if self.log:
                self.log.log_event(f"Screenshot failed: {str(e)}")
