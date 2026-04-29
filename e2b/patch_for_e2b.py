"""Sandbox-side patches that make Living UI iframes work in E2B.

Also exposes `patch_vite_config(path)` — used by both this one-shot
build-time script and the long-running `vite_host_watcher.py` daemon
(see e2b-start.sh) so marketplace apps downloaded at runtime get the
same `allowedHosts: true` treatment as the bundled template.

Runs ONCE during E2B template build, after the agent code has been copied
into /home/user/agent and BEFORE `npm run build`. The patches live only
inside the sandbox image — the user's git checkout is untouched.

Why this exists
---------------
The agent hands the browser absolute URLs like `http://localhost:3100`
for Living UI iframes. On localhost that just works. In E2B the user's
browser is on a different machine — `localhost` resolves to *their* box,
not the sandbox — so the iframe load 404s.

E2B exposes every port listening inside a sandbox at a public subdomain:
    https://<port>-<sandbox-id>.e2b.dev

So if a Living UI is on internal port 3100 inside sandbox `abc123`, the
browser-reachable URL is `https://3100-abc123.e2b.dev`. Same for the
backend port.

This script applies two patches that translate between the two worlds:

1. **Agent shell (top-level page)** — inject a `<script>` into
   `app/ui_layer/browser/frontend/index.html` (BEFORE the bundled JS
   loads) that overrides `HTMLIFrameElement.src` so any assignment of a
   `http://localhost:NNNN/...` URL gets rewritten to the matching E2B
   subdomain. iframePool.ts and any other iframe creation code goes
   through this setter, so a single override catches them all.

2. **Living UI project template** — replace the existing
   `__CRAFTBOT_BACKEND_URL__` block in
   `app/data/living_ui_template/index.html` with one that detects E2B
   (hostname matches `^\d+-`) and uses the matching backend subdomain
   instead of `<frontend-host>:<backend-port>` (which doesn't work in
   E2B since browsers can't reach random ports cross-origin).

Both patches are no-ops when the page is loaded from `localhost` — the
runtime detection (`/\.e2b\.dev$/`) keeps the logic dormant when
someone runs the same image elsewhere or runs the agent locally for
debugging.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AGENT_ROOT = Path("/home/user/agent")

# Marker comment dropped into vite.config.ts so we can detect
# "already patched" and skip without making the file noisier on every poll.
VITE_HOST_PATCH_MARKER = "/* e2b-allow-hosts */"

# Vite 5+ rejects requests whose Host header isn't in `allowedHosts`
# (a CSRF-style defence against DNS rebinding). E2B's port-forwarding
# subdomains (`<port>-<sandbox-id>.e2b.app`) aren't in the default list,
# so every Living UI iframe load 403s with "Blocked request" until we
# inject this. `true` accepts all hosts — fine inside a sandbox.
VITE_HOST_PATCH_LINE = "    allowedHosts: true, " + VITE_HOST_PATCH_MARKER


def patch_vite_config(path: Path) -> bool:
    """Apply two E2B-only fixes to a vite.config.{ts,js}, idempotent via
    the marker comment:

    1. **`allowedHosts: true`** in both `server` and `preview` blocks —
       Vite 5+ rejects requests whose Host header isn't allowlisted, and
       the default list doesn't include E2B's `<port>-<sandbox>.e2b.app`
       subdomains.

    2. **Rewrite `http://localhost:` proxy targets to `http://127.0.0.1:`** —
       Node 17+ resolves `localhost` to IPv6 (`::1`) first. If the project's
       backend binds only IPv4, Vite's proxy gets `ECONNREFUSED ::1:<port>`
       on every `/api/*` request. Forcing IPv4 in the proxy target
       sidesteps the dual-stack ambiguity entirely.

    Returns True when the file was modified.
    """
    if not path.is_file():
        return False
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return False

    new = src

    # Fix 1: inject `allowedHosts: true` into server/preview blocks. Skip
    # if the marker is already present so we don't stack duplicates on
    # subsequent watcher polls.
    if VITE_HOST_PATCH_MARKER not in new:
        new = re.sub(
            r"(\b(?:server|preview)\s*:\s*\{)",
            r"\1\n" + VITE_HOST_PATCH_LINE,
            new,
        )

    # Fix 2: force IPv4 in proxy targets. Naturally idempotent (the regex
    # finds no match after the first pass), so it's safe to re-run on
    # files patched by older versions of this script that only had Fix 1.
    new = re.sub(
        r"http://localhost:",
        "http://127.0.0.1:",
        new,
    )

    if new == src:
        return False
    try:
        path.write_text(new, encoding="utf-8")
    except Exception:
        return False
    return True

# JS injected into the agent shell. Detects remote hosting (anything that
# isn't localhost) and rewrites Living UI iframe srcs from
# http://localhost:<port> to a public URL the user's browser can reach.
# Wrapped in IIFE; no globals leaked. Logs to console so it's debuggable.
AGENT_SHELL_REWRITER = """\
<script>
// E2B (and generic remote-hosting) URL rewriter — injected at sandbox
// build time by e2b/patch_for_e2b.py. Translates Living UI iframe srcs
// from http://localhost:<port> to a host the user's remote browser can
// reach. Dormant on real localhost.
(function () {
  var host = window.location.hostname;
  // Activate for any non-loopback host. Covers e2b.dev, e2b.app, ngrok,
  // Cloudflare tunnels, custom domains, LAN IPs — anywhere the browser
  // is on a different machine than the agent.
  if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
    console.log('[e2b-rewriter] dormant on local host:', host);
    return;
  }
  console.log('[e2b-rewriter] active on host:', host);

  // E2B port-forwarding subdomain pattern. Both .e2b.dev (older) and
  // .e2b.app (newer) work the same way: each port the sandbox listens
  // on is exposed as `<port>-<sandbox-id>.<domain>`.
  // For other hosts (ngrok / Cloudflare) we don't know the pattern, so
  // we fall back to the same-origin approach which only works if the
  // proxy is forwarding all ports under one subdomain — unlikely. The
  // E2B path is the load-bearing one.
  // Strip a leading "<port>-" if present (defensive — happens when the
  // rewriter runs inside an already-port-mapped iframe, not the shell).
  var baseHost = host.replace(/^\\d+-/, '');

  function rewrite(value) {
    if (typeof value !== 'string') return value;
    var m = value.match(/^https?:\\/\\/(?:localhost|127\\.0\\.0\\.1):(\\d+)(.*)$/);
    if (!m) return value;
    var rewritten = 'https://' + m[1] + '-' + baseHost + (m[2] || '');
    console.log('[e2b-rewriter] rewrote', value, '->', rewritten);
    return rewritten;
  }

  // 1. Override the .src setter on HTMLIFrameElement (iframePool.ts uses this).
  try {
    var iframeSrcDescriptor =
      Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'src')
      || Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'src');
    if (iframeSrcDescriptor && iframeSrcDescriptor.set) {
      var origSrcSetter = iframeSrcDescriptor.set;
      Object.defineProperty(HTMLIFrameElement.prototype, 'src', {
        set: function (value) { origSrcSetter.call(this, rewrite(value)); },
        get: iframeSrcDescriptor.get,
        configurable: true,
      });
      console.log('[e2b-rewriter] HTMLIFrameElement.src setter overridden');
    } else {
      console.warn('[e2b-rewriter] could not find iframe src descriptor');
    }
  } catch (e) {
    console.error('[e2b-rewriter] failed to override iframe src setter:', e);
  }

  // 2. Belt-and-suspenders for code that uses setAttribute('src', ...).
  try {
    var origSetAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function (name, value) {
      if (this.tagName === 'IFRAME' && name === 'src') value = rewrite(value);
      return origSetAttr.call(this, name, value);
    };
    console.log('[e2b-rewriter] Element.setAttribute overridden');
  } catch (e) {
    console.error('[e2b-rewriter] failed to override setAttribute:', e);
  }
})();
</script>
"""

# Replacement for the Living UI project template's backend URL detection.
# {{BACKEND_PORT}} is substituted by the agent at project-creation time.
LIVING_UI_BACKEND_BLOCK_NEW = """\
    <!-- Backend URL: prefers E2B subdomain when running inside a sandbox,
         falls back to same-origin for HTTPS tunnels, then to direct port
         access for plain localhost / LAN. Patched by e2b/patch_for_e2b.py
         during sandbox image build. -->
    <script>
      (function () {
        var host = window.location.hostname;
        // Inside an E2B sandbox the iframe hostname looks like
        // "<frontend-port>-<sandbox-id>.e2b.dev". Strip the port prefix
        // and map to the backend port the same way.
        var e2bMatch = host.match(/^\\d+-(.+\\.e2b\\.dev)$/);
        if (e2bMatch) {
          window.__CRAFTBOT_BACKEND_URL__ = 'https://{{BACKEND_PORT}}-' + e2bMatch[1];
        } else if (window.location.protocol === 'https:') {
          window.__CRAFTBOT_BACKEND_URL__ = window.location.origin;
        } else {
          window.__CRAFTBOT_BACKEND_URL__ = 'http://' + host + ':{{BACKEND_PORT}}';
        }
      })();
    </script>"""

# Marker text identifying the original block in the template — used to
# locate the start of the script we're replacing. Matched as a substring,
# so whitespace and quoting variations don't matter.
LIVING_UI_OLD_BLOCK_START = "<!-- Backend URL:"
LIVING_UI_OLD_BLOCK_END = "</script>"


def patch_agent_shell(path: Path) -> None:
    """Inject the iframe URL rewriter into the agent shell's index.html.

    Idempotent — checks for a marker comment so re-running the build
    doesn't stack multiple copies.
    """
    if not path.is_file():
        print(f"[e2b-patch] SKIP (missing): {path}")
        return
    html = path.read_text(encoding="utf-8")
    if "E2B URL rewriter" in html:
        print(f"[e2b-patch] SKIP (already patched): {path}")
        return
    head_close = html.lower().find("</head>")
    if head_close < 0:
        print(f"[e2b-patch] SKIP (no </head>): {path}")
        return
    patched = html[:head_close] + AGENT_SHELL_REWRITER + html[head_close:]
    path.write_text(patched, encoding="utf-8")
    print(f"[e2b-patch] Injected E2B iframe rewriter into {path}")


def patch_living_ui_template(path: Path) -> None:
    """Replace the backend URL detection block in the Living UI project
    template's index.html.

    The block to replace runs from the `<!-- Backend URL:` comment to the
    immediately-following `</script>`. We locate by substring so minor
    formatting changes upstream don't break the match.
    """
    if not path.is_file():
        print(f"[e2b-patch] SKIP (missing): {path}")
        return
    html = path.read_text(encoding="utf-8")
    if "Patched by e2b/patch_for_e2b.py" in html:
        print(f"[e2b-patch] SKIP (already patched): {path}")
        return
    start = html.find(LIVING_UI_OLD_BLOCK_START)
    if start < 0:
        print(f"[e2b-patch] SKIP (backend URL block not found): {path}")
        return
    end = html.find(LIVING_UI_OLD_BLOCK_END, start)
    if end < 0:
        print(f"[e2b-patch] SKIP (no closing </script>): {path}")
        return
    end += len(LIVING_UI_OLD_BLOCK_END)
    # Preserve the leading indentation of the block we replaced so the
    # replacement reads naturally in source.
    line_start = html.rfind("\n", 0, start) + 1
    indent = html[line_start:start]
    replacement = LIVING_UI_BACKEND_BLOCK_NEW
    if indent and not replacement.startswith(indent):
        # Strip the literal indent we baked in if upstream's differs.
        pass
    patched = html[:line_start] + replacement + html[end:]
    path.write_text(patched, encoding="utf-8")
    print(f"[e2b-patch] Replaced backend URL block in {path}")


def main() -> int:
    targets = [
        (
            AGENT_ROOT / "app" / "ui_layer" / "browser" / "frontend" / "index.html",
            patch_agent_shell,
        ),
        (
            AGENT_ROOT / "app" / "data" / "living_ui_template" / "index.html",
            patch_living_ui_template,
        ),
    ]
    for path, fn in targets:
        try:
            fn(path)
        except Exception as e:
            print(f"[e2b-patch] ERROR patching {path}: {e}", file=sys.stderr)
            # Don't fail the build — the patches are an enhancement, not
            # a hard requirement. A WARN line in the build log is enough.

    # Patch the Living UI template's vite.config.ts so projects scaffolded
    # from it get `allowedHosts: true` baked in. Marketplace apps are
    # downloaded at runtime and patched by vite_host_watcher.py instead.
    template_vite = (
        AGENT_ROOT / "app" / "data" / "living_ui_template" / "vite.config.ts"
    )
    try:
        if patch_vite_config(template_vite):
            print(f"[e2b-patch] Patched vite allowedHosts in {template_vite}")
        else:
            print(f"[e2b-patch] vite.config.ts already patched or unchanged: {template_vite}")
    except Exception as e:
        print(f"[e2b-patch] ERROR patching {template_vite}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
