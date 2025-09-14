from screen_manager import ScreenManager
from logger import Logger
from PIL import Image

def test_capture_and_ocr():
    logger = Logger()
    sm = ScreenManager(logger)
    # Use a blank image for OCR edge case test
    blank_img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    text = sm.extract_text(blank_img)
    assert text == ''
    logger.info("ScreenManager OCR edge case handled.")
    print("Screen Manager test complete.")

if __name__ == "__main__":
    test_capture_and_ocr()