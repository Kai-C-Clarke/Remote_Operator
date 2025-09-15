from core.kai_agent_base import KaiAgent
import re

class KaiBoundaryAgent(KaiAgent):
    def __init__(self, pattern=None, **kwargs):
        super().__init__(name="KaiBoundaryAgent", **kwargs)
        # Support both << >> and <  > patterns
        self.pattern = pattern or r'<<\s*(.*?)\s*>>'
        self.alternative_pattern = r'<\s*(.*?)\s*>'
        self.boundaries = []

    def extract_boundaries(self, text):
        """Extract content from boundary markers"""
        if not text:
            self.log("No text provided for boundary extraction")
            return []

        # Try primary pattern first (<<  >>)
        boundaries = re.findall(self.pattern, text, re.DOTALL)
        
        if not boundaries:
            # Try alternative pattern (<  >)
            self.log("No << >> boundaries found, trying <  > pattern")
            boundaries = re.findall(self.alternative_pattern, text, re.DOTALL)

        # Clean up extracted boundaries
        cleaned_boundaries = []
        for boundary in boundaries:
            cleaned = boundary.strip()
            if cleaned:
                cleaned_boundaries.append(cleaned)

        self.boundaries = cleaned_boundaries
        
        if cleaned_boundaries:
            self.log(f"Found {len(cleaned_boundaries)} boundaries: {cleaned_boundaries}")
        else:
            self.log("No boundaries found in text")
            
        return cleaned_boundaries

    def clean_url(self, url: str) -> str:
        """Correct common OCR mistakes in URLs"""
        original_url = url
        url = url.strip()

        # Remove stray characters
        url = url.replace(" ", "").replace("\n", "")
        url = url.replace("↗", "").replace("→", "")
        url = url.replace("“", "").replace("”", "")
        url = url.replace("**", "").replace("```", "").replace("markdown", "")

        # Fix common protocol errors
        if url.startswith("https://ww."):
            url = url.replace("https://ww.", "https://www.", 1)
        if url.startswith("https//"):
            url = url.replace("https//", "https://", 1)
        if url.startswith("http//"):
            url = url.replace("http//", "http://", 1)
        if url.startswith("http:/") and not url.startswith("http://"):
            url = url.replace("http:/", "http://")
        if url.startswith("https:/") and not url.startswith("https://"):
            url = url.replace("https:/", "https://")

        # Drop obvious junk
        if url.endswith((".py", ".md", ".txt")):
            return ""

        # Ensure protocol
        if url.startswith("www."):
            url = "https://" + url
        if not url.startswith(("http://", "https://")) and "." in url:
            url = "https://" + url

        # Log raw vs cleaned
        if original_url != url:
            self.log(f"Raw URL from OCR: {original_url}")
            self.log(f"Cleaned URL: {url}")

        return url

    def extract_urls(self, boundaries=None):
        """Extract URLs from boundary contents"""
        if boundaries is None:
            boundaries = self.boundaries

        urls = []
        url_patterns = [
            r'https?://[^\s\]\)\"\'\,\<\>]+',  # Full URLs
            r'www\.[^\s\]\)\"\'\,\<\>]+',      # www domains
            r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s\]\)\"\'\,\<\>]*'  # Domain patterns
        ]

        for boundary in boundaries:
            self.log(f"Extracting URLs from: {boundary}")

            # --- NEW CLEANUP STEP ---
            cleaned_boundary = boundary
            cleaned_boundary = cleaned_boundary.replace("```", "")
            cleaned_boundary = cleaned_boundary.replace("markdown", "")
            cleaned_boundary = cleaned_boundary.replace("**", "")
            cleaned_boundary = re.sub(r'^[\{\(\[\"\|]+', '', cleaned_boundary)
            cleaned_boundary = re.sub(r'[\}\)\]\"\|]+$', '', cleaned_boundary)

            # Pattern search
            for pattern in url_patterns:
                matches = re.findall(pattern, cleaned_boundary, re.IGNORECASE)
                
                for match in matches:
                    url = match.strip()
                    
                    # Remove trailing punctuation
                    while url and url[-1] in '.,;:!?)]}"\'>>':
                        url = url[:-1]
                    
                    # Clean and normalize URL
                    cleaned = self.clean_url(url)
                    if cleaned:
                        urls.append(cleaned)
                        self.log(f"Extracted URL (final): {cleaned}")

        if not urls and boundaries:
            # If no URL patterns found, treat the boundary content as a potential URL
            for boundary in boundaries:
                candidate = boundary.strip()
                candidate = candidate.replace("```", "").replace("markdown", "").replace("**", "")
                candidate = re.sub(r'^[\{\(\[\"\|]+', '', candidate)
                candidate = re.sub(r'[\}\)\]\"\|]+$', '', candidate)

                if '.' in candidate and ' ' not in candidate:
                    cleaned = self.clean_url(candidate)
                    if cleaned:
                        urls.append(cleaned)
                        self.log(f"Treating boundary as URL: {cleaned}")

        return urls

    def run(self, text):
        """Main boundary detection operation"""
        if not text:
            raise ValueError("No text provided for boundary detection")

        self.log("Starting boundary detection")
        boundaries = self.extract_boundaries(text)
        
        if boundaries:
            urls = self.extract_urls(boundaries)
            self.log(f"Boundary detection complete: {len(boundaries)} boundaries, {len(urls)} URLs")
            return {
                'boundaries': boundaries,
                'urls': urls,
                'success': True
            }
        else:
            self.log("No boundaries detected")
            return {
                'boundaries': [],
                'urls': [],
                'success': False
            }

    def get_boundaries(self):
        """Get the last extracted boundaries"""
        return self.boundaries

    def verify(self):
        """Verify boundary detection succeeded"""
        return len(self.boundaries) > 0
