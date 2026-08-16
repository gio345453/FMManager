import ctypes
from ctypes import wintypes
import os
import sys


_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Icon", "Icona.ico")
_DWMWA_USE_IMMERSIVE_DARK_MODE = (20, 19)
_DWMWA_BORDER_COLOR = 34
_DWMWA_CAPTION_COLOR = 35
_DWMWA_TEXT_COLOR = 36
_BLACK = 0x000000
_WHITE = 0xFFFFFF


_DARK_MODE_ENABLED = 1
_SET_WINDOW_POS_FLAGS = 0x0020 | 0x0002 | 0x0001 | 0x0004 | 0x0010


def enable_windows_dark_mode():
    if not sys.platform.startswith("win"):
        return

    try:
        uxtheme = ctypes.WinDLL("uxtheme")
        set_preferred_app_mode = uxtheme[135]
        set_preferred_app_mode.argtypes = (ctypes.c_int,)
        set_preferred_app_mode.restype = ctypes.c_int
        set_preferred_app_mode(2)

        flush_menu_themes = uxtheme[136]
        flush_menu_themes.argtypes = ()
        flush_menu_themes.restype = None
        flush_menu_themes()
    except Exception:
        pass


def configure_application_window(window):
    """Applica icona e chrome Windows alle finestre applicative decorate."""
    try:
        window.wm_iconbitmap(_ICON_PATH)
    except Exception:
        pass

    if sys.platform.startswith("win"):
        window.after_idle(lambda: _apply_windows_chrome(window))


def _apply_windows_chrome(window):
    try:
        window.update_idletasks()
        hwnd = wintypes.HWND(window.winfo_id())
        user32 = ctypes.windll.user32
        user32.GetAncestor.argtypes = (wintypes.HWND, ctypes.c_uint)
        user32.GetAncestor.restype = wintypes.HWND
        root_hwnd = user32.GetAncestor(hwnd, 2)
        hwnd = wintypes.HWND(root_hwnd or hwnd)
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = (
            wintypes.HWND,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        )
        dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long
    except Exception:
        return

    _set_dwm_attribute(dwmapi, hwnd, _DWMWA_USE_IMMERSIVE_DARK_MODE[0], 1)
    _set_dwm_attribute(dwmapi, hwnd, _DWMWA_USE_IMMERSIVE_DARK_MODE[1], 1)
    _set_dwm_attribute(dwmapi, hwnd, _DWMWA_BORDER_COLOR, _BLACK)
    _set_dwm_attribute(dwmapi, hwnd, _DWMWA_CAPTION_COLOR, _BLACK)
    _set_dwm_attribute(dwmapi, hwnd, _DWMWA_TEXT_COLOR, _WHITE)
    _refresh_window_frame(hwnd)


def _refresh_window_frame(hwnd):
    try:
        user32 = ctypes.windll.user32
        user32.SetWindowPos.argtypes = (
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        )
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            _SET_WINDOW_POS_FLAGS,
        )
    except Exception:
        pass


def _set_dwm_attribute(dwmapi, hwnd, attribute, value):
    try:
        value_ref = ctypes.c_uint(value)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            attribute,
            ctypes.byref(value_ref),
            ctypes.sizeof(value_ref)
        )
    except Exception:
        pass
