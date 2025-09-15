# Configuration for AI Remote Operator

# File paths
SCREENSHOT_PATH = "debug_screenshots/"
LOG_FILE = "webpage_operator.log"

# Prompt text
PROMPT_TEXT = "Ready for your next webpage operation command! Use <<URL>> format."

# OCR settings
OCR_CONFIG = r'--psm 6 --oem 3'

# Retry and timing settings
RETRY_ATTEMPTS = 3
CYCLE_DELAY = 5  # seconds between cycles
CLAUDE_RESPONSE_WAIT = 8  # seconds to wait for Claude to respond
PAGE_LOAD_WAIT = 4  # seconds to wait for page to load

# Desktop assignments
DESKTOP_CLAUDE = 1
DESKTOP_BROWSER = 2

# Health monitoring
MIN_SUCCESS_RATE = 60  # percentage
MAX_CONSECUTIVE_FAILURES = 3