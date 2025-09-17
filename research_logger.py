"""
research_logger.py
Keeps a daily log of the daylong researcher’s activity.
"""

import time
import json
from pathlib import Path

class ResearchLogger:
    def __init__(self, log_file=None):
        base_dir = Path("logs/research")
        base_dir.mkdir(parents=True, exist_ok=True)

        # Default: one file per day
        if log_file is None:
            today = time.strftime("%Y-%m-%d")
            log_file = base_dir / f"{today}.json"

        self.log_file = Path(log_file)
        self.entries = self._load_existing()

    def _load_existing(self):
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def log(self, url, chosen_link=None, reflection=None, screenshot_path=None):
        """Append a new log entry for this cycle."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "chosen_link": chosen_link,
            "reflection": reflection,
            "screenshot": screenshot_path
        }
        self.entries.append(entry)
        self._save()
        print(f"📝 Logged research entry: {url} -> {chosen_link}")

    def _save(self):
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.entries, f, indent=2)
        except Exception as e:
            print(f"Failed to save research log: {e}")

    def summarize_day(self):
        """Produce a readable summary of today’s log."""
        summary_lines = []
        for entry in self.entries:
            line = f"[{entry['timestamp']}] Visited {entry['url']}"
            if entry.get("chosen_link"):
                line += f" → chose {entry['chosen_link']}"
            if entry.get("reflection"):
                line += f"\n   Reflection: {entry['reflection']}"
            summary_lines.append(line)
        return "\n".join(summary_lines)
