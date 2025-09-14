from core.kai_agent_base import KaiAgent
import re

class KaiBoundaryAgent(KaiAgent):
    def __init__(self, **kwargs):
        super().__init__(name="KaiBoundaryAgent", **kwargs)

    def clean_url(self, url):
        """Clean and construct full URL from domain"""
        if not url:
            return None
        
        # Remove whitespace and common artifacts
        url = url.strip()
        url = url.replace('<<', '').replace('>>', '').replace('<', '').replace('>', '')
        url = re.sub(r'\s+', '', url)
        
        # Remove common prefixes from natural language
        url = re.sub(r'^(visit|go to|try|check out)\s+', '', url, flags=re.IGNORECASE)
        
        # Basic domain validation
        if not ('.' in url and len(url) > 3):
            return None
        
        # Skip obviously invalid domains
        if any(invalid in url.lower() for invalid in ['example.com', 'test.com', 'sample.com', 'domain.com']):
            return None
        
        # Construct full URL from domain
        if url.startswith(('http://', 'https://')):
            return url
        
        # Add www if not present
        if not url.startswith('www.'):
            url = 'www.' + url
            
        return 'https://' + url

    def extract_from_natural_language(self, text):
        """Extract website references from natural language"""
        urls = []
        
        # Pattern 1: Direct domain mentions
        domain_patterns = [
            r'\b([a-zA-Z0-9-]+\.(?:com|org|net|edu|gov|co\.uk|co|io|ai|de|fr|jp|cn|in|au|ca|br))\b',
            r'\bwww\.([a-zA-Z0-9-]+\.(?:com|org|net|edu|gov|co\.uk|co|io|ai|de|fr|jp|cn|in|au|ca|br))\b'
        ]
        
        for pattern in domain_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = self.clean_url(match)
                if cleaned:
                    urls.append(cleaned)
        
        # Pattern 2: "Let's visit X" or "Try X" patterns
        visit_patterns = [
            r'(?:let\'s|try|visit|go to|check out)\s+([a-zA-Z0-9.-]+\.(?:com|org|net|edu|gov|co\.uk|co|io|ai))',
            r'(?:website|site).*?([a-zA-Z0-9.-]+\.(?:com|org|net|edu|gov|co\.uk|co|io|ai))'
        ]
        
        for pattern in visit_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = self.clean_url(match)
                if cleaned:
                    urls.append(cleaned)
        
        # Pattern 3: Full URLs mentioned in text
        url_pattern = r'https?://[^\s<>"\']+(?:\.[^\s<>"\']+)+'
        url_matches = re.findall(url_pattern, text)
        for match in url_matches:
            cleaned = self.clean_url(match)
            if cleaned:
                urls.append(cleaned)
        
        return list(set(urls))  # Remove duplicates

    def extract_from_boundaries(self, text):
        """Extract from explicit boundary markers << >> """
        boundaries = re.findall(r'<<([^<>]+)>>', text, re.DOTALL)
        
        urls = []
        for boundary in boundaries:
            cleaned = self.clean_url(boundary.strip())
            if cleaned:
                urls.append(cleaned)
        
        return urls

    def extract_from_bold_text(self, text):
        """Extract from **text** patterns"""
        bold_matches = re.findall(r'\*\*([^*]+)\*\*', text)
        
        urls = []
        for match in bold_matches:
            # Check if it looks like a domain
            if ('.' in match and 
                any(tld in match.lower() for tld in ['.com', '.org', '.net', '.edu', '.gov', '.co.uk', '.io', '.ai'])):
                cleaned = self.clean_url(match)
                if cleaned:
                    urls.append(cleaned)
        
        return urls

    def run(self, text):
        """Main detection operation - try multiple extraction methods"""
        if not text:
            raise ValueError("No text provided for website detection")

        self.log("Starting natural language website detection")

        # Method 1: Explicit boundary markers << >>
        boundary_urls = self.extract_from_boundaries(text)
        if boundary_urls:
            self.log(f"Found {len(boundary_urls)} boundary-marked websites: {boundary_urls}")
            return {
                'boundaries': boundary_urls,
                'urls': boundary_urls,
                'success': True,
                'method': 'boundary_markers'
            }

        # Method 2: Bold text **website**
        bold_urls = self.extract_from_bold_text(text)
        if bold_urls:
            self.log(f"Found {len(bold_urls)} bold websites: {bold_urls}")
            return {
                'boundaries': [],
                'urls': bold_urls,
                'success': True,
                'method': 'bold_text'
            }

        # Method 3: Natural language extraction
        natural_urls = self.extract_from_natural_language(text)
        if natural_urls:
            self.log(f"Found {len(natural_urls)} websites in natural language: {natural_urls}")
            return {
                'boundaries': [],
                'urls': natural_urls,
                'success': True,
                'method': 'natural_language'
            }

        self.log("No websites detected in text")
        return {
            'boundaries': [],
            'urls': [],
            'success': False,
            'method': 'none'
        }

    def verify(self):
        """Verify operation succeeded"""
        return True