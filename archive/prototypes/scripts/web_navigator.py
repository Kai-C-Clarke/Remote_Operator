import subprocess
import time
import pyautogui
from logger import Logger

class WebNavigator:
    def __init__(self, logger=None):
        self.logger = logger or Logger()

    def open_url(self, url):
        """Open URL in default browser and focus it"""
        try:
            # Open URL using macOS 'open' command
            result = subprocess.run(['open', url], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to open URL: {result.stderr}")
                return False
            
            # Wait for browser to open
            time.sleep(2)
            
            # Focus browser window (bring to front)
            self._focus_browser()
            
            self.logger.info(f"Successfully opened URL: {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening URL {url}: {e}")
            return False
    
    def _focus_browser(self):
        """Focus the browser window using AppleScript"""
        try:
            # Try to focus Safari first, then Chrome
            browsers = ['Safari', 'Google Chrome', 'Firefox']
            
            for browser in browsers:
                applescript = f'''
                tell application "System Events"
                    if exists (processes where name is "{browser}") then
                        tell application "{browser}"
                            activate
                        end tell
                        return true
                    end if
                end tell
                '''
                
                result = subprocess.run(['osascript', '-e', applescript], 
                                      capture_output=True, text=True)
                
                if 'true' in result.stdout:
                    self.logger.info(f"Focused {browser}")
                    return True
            
            self.logger.warning("Could not focus any browser")
            return False
            
        except Exception as e:
            self.logger.error(f"Error focusing browser: {e}")
            return False

    def refresh_page(self):
        """Refresh the current page"""
        try:
            pyautogui.hotkey('cmd', 'r')
            self.logger.info("Page refreshed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to refresh page: {e}")
            return False

    def go_back(self):
        """Navigate back in browser history"""
        try:
            pyautogui.hotkey('cmd', 'left')
            self.logger.info("Navigated back")
            return True
        except Exception as e:
            self.logger.error(f"Failed to go back: {e}")
            return False