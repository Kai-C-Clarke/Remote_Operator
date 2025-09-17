"""
daylong_researcher_v2.py
Refactored wanderer: follows articles inside a site, supports navigation commands
"""

import time
import subprocess
import pyautogui
import asyncio
from playwright.async_api import async_playwright

from agents.kai_claude_region_agent import KaiClaudeRegionAgent
from agents.kai_boundary_agent import KaiBoundaryAgent
from agents.kai_web_agent import KaiWebAgent
from agents.kai_desktop_agent import KaiDesktopAgent
from agents.kai_clipboard_agent import KaiClipboardAgent
from research_logger import ResearchLogger


class DaylongResearcher:
    def __init__(self):
        self.logger = ResearchLogger()
        self.cycle_count = 0
        self.current_url = None
        self.home_url = None

    def capture_claude_command(self):
        """OCR Claude’s output and parse article/command"""
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
            return {"type": "nextsite", "url": stable_text.split(":", 1)[1].strip()}
        elif cmd in ("home", "back"):
            return {"type": "command", "action": cmd}
        else:
            # fallback: raw URL
            boundary_agent = KaiBoundaryAgent()
            url_result = boundary_agent.run(stable_text)
            if url_result["success"] and url_result["urls"]:
                return {"type": "nextsite", "url": url_result["urls"][0]}
            return None

    async def open_url(self, url):
        """Open a fresh site in the browser"""
        self.current_url = url
        if not self.home_url:
            self.home_url = url

        KaiDesktopAgent(direction="right", presses=2).run_fast()
        time.sleep(0.7)

        KaiWebAgent(url=url).run_fast()
        time.sleep(2.0)

        subprocess.run(["screencapture", "-c"], check=True, timeout=8)
        print(f"📸 Opened {url} and captured homepage")

        # Return to Claude
        KaiDesktopAgent(direction="left", presses=1).run_fast()
        time.sleep(1.0)

    async def click_article(self, query):
        """Find and click an article by partial text match"""
        KaiDesktopAgent(direction="right", presses=2).run_fast()
        time.sleep(0.7)

        success = False
        chosen_link = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://" + self.current_url)

            anchors = await page.query_selector_all("a")
            for a in anchors:
                try:
                    text = (await a.inner_text()).strip()
                    href = await a.get_attribute("href")
                    if query.lower() in text.lower():
                        await a.click()
                        await page.wait_for_load_state("networkidle")
                        time.sleep(2)
                        subprocess.run(["screencapture", "-c"], check=True, timeout=8)
                        print(f"📸 Clicked article: {text}")
                        success = True
                        chosen_link = href
                        break
                except:
                    continue
            await browser.close()

        KaiDesktopAgent(direction="left", presses=1).run_fast()
        time.sleep(1.0)

        return success, chosen_link

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
            success, chosen_link = await self.click_article(command["query"])
            reflection = f"Clicked article matching '{command['query']}'" if success else f"Failed to find article: {command['query']}"
        elif command["type"] == "command":
            if command["action"] == "home" and self.home_url:
                await self.open_url(self.home_url)
                reflection = f"Returned home: {self.home_url}"
            elif command["action"] == "back":
                reflection = "Back command received (not implemented)"
            else:
                reflection = f"Unknown command: {command['action']}"
        else:
            reflection = f"Unhandled command: {command}"

        # Send screenshot + follow-up
        try:
            claude_input_x, claude_input_y = 1845, 1280
            pyautogui.click(claude_input_x, claude_input_y)
            time.sleep(0.3)
            pyautogui.hotkey("command", "a")
            time.sleep(0.2)
            pyautogui.hotkey("command", "v")
            time.sleep(1.2)
            pyautogui.press("enter")
            time.sleep(0.5)

            follow_up = "What article or site should we visit next?"
            pyautogui.typewrite(follow_up, interval=0.008)
            time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(0.5)

            print("Follow-up sent to Claude.")
        except Exception as e:
            print(f"Error sending screenshot: {e}")

        # Log
        self.logger.log(
            url=self.current_url or "N/A",
            chosen_link=command.get("query") or command.get("url"),
            reflection=reflection
        )

        return True


async def main():
    print("=== Daylong Researcher v2 ===")

    KaiDesktopAgent(direction="right", presses=1).run_fast()
    time.sleep(1.0)

    researcher = DaylongResearcher()

    # Seed homepage: BBC News
    await researcher.open_url("bbc.co.uk/news")

    while True:
        await researcher.run_cycle()
        time.sleep(1.5)


if __name__ == "__main__":
    asyncio.run(main())
