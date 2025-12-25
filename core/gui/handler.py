from typing import Optional
import mss
import mss.tools


class GUIHandler:
    @classmethod
    def get_screen_state(cls) -> Optional[bytes]:
        """
        Capture the primary monitor and return PNG bytes in memory.
        Returns None on failure.
        """
        try:
            with mss.mss() as sct:
                monitors = sct.monitors

                # Primary monitor is index 1 if available
                monitor = monitors[1] if len(monitors) > 1 else monitors[0]

                shot = sct.grab(monitor)
                png_bytes = mss.tools.to_png(
                    shot.rgb,
                    shot.size,
                    output=None,
                )

                return png_bytes

        except Exception as e:
            print(f"[ScreenState ERROR] {e}")
            return None
