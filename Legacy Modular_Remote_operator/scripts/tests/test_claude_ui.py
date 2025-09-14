from claude_ui import ClaudeUI
from logger import Logger

def test_focus_and_type_fail():
    logger = Logger()
    cu = ClaudeUI(logger)
    # Simulate by moving the window off screen or using invalid coords
    cu.find_input_box = lambda: (9999, 9999)  # patch to fail
    try:
        cu.focus_and_type("Test message")
    except Exception as e:
        logger.notify("Claude UI Focus Failure", "Manual intervention required.")
    print("Claude UI test complete.")

if __name__ == "__main__":
    test_focus_and_type_fail()