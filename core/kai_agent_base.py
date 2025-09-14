from abc import ABC, abstractmethod
import time
import traceback
import logging
from logging.handlers import RotatingFileHandler
import os

# Configure global logger once
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "operator.log")

logger = logging.getLogger("KaiOperator")
logger.setLevel(logging.INFO)

# File handler (rotating, 1MB, keep 5 backups)
file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

# Avoid duplicate handlers on reload
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

class KaiAgent(ABC):
    def __init__(self, name=None, max_retries=2, retry_delay=1):
        self.name = name or self.__class__.__name__
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger  # default to global logger

    def attach_logger(self, custom_logger):
        """Optionally attach a custom logger."""
        self.logger = custom_logger

    def log(self, message, level=logging.INFO):
        if self.logger:
            self.logger.log(level, f"[{self.name}] {message}")
        else:
            print(f"[{self.name}] {message}")

    def run_with_retry(self, *args, **kwargs):
        attempts = 0
        while attempts <= self.max_retries:
            try:
                self.log(f"Attempt {attempts + 1}...")
                result = self.run(*args, **kwargs)
                self.log("Success.")
                return result
            except Exception as e:
                self.log(f"Error: {e}\n{traceback.format_exc()}", level=logging.ERROR)
                attempts += 1
                if attempts > self.max_retries:
                    self.log("Max retries exceeded. Failing.", level=logging.CRITICAL)
                    raise
                self.log(f"Retrying in {self.retry_delay} seconds...", level=logging.WARNING)
                time.sleep(self.retry_delay)

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
