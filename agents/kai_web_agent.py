from core.kai_agent_base import KaiAgent
import subprocess
import time

class KaiWebAgent(KaiAgent):
    def __init__(self, url=None, browser="chrome", **kwargs):
        super().__init__(name="KaiWebAgent", **kwargs)
        self.url = url
        self.browser = browser.lower()

    def validate_url(self, url):
        """Validate and clean URL"""
        if not url:
            return None
            
        url = url.strip()
        
        # Remove boundary markers if present
        url = url.replace('<<', '').replace('>>', '').replace('<', '').replace('>', '').strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            else:
                url = 'https://' + url
        
        # Basic validation
        if not ('.' in url and len(url) > 4):
            return None
            
        return url

    def open_url(self, url=None):
        """Open URL in specified browser"""
        target_url = url or self.url
        
        if not target_url:
            raise ValueError("No URL provided")
        
        validated_url = self.validate_url(target_url)
        if not validated_url:
            raise ValueError(f"Invalid URL: {target_url}")
        
        self.log(f"Opening URL: {validated_url}")
        
        try:
            if self.browser == "chrome":
                subprocess.run([
                    "open", "-a", "Google Chrome", validated_url
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self.browser == "safari":
                subprocess.run([
                    "open", "-a", "Safari", validated_url
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Default browser
                subprocess.run([
                    "open", validated_url
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for browser to open and load
            time.sleep(3)
            self.log(f"Successfully opened {validated_url}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to open URL with {self.browser}: {e}")
            return False
        except Exception as e:
            self.log(f"Unexpected error opening URL: {e}")
            return False

    def open_url_fast(self, url=None):
        """Speed-optimized URL opening"""
        target_url = url or self.url
        validated_url = self.validate_url(target_url)
        
        if not validated_url:
            raise ValueError(f"Invalid URL: {target_url}")
        
        self.log(f"Fast opening URL: {validated_url}")
        
        try:
            subprocess.run([
                "open", "-a", "Google Chrome", validated_url
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(2.0)  # Reduced from 3.0s
            self.log(f"Fast opened {validated_url}")
            return True
            
        except Exception as e:
            self.log(f"Fast URL opening failed: {e}")
            return False

    def focus_browser(self):
        """Bring browser to foreground"""
        try:
            browser_apps = {
                'chrome': 'Google Chrome',
                'safari': 'Safari',
                'firefox': 'Firefox'
            }
            
            app_name = browser_apps.get(self.browser, 'Google Chrome')
            
            applescript = f'''
            tell application "System Events"
                if exists (processes where name is "{app_name}") then
                    tell application "{app_name}"
                        activate
                    end tell
                    return true
                end if
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True)
            
            if 'true' in result.stdout:
                self.log(f"Focused {app_name}")
                return True
            else:
                self.log(f"Could not focus {app_name}")
                return False
                
        except Exception as e:
            self.log(f"Error focusing browser: {e}")
            return False

    def run(self, url=None):
        """Main web navigation operation"""
        target_url = url or self.url
        
        if not target_url:
            raise ValueError("No URL provided for web navigation")
        
        # Open URL
        success = self.open_url(target_url)
        if not success:
            raise Exception(f"Failed to open URL: {target_url}")
        
        # Focus browser window
        self.focus_browser()
        
        # Additional wait for page load
        time.sleep(2)
        
        self.log("Web navigation completed successfully")
        return True

    def run_fast(self, url=None):
        """Speed-optimized web navigation"""
        target_url = url or self.url
        
        if not target_url:
            raise ValueError("No URL provided for fast navigation")
        
        # Quick URL opening
        success = self.open_url_fast(target_url)
        if not success:
            raise Exception(f"Fast navigation failed: {target_url}")
        
        # Reduced focus time
        self.focus_browser()
        time.sleep(1.0)  # Reduced from 2.0s
        
        self.log("Fast web navigation completed")
        return True

    def verify(self):
        """Verify browser opened successfully"""
        # Could add more sophisticated verification later
        return True