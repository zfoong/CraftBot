from agent_core import action

@action(
    name="web_fetch",
    description=(
        "Fetches content from a URL and returns it as cleaned text/markdown. "
        "Use web_search first to find URLs, then web_fetch to read them. "
        "The 'prompt' parameter controls what is returned: "
        "include 'title' to extract just the page title, "
        "include 'summary' to get a short preview (~900 chars), "
        "or describe what you need (e.g., 'find the pricing table') to get a focused preview. "
        "Content beyond max_content_length is saved to a temp file (returned as content_file) "
        "— use grep_files or read_file on that path to access the rest. "
        "HTTP is auto-upgraded to HTTPS (except localhost). Follows up to 10 redirects automatically."
    ),
    mode="CLI",
    action_sets=["core"],
    input_schema={
        "url": {
            "type": "string",
            "example": "https://example.com/article",
            "description": "The URL to fetch content from. Must be a valid http(s) URL.",
            "required": True
        },
        "prompt": {
            "type": "string",
            "example": "Extract the main pricing information",
            "description": "Describes what information to extract. Use 'title' to get just the page title. Use 'summary' for a short content preview (~900 chars). Otherwise, provide a specific prompt (e.g., 'find the API rate limits') and the response will include a content preview with your prompt for context. Always provide a prompt to keep responses token-efficient."
        },
        "timeout": {
            "type": "number",
            "example": 20,
            "description": "Request timeout in seconds. Defaults to 20."
        },
        "max_content_length": {
            "type": "integer",
            "example": 5000,
            "description": "Maximum content length in characters returned inline. Content beyond this is saved to content_file for access via read_file/grep_files. Defaults to 5000. Pass 0 to return all content inline (use sparingly — large pages waste tokens)."
        },
        "use_jina_fallback": {
            "type": "boolean",
            "example": True,
            "description": "Use Jina Reader API as fallback for JS-rendered sites when static extraction yields too little content. Defaults to True."
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success",
            "description": "'success' or 'error'."
        },
        "status_code": {
            "type": "integer",
            "example": 200,
            "description": "HTTP status code (e.g., 200, 404, 500)."
        },
        "status_text": {
            "type": "string",
            "example": "OK",
            "description": "HTTP status reason (e.g., 'OK', 'Not Found')."
        },
        "url": {
            "type": "string",
            "description": "The final URL after following redirects."
        },
        "title": {
            "type": "string",
            "description": "The page title, if extracted."
        },
        "content": {
            "type": "string",
            "description": "The extracted content. Format depends on prompt: title-only, summary preview, or prompt-contextualized preview. If no prompt given, returns full content (up to max_content_length)."
        },
        "content_length": {
            "type": "integer",
            "description": "Length of the inline content in characters."
        },
        "total_content_length": {
            "type": "integer",
            "description": "Total length of the full fetched content (before truncation)."
        },
        "was_truncated": {
            "type": "boolean",
            "description": "True if content was truncated to max_content_length."
        },
        "content_file": {
            "type": "string",
            "description": "Absolute path to the full content file when was_truncated is true. Use read_file with offset/limit to paginate, or grep_files to search. Null if content was not truncated."
        },
        "message": {
            "type": "string",
            "description": "Error or informational message."
        }
    },
    requirement=["requests", "beautifulsoup4", "trafilatura", "lxml"],
    test_payload={
        "url": "https://example.com/article",
        "prompt": "summary",
        "timeout": 20,
        "simulated_mode": True
    }
)
def web_fetch(input_data: dict) -> dict:
    """Fetches content from a URL and returns cleaned text/markdown."""
    import re
    from urllib.parse import urlparse

    simulated_mode = input_data.get('simulated_mode', False)
    url = str(input_data.get('url', '')).strip()
    prompt = str(input_data.get('prompt', '')).strip() if input_data.get('prompt') else None
    timeout = float(input_data.get('timeout', 20))
    raw_max = input_data.get('max_content_length')
    try:
        max_content_length = int(raw_max) if raw_max is not None else 5000
    except (TypeError, ValueError):
        max_content_length = 5000
    if max_content_length < 0:
        max_content_length = 5000
    unlimited = (max_content_length == 0)
    use_jina_fallback = input_data.get('use_jina_fallback', True)
    session_id = input_data.get('_session_id', '')

    # --- Validate URL ---
    if not url:
        return _make_error('URL is required.')

    # Auto-upgrade HTTP to HTTPS (except localhost)
    if url.startswith('http://'):
        try:
            parsed = urlparse(url)
            host = parsed.hostname or ''
            if host not in ('localhost', '127.0.0.1', '::1'):
                url = 'https://' + url[7:]
        except Exception:
            url = 'https://' + url[7:]

    if not re.match(r'^https?://', url, re.I):
        return _make_error('A valid http(s) URL is required.', url)

    # --- Simulated mode ---
    if simulated_mode:
        mock_content = (
            "# Test Page Title\n\n"
            "This is simulated content fetched from the URL.\n\n"
            "## Main Content\n\n"
            "- Point 1: Important information\n"
            "- Point 2: More details\n"
            "- Point 3: Additional context\n\n"
            "## Summary\n\n"
            "This is a test page demonstrating the web_fetch action."
        )
        result_content = mock_content
        if prompt:
            result_content = _apply_prompt(prompt, mock_content, 'Test Page Title')

        return {
            'status': 'success',
            'status_code': 200,
            'status_text': 'OK',
            'url': url,
            'title': 'Test Page Title',
            'content': result_content,
            'content_length': len(result_content),
            'total_content_length': len(mock_content),
            'was_truncated': False,
            'content_file': None,
            'message': ''
        }

    # --- Fetch the URL ---
    try:
        import requests
        from bs4 import BeautifulSoup
        import trafilatura

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        # Fetch content — follow up to 10 redirects automatically
        response = requests.get(
            url, headers=headers, timeout=timeout,
            allow_redirects=True, stream=True
        )
        response.raise_for_status()

        status_code = response.status_code
        status_text = response.reason or ''
        final_url = str(response.url)

        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if not any(t in content_type for t in ('text/html', 'application/xhtml+xml', 'text/plain')):
            return _make_error(
                f'Unsupported content-type: {content_type}', final_url,
                status_code=status_code, status_text=status_text
            )

        # Read content with size limit (raw bytes cap to prevent memory issues)
        max_bytes = 500000  # 500KB raw cap
        content_bytes = b''
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                content_bytes += chunk
                if len(content_bytes) > max_bytes:
                    break

        encoding = response.encoding or 'utf-8'
        html_text = content_bytes.decode(encoding, errors='replace')

        # === TIER 1: Static Extraction ===
        title = ''
        content_md = ''
        min_content_length = 200

        try:
            content_md = trafilatura.extract(
                content_bytes,
                url=final_url,
                include_comments=False,
                include_tables=True,
                output_format='markdown'
            ) or ''

            try:
                meta = trafilatura.metadata.extract_metadata(content_bytes, url=final_url)
                if meta and getattr(meta, 'title', None):
                    title = meta.title.strip()
            except Exception:
                pass
        except Exception:
            pass

        # Fallback to BeautifulSoup
        if not content_md or len(content_md) < min_content_length:
            soup = BeautifulSoup(html_text, 'lxml')

            if not title and soup.title and soup.title.string:
                title = soup.title.string.strip()

            for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header']):
                tag.decompose()

            text = soup.get_text('\n')
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            bs_content = text.strip()

            if len(bs_content) > len(content_md or ''):
                content_md = bs_content

        # === TIER 2: Jina Reader API Fallback ===
        if use_jina_fallback and (not content_md or len(content_md) < min_content_length):
            try:
                jina_url = f"https://r.jina.ai/{url}"
                jina_headers = {
                    'Accept': 'text/plain',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                jina_response = requests.get(jina_url, headers=jina_headers, timeout=timeout)

                if jina_response.status_code == 200:
                    jina_content = jina_response.text.strip()
                    if jina_content and len(jina_content) > min_content_length:
                        content_md = jina_content

                        title_match = re.match(r'^#\s*(.+?)[\n\r]', jina_content)
                        if title_match and not title:
                            title = title_match.group(1).strip()
            except Exception:
                pass

        # === Clean content ===
        if content_md:
            content_md = re.sub(r'\n{4,}', '\n\n\n', content_md)
            content_md = content_md.strip()

        if not content_md:
            return _make_result(
                final_url, title, '', 0, status_code, status_text,
                message='No content could be extracted. Site may require JavaScript rendering or authentication.'
            )

        total_content_length = len(content_md)

        # === Apply prompt-based extraction ===
        if prompt:
            result_content = _apply_prompt(prompt, content_md, title)
            # Prompt-based results are already compact, no truncation needed
            return _make_result(
                final_url, title, result_content, total_content_length,
                status_code, status_text
            )

        # === No prompt — return raw content with truncation + file save ===
        was_truncated = False
        content_file = None

        if not unlimited and total_content_length > max_content_length:
            # Save full content to temp file
            content_file = _save_content_file(content_md, final_url, session_id)

            # Truncate at a sentence boundary
            truncated = content_md[:max_content_length]
            last_period = truncated.rfind('.')
            if last_period > max_content_length * 0.8:
                truncated = truncated[:last_period + 1]
            content_md = truncated
            was_truncated = True

        return _make_result(
            final_url, title, content_md, total_content_length,
            status_code, status_text,
            was_truncated=was_truncated, content_file=content_file,
            message=(
                f'Content truncated to {len(content_md)} chars. '
                f'Full content ({total_content_length} chars) saved to content_file. '
                f'Use read_file or grep_files on that path to access the rest.'
            ) if was_truncated else ''
        )

    except Exception as e:
        # Extract status code from requests exceptions when possible
        sc, st = 0, ''
        if hasattr(e, 'response') and e.response is not None:
            sc = e.response.status_code
            st = e.response.reason or ''

        error_type = type(e).__name__
        if 'Timeout' in error_type:
            msg = f'Request timed out after {timeout} seconds.'
        elif 'ConnectionError' in error_type:
            msg = f'Connection error: {str(e)}'
        elif 'HTTPError' in error_type:
            msg = f'HTTP error: {str(e)}'
        else:
            msg = f'Fetch failed: {str(e)}'

        return _make_error(msg, url, status_code=sc, status_text=st)


def _apply_prompt(prompt, content, title):
    """Apply prompt-based extraction to content.

    - 'title' in prompt: extract page title
    - 'summary'/'summarize' in prompt: return ~900 char preview
    - otherwise: return content preview with prompt context
    """
    import re
    lower_prompt = prompt.lower()

    # Collapse whitespace for compact previews
    compact = re.sub(r'\s+', ' ', content).strip()

    if 'title' in lower_prompt:
        if title:
            return f'Title: {title}'
        # Fallback: first 600 chars as preview
        return compact[:600]

    if 'summary' in lower_prompt or 'summarize' in lower_prompt:
        preview = compact[:900]
        if title:
            return f'Title: {title}\n\n{preview}'
        return preview

    # Custom prompt — return preview with prompt context
    preview = compact[:900]
    result = f'Prompt: {prompt}\n\nContent preview:\n{preview}'
    if title:
        result = f'Title: {title}\n{result}'
    return result


def _save_content_file(content, url, session_id):
    """Save full content to a temp file and return the path."""
    import os
    import tempfile
    from datetime import datetime, timezone
    from urllib.parse import urlparse

    # Determine temp directory
    # Try to find agent_file_system/workspace/tmp/{session_id} relative to project root
    temp_dir = None
    if session_id:
        try:
            # Walk up from this file to find the project root (contains agent_file_system/)
            current = os.path.abspath(__file__)
            for _ in range(10):
                current = os.path.dirname(current)
                candidate = os.path.join(current, 'agent_file_system', 'workspace', 'tmp', session_id)
                if os.path.isdir(os.path.join(current, 'agent_file_system')):
                    temp_dir = candidate
                    break
        except Exception:
            pass

    if not temp_dir:
        temp_dir = tempfile.gettempdir()

    os.makedirs(temp_dir, exist_ok=True)

    # Generate filename from URL domain + timestamp
    try:
        domain = urlparse(url).hostname or 'unknown'
        domain = domain.replace('.', '_')
    except Exception:
        domain = 'unknown'

    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S%f')
    filename = f'web_fetch_{domain}_{ts}.md'
    file_path = os.path.join(temp_dir, filename)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f'<!-- Source: {url} -->\n\n')
        f.write(content)

    return file_path


def _make_result(url, title, content, total_content_length,
                 status_code, status_text,
                 was_truncated=False, content_file=None, message=''):
    """Build a success response."""
    return {
        'status': 'success',
        'status_code': status_code,
        'status_text': status_text,
        'url': url,
        'title': title or '',
        'content': content,
        'content_length': len(content),
        'total_content_length': total_content_length,
        'was_truncated': was_truncated,
        'content_file': content_file,
        'message': message
    }


def _make_error(message, url='', status_code=0, status_text=''):
    """Build an error response."""
    return {
        'status': 'error',
        'status_code': status_code,
        'status_text': status_text,
        'url': url,
        'title': '',
        'content': '',
        'content_length': 0,
        'total_content_length': 0,
        'was_truncated': False,
        'content_file': None,
        'message': message
    }
