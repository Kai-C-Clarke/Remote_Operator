from boundary_detector import BoundaryDetector
from logger import Logger

def test_boundary_extraction():
    logger = Logger()
    bd = BoundaryDetector(logger)
    # Simulate malformed OCR output
    text = "Go to <<https:/example.com>> and see <<foo bar>>"
    boundaries = bd.extract_boundaries(text)
    assert boundaries == ['https:/example.com', 'foo bar']
    print("Boundary Detector test complete.")

if __name__ == "__main__":
    test_boundary_extraction()