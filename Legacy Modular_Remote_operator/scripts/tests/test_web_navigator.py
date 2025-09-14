from web_navigator import WebNavigator
from logger import Logger

def test_open_url_fallback():
    logger = Logger()
    wn = WebNavigator(logger)
    success = wn.open_url("https://notarealwebsite.fake")
    if not success:
        logger.notify("Browser Open Failure", "Manual browser open required.")
    print("Web Navigator test complete.")

if __name__ == "__main__":
    test_open_url_fallback()