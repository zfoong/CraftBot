"""PyInstaller runtime hook: force UTF-8 on stdout/stderr.

In frozen builds — especially `console=False` windowed builds on Windows —
Python's stdout/stderr default to the system locale codec (cp1252 in most
locales). Any non-Latin-1 character (the box-drawing glyphs in run.py's
banner, emoji in messages, etc.) crashes with UnicodeEncodeError.

PYTHONIOENCODING is ignored by frozen PyInstaller bootloaders, so we
reconfigure here at startup, before any user code runs.

Strategy:
  1. If the stream supports `.reconfigure()` (Python 3.7+ TextIOWrapper),
     try it. Cheap and non-destructive.
  2. Otherwise rebuild a fresh TextIOWrapper around the underlying FD with
     UTF-8 encoding. We have to grab the FD before replacing the stream.
  3. If even that fails (no FD — e.g. windowed build with stdout=None),
     install a NullIO so unconditional `print()` calls don't crash.

Force-rebuild safety: this runs unconditionally on Windows whether or not
the existing stream looks OK, because a "looks OK" cp1252 stream is exactly
the case we need to fix.
"""

import io
import os
import sys


class _NullIO(io.TextIOBase):
    def isatty(self) -> bool:
        return False

    def write(self, s: str) -> int:
        return len(s)

    def flush(self) -> None:
        pass

    @property
    def encoding(self) -> str:
        return "utf-8"


def _force_utf8(name: str) -> None:
    stream = getattr(sys, name, None)

    # No stream at all (windowed build with stdio detached) — install NullIO.
    if stream is None:
        setattr(sys, name, _NullIO())
        return

    # Already UTF-8? Leave it alone.
    enc = getattr(stream, "encoding", "") or ""
    if enc.lower().replace("-", "") == "utf8":
        return

    # Path 1: reconfigure() — preserves the stream object identity.
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
            return
        except Exception:
            pass

    # Path 2: rebuild a TextIOWrapper around the same FD with UTF-8.
    fd = -1
    try:
        fd = stream.fileno()
    except Exception:
        pass
    if fd != -1:
        try:
            try:
                stream.flush()
            except Exception:
                pass
            new = io.TextIOWrapper(
                os.fdopen(fd, "wb", buffering=0, closefd=False),
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
                write_through=True,
            )
            setattr(sys, name, new)
            return
        except Exception:
            pass

    # Path 3: nothing worked — replace with a sink so prints don't crash.
    setattr(sys, name, _NullIO())


for _name in ("stdout", "stderr"):
    _force_utf8(_name)
