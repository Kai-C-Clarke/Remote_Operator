import re
from logger import Logger

class BoundaryDetector:
    def __init__(self, logger=None):
        self.logger = logger or Logger()
        self.pattern = r'<<(.*?)>>'

    def extract_boundaries(self, text):
        boundaries = re.findall(self.pattern, text, re.DOTALL)
        self.logger.info(f"Extracted boundaries: {boundaries}")
        return boundaries