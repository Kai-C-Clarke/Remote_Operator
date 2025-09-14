# test_desktop_switch.py
import time
from agents.kai_desktop_agent import KaiDesktopAgent

def main():
    print("=== Desktop Switch Test ===")

    # Step 1: Switch to Claude (Desktop 1)
    print("\n➡️ Switching to Claude (Desktop 1)...")
    agent1 = KaiDesktopAgent(direction="right", presses=1)
    agent1.run()
    time.sleep(2)

    # Step 2: Switch to Browser (Desktop 2)
    print("\n➡️ Switching to Browser (Desktop 2)...")
    agent2 = KaiDesktopAgent(direction="right", presses=1)
    agent2.run()
    time.sleep(2)

    # Step 3: Switch back to Claude (Desktop 1)
    print("\n➡️ Switching back to Claude (Desktop 1)...")
    agent3 = KaiDesktopAgent(direction="left", presses=1)
    agent3.run()
    time.sleep(2)

    print("\n✅ Desktop switch test complete.")

if __name__ == "__main__":
    main()
