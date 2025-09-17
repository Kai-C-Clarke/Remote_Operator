"""
hybrid_navigator_v2.py
Stable integrated navigator skeleton + OCR article clicker (fixed)
"""

import time
import subprocess
import pyautogui
import asyncio
import cv2
import pytesseract
from playwright.async_api import async_playwright

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_desktop_agent import KaiDesktopAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from research_logger import ResearchLogger


class HybridNavigatorV2:
    def __init__(self, page):
        self.logger = ResearchLogger()
        self.cycle_count = 0
        self.current_url = None
        self.home_url = None
        self.page = page  # Reused Playwright page
        self.claude_input_x = 1845
        self.claude_input_y = 1280

    def capture_claude_command(self):
        """OCR Claude’s output and parse into command dict"""
        claude_agent = KaiClaudeRegionAgent()
        stable_text = claude_agent.wait_for_response_completion_fast()
        if not stable_text:
            print("⚠️ No text captured from Claude region.")
            return None

        print(f"Captured text ({len(stable_text)} chars): {stable_text}")
        cmd = stable_text.strip().lower()

        if cmd.startswith("article:"):
            return {"type": "article", "query": stable_text.split(":", 1)[1].strip()}
        elif cmd.startswith("nextsite:"):
            return {"type": "nextsite", "url": cmd.split(":", 1)[1].strip()}
        elif cmd in ("home", "back"):
            return {"type": "command", "action": cmd}
        else:
            boundary_agent = KaiBoundaryAgent()
            url_result = boundary_agent.run(stable_text)
            if url_result["success"] and url_result["urls"]:
                return {"type": "nextsite", "url": url_result["urls"][0]}
            return None

    async def open_url(self, url):
        """Open a site in the reused Playwright browser"""
        self.current_url = url
        if not self.home_url:
            self.home_url = url

        # Switch → browser desktop2
        KaiDesktopAgent(direction="right", presses=2).run_fast()
        time.sleep(0.7)

        await self.page.goto("https://" + url)
        await self.page.wait_for_selector("body")
        time.sleep(2)

        subprocess.run(["screencapture", "-c"], check=True, timeout=8)
        print(f"📸 Opened {url} and captured homepage")

        # Switch → Claude desktop1
        KaiDesktopAgent(direction="left", presses=1).run_fast()
        time.sleep(1.0)

    async def click_article_ocr(self, query):
        """Use OCR to find and click an article by keyword"""
        # Switch → browser desktop2
        KaiDesktopAgent(direction="right", presses=2).run_fast()
        time.sleep(0.7)

        success = False
        chosen_text = None

        # Screenshot page for OCR
        await self.page.screenshot(path="logs/debug_screenshots/page_for_ocr.png", full_page=True)
        img = cv2.imread("logs/debug_screenshots/page_for_ocr.png")

        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for i, word in enumerate(data["text"]):
            if query.lower() in word.lower():
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                pyautogui.click(x + w // 2, y + h // 2)
                time.sleep(2)
                subprocess.run(["screencapture", "-c"], check=True, timeout=8)
                print(f"📸 OCR clicked article: {word}")
                success = True
                chosen_text = word
                break

        # Switch → Claude desktop1
        KaiDesktopAgent(direction="left", presses=1).run_fast()
        time.sleep(1.0)

        return success, chosen_text

    def send_screenshot_and_followup(self, follow_up_text):
        """Paste screenshot + follow-up to Claude"""
        try:
            pyautogui.click(self.claude_input_x, self.claude_input_y)
            time.sleep(0.3)

            pyautogui.hotkey("command", "v")
            time.sleep(1.5)
            pyautogui.press("enter")
            time.sleep(0.5)

            KaiClipboardAgent(message=follow_up_text).run_fast()
            time.sleep(0.25)
            pyautogui.press("enter")
            time.sleep(0.5)

            print("Screenshot + follow-up sent to Claude.")
        except Exception as e:
            print(f"Error sending screenshot: {e}")

    async def run_cycle(self):
        self.cycle_count += 1
        print(f"\n=== Cycle {self.cycle_count} ===")

        command = self.capture_claude_command()
        if not command:
            print("⚠️ No command, skipping")
            return False

        if command["type"] == "nextsite":
            await self.open_url(command["url"])
            reflection = f"Opened new site: {command['url']}"
        elif command["type"] == "article":
            success, chosen_text = await self.click_article_ocr(command["query"])
            reflection = f"Clicked article matching '{command['query']}'" if success else f"Failed to find article: {command['query']}"
        elif command["type"] == "command":
            if command["action"] == "home" and self.home_url:
                await self.open_url(self.home_url)
                reflection = f"Returned home: {self.home_url}"
            elif command["action"] == "back":
                reflection = "Back command (not implemented)"
            else:
                reflection = f"Unknown command: {command['action']}"
        else:
            reflection = f"Unhandled command: {command}"

        self.send_screenshot_and_followup("What article or site should we visit next?")

        self.logger.log(
            url=self.current_url or "N/A",
            chosen_link=command.get("query") or command.get("url"),
            reflection=reflection,
        )
        return True


async def main():
    print("=== Hybrid Navigator v2 ===")

    KaiDesktopAgent(direction="right", presses=1).run_fast()
    time.sleep(1.0)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        researcher = HybridNavigatorV2(page)

        # Seed homepage
        await researcher.open_url("bbc.co.uk/news")

        while True:
            await researcher.run_cycle()
            time.sleep(1.5)


if __name__ == "__main__":
    asyncio.run(main())
