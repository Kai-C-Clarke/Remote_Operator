from desktop_manager import DesktopManager
from logger import Logger

def test_switch_desktop_notify():
    logger = Logger()
    dm = DesktopManager(logger)
    dm.current_desktop = 0
    # Simulate failed switch to trigger notification
    result = dm.switch_desktop(99)  # unlikely valid desktop
    if not result:
        logger.notify("Desktop Switch Failure", "Manual intervention required.")
    print("Desktop Manager test complete.")

if __name__ == "__main__":
    test_switch_desktop_notify()