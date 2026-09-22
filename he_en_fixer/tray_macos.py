"""macOS menu bar refinements for the pystray status item.

pystray squeezes the tray image into a square at 1x, which is blurry on Retina and
ignores the menu bar's light/dark appearance. These helpers reach into the status
item to install a Retina template image instead, and report when macOS has parked
the icon behind the camera housing because the menu bar is full.
"""

from __future__ import annotations

import io

from PIL import Image

try:
    import AppKit
    import Foundation
except ImportError:  # pragma: no cover - only importable on macOS with pyobjc
    AppKit = None
    Foundation = None

# Points of menu bar height the glyph is drawn for; the image itself is 2x that.
MENU_BAR_SCALE = 2

# macOS remembers a status item's slot under this name once it is set.
AUTOSAVE_NAME = "he-en-fixer"

# Seeded the first time only: a slot near the right of the menu bar, so a full
# menu bar does not push the icon behind the camera housing. Dragging it later
# overwrites this.
DEFAULT_PREFERRED_POSITION = 0.0


def available() -> bool:
    return AppKit is not None


def _status_button(icon):
    item = getattr(icon, "_status_item", None)
    return item.button() if item is not None else None


def _on_main_thread(work) -> None:
    if Foundation.NSThread.isMainThread():
        work()
        return
    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(work)


def set_menu_bar_image(icon, image: Image.Image, scale: int = MENU_BAR_SCALE) -> bool:
    """Install `image` as a Retina template image on the status item."""
    if not available():
        return False
    button = _status_button(icon)
    if button is None:
        return False

    buffer = io.BytesIO()
    image.save(buffer, "png")
    data = Foundation.NSData(buffer.getvalue())

    def apply() -> None:
        ns_image = AppKit.NSImage.alloc().initWithData_(data)
        ns_image.setSize_(
            Foundation.NSMakeSize(image.width / scale, image.height / scale)
        )
        # Template images are recoloured by macOS for light and dark menu bars.
        ns_image.setTemplate_(True)
        button.setImage_(ns_image)

    _on_main_thread(apply)
    return True


def pin_menu_bar_position(icon) -> bool:
    """Give the status item a remembered slot, seeding a visible one on first run."""
    if not available():
        return False
    item = getattr(icon, "_status_item", None)
    if item is None:
        return False

    defaults = Foundation.NSUserDefaults.standardUserDefaults()
    key = f"NSStatusItem Preferred Position {AUTOSAVE_NAME}"
    if defaults.objectForKey_(key) is None:
        defaults.setObject_forKey_(DEFAULT_PREFERRED_POSITION, key)

    _on_main_thread(lambda: item.setAutosaveName_(AUTOSAVE_NAME))
    return True


def is_hidden_behind_notch(icon) -> bool:
    """True when the icon exists but sits under the camera housing, so nobody sees it."""
    if not available():
        return False
    button = _status_button(icon)
    window = button.window() if button is not None else None
    if window is None:
        return False
    screen = AppKit.NSScreen.mainScreen()
    if screen is None:
        return False
    try:
        left = screen.auxiliaryTopLeftArea()
        right = screen.auxiliaryTopRightArea()
    except AttributeError:
        return False
    if left is None or right is None:
        # No camera housing on this display, so nothing can hide behind it.
        return False

    frame = window.frame()
    item_left = frame.origin.x
    item_right = frame.origin.x + frame.size.width

    def fits(area) -> bool:
        return item_left >= area.origin.x and item_right <= area.origin.x + area.size.width

    return not (fits(left) or fits(right))
