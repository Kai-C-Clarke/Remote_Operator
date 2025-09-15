from clipboard_manager import ClipboardManager
from logger import Logger

def test_clipboard_retry_fallback():
    logger = Logger()
    cm = ClipboardManager(logger)
    fake_image = "not_a_real_image.png"
    for attempt in range(3):
        success = cm.copy_image_to_clipboard(fake_image)
        if success and cm.verify_clipboard_has_image():
            print("Clipboard success.")
            break
        else:
            logger.warning("Clipboard failed, retrying...")
    else:
        logger.notify("Clipboard Failure", "Manual upload fallback required.")
    print("Clipboard Manager test complete.")

if __name__ == "__main__":
    test_clipboard_retry_fallback()