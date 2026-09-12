"""Send Unicode keystrokes and clipboard operations for the current OS."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .injector_win import *  # noqa: F403
else:
    from .injector_generic import *  # noqa: F403
