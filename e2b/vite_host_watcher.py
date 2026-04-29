"""Background daemon — patches Living UI projects' vite.config.ts at runtime.

Why this exists
---------------
patch_for_e2b.py runs ONCE at sandbox build time. It patches the bundled
Living UI template, but marketplace apps (and any user-created projects
that bypass the template) appear AFTER the sandbox has booted. Vite 5+
rejects requests whose Host header isn't in `allowedHosts`, so without
this watcher every marketplace install would 403 with:

    Blocked request. This host ("3100-<sandbox>.e2b.app") is not allowed.
    To allow this host, add "3100-<sandbox>.e2b.app" to `preview.allowedHosts`.

The daemon polls the Living UI workspace every couple of seconds and
patches any vite.config.ts it hasn't seen yet. The patch is idempotent
(marker comment) so re-runs are no-ops.

Why polling instead of inotifywait
----------------------------------
- No extra apt deps (inotify-tools isn't in the base desktop image).
- Polling 2s is plenty: project lifecycle is `git clone → npm install →
  vite start`, and `npm install` alone takes 30+ seconds, so we always
  catch the config before vite reads it.
- One process, plain stdlib, easy to reason about.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Reuse the patcher from the build-time script so the marker / regex stays
# in one place.
sys.path.insert(0, "/home/user/agent/e2b")
from patch_for_e2b import patch_vite_config  # noqa: E402

WORKSPACE = Path("/home/user/agent/agent_file_system/workspace/living_ui")
POLL_INTERVAL_S = 2.0


def main() -> int:
    print("[e2b-vite-watcher] starting; polling", WORKSPACE, "every", POLL_INTERVAL_S, "s")
    while True:
        try:
            if WORKSPACE.is_dir():
                for cfg in WORKSPACE.rglob("vite.config.*"):
                    try:
                        if patch_vite_config(cfg):
                            print(f"[e2b-vite-watcher] patched {cfg}")
                    except Exception as e:
                        print(f"[e2b-vite-watcher] error on {cfg}: {e}", file=sys.stderr)
        except Exception as e:
            # Don't let any error kill the watcher — log and keep going.
            print(f"[e2b-vite-watcher] poll error: {e}", file=sys.stderr)
        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    sys.exit(main())
