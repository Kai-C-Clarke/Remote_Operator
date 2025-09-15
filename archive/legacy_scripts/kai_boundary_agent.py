def run(self, text):
    """Main detection operation - prefer marked URLs first, then bold, plain, then boundaries"""
    if not text:
        raise ValueError("No text provided for URL detection")

    self.log("Starting URL detection")

    # 🔑 Step 1: Prefer URLs inside << >>
    marker_urls = re.findall(r'<<\s*(https?://[^\s<>]+)\s*>>', text)
    if marker_urls:
        cleaned = [self.clean_url(u) for u in marker_urls if self.clean_url(u)]
        if cleaned:
            self.log(f"Found {len(cleaned)} marked URLs: {cleaned}")
            return {
                'boundaries': [],
                'urls': cleaned,
                'success': True,
                'method': 'marked_urls'
            }

    # Step 2: Try bold URLs
    bold_urls = self.extract_bold_urls(text)
    if bold_urls:
        self.log(f"Found {len(bold_urls)} bold URLs")
        return {
            'boundaries': [],
            'urls': bold_urls,
            'success': True,
            'method': 'bold_urls'
        }

    # Step 3: Try plain URLs
    plain_urls = self.extract_plain_urls(text)
    if plain_urls:
        self.log(f"Found {len(plain_urls)} plain URLs")
        return {
            'boundaries': [],
            'urls': plain_urls,
            'success': True,
            'method': 'plain_urls'
        }

    # Step 4: Fallback to boundary markers
    boundaries = self.extract_boundaries(text)
    if boundaries:
        urls = self.extract_urls(boundaries)
        self.log(f"URL detection complete: {len(boundaries)} boundaries, {len(urls)} URLs")
        return {
            'boundaries': boundaries,
            'urls': urls,
            'success': True,
            'method': 'boundaries'
        }

    self.log("No URLs or boundaries detected")
    return {
        'boundaries': [],
        'urls': [],
        'success': False,
        'method': 'none'
    }
