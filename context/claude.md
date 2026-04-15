# CraftBot Security Review - Session Context

## Current State

- **Repo:** CraftOS-dev/CraftBot (cloned to ~/Claude/projects/CraftBot)
- **Fork:** eesb99/CraftBot
- **Branch:** security/fix-critical-vulnerabilities
- **PR:** CraftOS-dev/CraftBot#198 (open -- follow-up to merged #195)
- **Date:** 2026-04-16 (Session 2)

## Session 1 Summary (2026-04-15)

### Goals
- Clone CraftBot repo and perform a full security review
- Fix identified vulnerabilities and submit PR to upstream

### Security Review Findings (12 total)

| # | Severity | Finding | CWE | Fixed? |
|---|----------|---------|-----|--------|
| 1 | CRITICAL | Hardcoded OAuth credentials (base64-encoded in source) | CWE-798 | No (arch) |
| 2 | CRITICAL | Unsandboxed `exec()` of LLM-generated Python | CWE-94 | No (arch) |
| 3 | CRITICAL | Unrestricted `shell=True` command execution | CWE-78 | No (arch) |
| 4 | HIGH | Plaintext credential storage | CWE-312 | Yes (permissions) |
| 5 | HIGH | No path traversal protection on file ops | CWE-22 | Yes |
| 6 | HIGH | XSS in OAuth callback | CWE-79 | Yes |
| 7 | HIGH | Prompt sanitizer detects but doesn't block | CWE-20 | Yes |
| 8 | MEDIUM | Auto-install arbitrary pip packages | CWE-829 | No (design) |
| 9 | MEDIUM | Docker socket exposure | CWE-250 | No (deploy) |
| 10 | MEDIUM | No SSRF protection on HTTP requests | CWE-918 | Yes |
| 11 | MEDIUM | OAuth state not validated (CSRF) | CWE-352 | Yes |
| 12 | LOW | Broad `COPY .` in Dockerfile | - | No (low risk) |

### Files Modified (6)
1. `agent_core/core/credentials/oauth_server.py` - XSS fix + CSRF state validation
2. `app/data/action/http_request.py` - SSRF protection (private IPs, cloud metadata)
3. `app/data/action/read_file.py` - Path traversal protection
4. `app/data/action/write_file.py` - Path traversal protection
5. `app/external_comms/credentials.py` - File permission hardening (0600)
6. `app/security/prompt_sanitizer.py` - Enforce pattern stripping

### Commits
- `ae5025e` - security: fix 6 vulnerabilities (XSS, CSRF, SSRF, path traversal, credential storage, prompt injection)

### Key Architecture Notes
- Python AI agent with LLM integrations (OpenAI, Gemini, Anthropic)
- OAuth for 6+ platforms (Google, Slack, Notion, LinkedIn, Discord, Telegram)
- Actions system in `app/data/action/` -- each action is a decorated function
- Credentials stored as JSON in `.credentials/` directory
- GUI mode uses Docker containers with desktop environments
- 150+ skills in `skills/` directory
- TUI built with Textual, browser UI with separate frontend

### Next Steps
- [x] Monitor PR CraftOS-dev/CraftBot#195 for maintainer feedback -- MERGED
- [ ] Consider filing separate issues for the 3 CRITICAL unfixed items
- [ ] If PR is merged, the embedded credentials issue should be escalated as a security advisory

## Session 2 Summary (2026-04-16)

### Goals
- Rebase security branch onto latest origin/main
- Code review (unified-review --fix) of session 1 security fixes
- Fix bugs and architectural bypass vectors found during review
- Open follow-up PR (#198) to upstream

### Unified Review Findings (10 total, >= 80 confidence)

Dispatched parallel reviewers: python-code-reviewer + security-focused code-reviewer.

| Confidence | Finding | Status |
|-----------|---------|--------|
| 95 | `socket.gaierror` vs `_socket.gaierror` NameError silently disabled SSRF | Fixed (auto-fix) |
| 93 | HTTP redirect bypass defeats SSRF check entirely | Fixed (PR A) |
| 92 | CSRF state validation silently skipped when state absent | Fixed (PR A) |
| 90 | DNS rebinding TOCTOU in resolve-then-request pattern | Deferred |
| 88 | Non-timing-safe OAuth state comparison | Fixed (auto-fix) |
| 85 | Path blocklist too narrow for read_file/write_file | Deferred |
| 85 | Credential file written world-readable before chmod | Fixed (auto-fix) |
| 82 | Outer `except Exception: pass` makes SSRF fail-open | Fixed (PR A) |
| 82 | Sequential pattern stripping creates new injection vectors | Deferred |
| 80 | Overly broad regex causes false positives on "run", "import" | Deferred |

### Implementation Details

**Commit 1 (c8389b2) -- Bug fixes (auto-fix phase):**
- `_socket.gaierror` NameError fix
- `hmac.compare_digest()` for timing-safe OAuth state comparison
- `os.open()` with 0o600 for atomic credential file permissions

**Commit 2 (91ac962) -- Architectural fixes (PR A):**
- Extracted `_is_url_ssrf_safe()` helper for reuse across redirect hops
- Disabled `allow_redirects`, manually follow redirects with SSRF validation per hop
- Removed fail-open `except Exception: pass` -- DNS failures now block requests
- Explicit 3-way CSRF state handling (no state/missing from callback/mismatch)

### Files Modified (3)
1. `app/data/action/http_request.py` - SSRF redirect validation, fail-closed, helper extraction
2. `agent_core/core/credentials/oauth_server.py` - CSRF enforcement, timing-safe comparison
3. `app/external_comms/credentials.py` - Atomic file permissions

### Commits
- `c8389b2` - security: fix SSRF NameError, timing-safe OAuth state, atomic credential perms
- `91ac962` - security: fix SSRF redirect bypass, fail-closed validation, CSRF enforcement

### Code Design Assessment
- Architecture is solid (protocol-driven, registry DI, plugin-based)
- Security was bolted on after the fact, not designed in
- Zero test infrastructure -- biggest gap for security confidence
- Prompt sanitizer is fundamentally unsound (regex vs semantic attacks)
- Blocklist approach is inherently weaker than allowlist for file/URL validation

### Advisor Recommendations (prioritized)
1. **PR A** (done): SSRF redirect bypass + fail-closed + CSRF enforcement
2. **PR B** (next): pytest infrastructure + action file unit tests
3. **PR C** (future): Extract shared validation utilities (`validate_url()`, `validate_file_path()`)
4. **Skip**: Prompt sanitizer iteration (flawed approach, suggest architecture change instead)

### Next Steps
- [ ] Monitor PR CraftOS-dev/CraftBot#198 for maintainer feedback
- [ ] PR B: Add pytest framework with tests for http_request, read_file, write_file
- [ ] PR C: Extract centralized validation utilities
- [ ] File GitHub issue recommending prompt injection architecture change
- [ ] Consider filing security advisory for embedded OAuth credentials (CWE-798)
