from core.kai_agent_base import KaiAgent
from agents.kai_ocr_agent import KaiOCRAgent
import time

class KaiClaudeRegionAgent(KaiAgent):
    def __init__(self, **kwargs):
        super().__init__(name="KaiClaudeRegionAgent", **kwargs)
        # Use your exact measured Claude's read area coordinates
        # Claude's Read area: (1552, 198) to (2324, 1113)
        claude_x = 1552
        claude_y = 198
        claude_width = 2324 - 1552  # 772
        claude_height = 1113 - 198  # 915
        
        self.claude_region = (claude_x, claude_y, claude_width, claude_height)
        self.ocr_agent = None
        
    def initialize_ocr(self):
        """Initialize OCR agent with Claude's specific region"""
        self.ocr_agent = KaiOCRAgent(region=self.claude_region, save_debug=True)
        self.ocr_agent.attach_logger(self.logger)
        
    def wait_for_claude_response_stability(self, timeout=60, stability_checks=3):
        """Wait for Claude's response to stabilize in the specific region"""
        if not self.ocr_agent:
            self.initialize_ocr()
            
        self.log("Waiting for Claude response to stabilize in specific region...")
        
        last_text = ""
        stable_count = 0
        check_interval = 2
        
        while stable_count < stability_checks and timeout > 0:
            # Capture from Claude's specific region only
            current_text = self.ocr_agent.capture_and_extract()
            
            if current_text == last_text:
                stable_count += 1
                self.log(f"Claude region content stable (count: {stable_count}/{stability_checks})")
            else:
                stable_count = 0
                self.log("Claude region content still changing...")
            
            last_text = current_text
            time.sleep(check_interval)
            timeout -= check_interval
        
        if stable_count >= stability_checks:
            self.log("Claude region content has stabilized")
            return last_text
        else:
            self.log("Timeout waiting for Claude region stability")
            return last_text

    def capture_claude_area(self):
        """Capture just Claude's response area"""
        if not self.ocr_agent:
            self.initialize_ocr()
            
        return self.ocr_agent.capture_and_extract()

    def run(self, wait_for_stability=True):
        """Main operation - capture Claude's region with optional stability check"""
        if wait_for_stability:
            text = self.wait_for_claude_response_stability()
        else:
            text = self.capture_claude_area()
        
        self.log(f"Claude region OCR completed. Text length: {len(text)}")
        
        if text:
            # Log preview for debugging
            preview = text.replace('\n', ' ')[:100]
            self.log(f"Claude region text preview: {preview}...")
        
        return text

    def verify(self):
        """Verify operation succeeded"""
        return True