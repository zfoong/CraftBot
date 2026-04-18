from agent_core import action

@action(
        name="http_request",
        description="Sends HTTP requests (GET, POST, PUT, PATCH, DELETE) with optional headers, params, and body.",
        mode="CLI",
        action_sets=["core"],
        input_schema={
                "method": {
                        "type": "string",
                        "enum": [
                                "GET",
                                "POST",
                                "PUT",
                                "PATCH",
                                "DELETE"
                        ],
                        "example": "GET",
                        "description": "HTTP method to use."
                },
                "url": {
                        "type": "string",
                        "example": "https://api.example.com/v1/items",
                        "description": "Absolute URL to request. Must start with http or https."
                },
                "headers": {
                        "type": "object",
                        "example": {
                                "Authorization": "Bearer <token>",
                                "Accept": "application/json"
                        },
                        "description": "Optional headers to send as key-value pairs."
                },
                "params": {
                        "type": "object",
                        "example": {
                                "q": "search",
                                "limit": "10"
                        },
                        "description": "Optional query parameters."
                },
                "json": {
                        "type": "object",
                        "example": {
                                "name": "Widget",
                                "price": 19.99
                        },
                        "description": "JSON body to send. Mutually exclusive with 'data'."
                },
                "data": {
                        "type": "string",
                        "example": "field1=value1&field2=value2",
                        "description": "Raw request body (e.g., form-encoded or plain text). Mutually exclusive with 'json'."
                },
                "timeout": {
                        "type": "number",
                        "example": 30,
                        "description": "Timeout in seconds. Defaults to 30."
                },
                "allow_redirects": {
                        "type": "boolean",
                        "example": True,
                        "description": "Whether to follow redirects. Defaults to true."
                },
                "verify_tls": {
                        "type": "boolean",
                        "example": True,
                        "description": "Verify TLS certificates. Defaults to true."
                }
        },
        output_schema={
                "status": {
                        "type": "string",
                        "example": "success",
                        "description": "'success' if the request completed, 'error' otherwise."
                },
                "status_code": {
                        "type": "integer",
                        "example": 200,
                        "description": "HTTP status code from the response."
                },
                "response_headers": {
                        "type": "object",
                        "example": {
                                "Content-Type": "application/json"
                        },
                        "description": "Response headers returned by the server."
                },
                "body": {
                        "type": "string",
                        "example": "{\"ok\":true}",
                        "description": "Response body as text."
                },
                "response_json": {
                        "type": "object",
                        "example": {
                                "ok": True
                        },
                        "description": "Parsed JSON body if available; otherwise omitted."
                },
                "final_url": {
                        "type": "string",
                        "example": "https://api.example.com/v1/items?limit=10",
                        "description": "Final URL after redirects."
                },
                "elapsed_ms": {
                        "type": "number",
                        "example": 123,
                        "description": "Round-trip time in milliseconds."
                },
                "message": {
                        "type": "string",
                        "example": "HTTP 404",
                        "description": "Error message if applicable."
                }
        },
        requirement=["requests"],
        test_payload={
                "method": "GET",
                "url": "https://api.example.com/v1/items",
                "headers": {
                        "Authorization": "Bearer <token>",
                        "Accept": "application/json"
                },
                "params": {
                        "q": "search",
                        "limit": "10"
                },
                "timeout": 30,
                "allow_redirects": True,
                "verify_tls": True,
                "simulated_mode": True
        }
)
def send_http_requests(input_data: dict) -> dict:
    import json, sys, subprocess, importlib, time
    pkg = 'requests'
    try:
        importlib.import_module(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '--quiet'])
    import requests
    
    simulated_mode = input_data.get('simulated_mode', False)
    
    if simulated_mode:
        # Return mock result for testing
        return {
            'status': 'success',
            'status_code': 200,
            'response_headers': {'Content-Type': 'application/json'},
            'body': '{"ok": true}',
            'final_url': input_data.get('url', ''),
            'elapsed_ms': 100,
            'message': ''
        }
    
    method = str(input_data.get('method', 'GET')).upper()
    url = str(input_data.get('url', '')).strip()
    headers = input_data.get('headers') or {}
    params = input_data.get('params') or {}
    json_body = input_data.get('json') if 'json' in input_data else None
    data_body = input_data.get('data') if 'data' in input_data else None
    timeout = float(input_data.get('timeout', 30))
    allow_redirects = bool(input_data.get('allow_redirects', True))
    verify_tls = bool(input_data.get('verify_tls', True))
    allowed = {'GET','POST','PUT','PATCH','DELETE'}

    def _error(message, status_code=0, final_url='', elapsed_ms=0):
        return {'status':'error','status_code':status_code,'response_headers':{},'body':'','final_url':final_url,'elapsed_ms':elapsed_ms,'message':message}

    if method not in allowed:
        return _error('Unsupported method.')
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        return _error('Invalid or missing URL.')

    # SSRF protection: block requests to private/internal networks and cloud metadata
    from urllib.parse import urlparse as _urlparse, urljoin as _urljoin
    import ipaddress as _ipaddress
    import socket as _socket

    _BLOCKED_HOSTS = frozenset({'169.254.169.254', 'metadata.google.internal', 'metadata.internal'})

    def _is_url_ssrf_safe(check_url: str) -> 'str | None':
        """Return an error message if the URL targets a blocked host, or None if safe."""
        _parsed = _urlparse(check_url)
        # Block non-HTTP schemes (file://, gopher://, etc.)
        if _parsed.scheme not in ('http', 'https'):
            return f'Blocked: only http/https schemes are allowed (got {_parsed.scheme}).'
        _hostname = _parsed.hostname or ''
        if _hostname in _BLOCKED_HOSTS:
            return 'Blocked: requests to cloud metadata endpoints are not allowed.'
        try:
            _resolved = _socket.getaddrinfo(_hostname, None)
            for _family, _type, _proto, _canonname, _sockaddr in _resolved:
                _ip = _ipaddress.ip_address(_sockaddr[0])
                if _ip.is_private or _ip.is_loopback or _ip.is_link_local:
                    return f'Blocked: requests to private/internal addresses ({_hostname}) are not allowed.'
        except (_socket.gaierror, ValueError):
            return f'Blocked: could not resolve hostname ({_hostname}).'
        return None

    ssrf_error = _is_url_ssrf_safe(url)
    if ssrf_error:
        return _error(ssrf_error)
    if json_body is not None and data_body is not None:
        return _error('Provide either json or data, not both.')
    if not isinstance(headers, dict) or not isinstance(params, dict):
        return _error('headers and params must be objects.')
    headers = {str(k): str(v) for k, v in headers.items()}
    params = {str(k): str(v) for k, v in params.items()}
    kwargs = {'headers': headers, 'params': params, 'timeout': timeout, 'allow_redirects': False, 'verify': verify_tls}
    if json_body is not None:
        kwargs['json'] = json_body
    elif data_body is not None:
        kwargs['data'] = data_body
    try:
        t0 = time.time()
        resp = requests.request(method, url, **kwargs)
        # Manually follow redirects with SSRF validation on each hop
        _max_redirects = 10
        while allow_redirects and resp.is_redirect and _max_redirects > 0:
            _max_redirects -= 1
            redirect_url = resp.headers.get('Location', '')
            if not redirect_url:
                break
            # Resolve relative redirects
            if not redirect_url.startswith(('http://', 'https://')):
                redirect_url = _urljoin(resp.url, redirect_url)
            redirect_error = _is_url_ssrf_safe(redirect_url)
            if redirect_error:
                return _error(f'Redirect blocked: {redirect_error}', status_code=resp.status_code, final_url=resp.url, elapsed_ms=int((time.time()-t0)*1000))
            # 307/308 preserve method; all others downgrade to GET per RFC 7231
            redirect_method = method if resp.status_code in (307, 308) else 'GET'
            redirect_kwargs = {**kwargs, 'allow_redirects': False}
            # Strip body on method downgrade to GET
            if redirect_method == 'GET':
                redirect_kwargs.pop('json', None)
                redirect_kwargs.pop('data', None)
            # Strip auth headers on cross-origin redirects
            _orig_host = _urlparse(url).netloc
            _redir_host = _urlparse(redirect_url).netloc
            if _orig_host != _redir_host and 'Authorization' in redirect_kwargs.get('headers', {}):
                redirect_kwargs['headers'] = {k: v for k, v in redirect_kwargs['headers'].items() if k != 'Authorization'}
            resp = requests.request(redirect_method, redirect_url, **redirect_kwargs)
        elapsed_ms = int((time.time() - t0) * 1000)
        resp_headers = {k: v for k, v in resp.headers.items()}
        parsed_json = None
        try:
            parsed_json = resp.json()
        except Exception:
            parsed_json = None
        out = {
            'status': 'success' if resp.ok else 'error',
            'status_code': resp.status_code,
            'response_headers': resp_headers,
            'body': resp.text,
            'final_url': resp.url,
            'elapsed_ms': elapsed_ms,
            'message': '' if resp.ok else f'HTTP {resp.status_code}'
        }
        if parsed_json is not None:
            out['response_json'] = parsed_json
        return out
    except Exception as e:
        return {'status':'error','status_code':0,'response_headers':{},'body':'','final_url':'','elapsed_ms':0,'message':str(e)}