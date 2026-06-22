"""Move application windows onto the primary monitor."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
GW_OWNER = 4
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
MONITORINFOF_PRIMARY = 1
WINDOWPLACEMENT_SIZE = 44
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


@dataclass(frozen=True)
class OffScreenWindow:
    hwnd: int
    title: str
    process_name: str

    @property
    def label(self) -> str:
        if self.process_name:
            return f"{self.process_name} — {self.title}"
        return self.title


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("showCmd", ctypes.c_uint),
        ("ptMinPosition", POINT),
        ("ptMaxPosition", POINT),
        ("rcNormalPosition", RECT),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
MONITORENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(RECT),
    wintypes.LPARAM,
)


@dataclass(frozen=True)
class MonitorArea:
    left: int
    top: int
    right: int
    bottom: int

    def intersects(self, other: MonitorArea) -> bool:
        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.bottom <= other.top
            or self.top >= other.bottom
        )

    def clamp_position(self, left: int, top: int, width: int, height: int) -> tuple[int, int]:
        max_left = max(self.left, self.right - width)
        max_top = max(self.top, self.bottom - height)
        clamped_left = max(self.left, min(left, max_left))
        clamped_top = max(self.top, min(top, max_top))
        return int(clamped_left), int(clamped_top)


def _rect_to_area(rect: RECT) -> MonitorArea:
    return MonitorArea(rect.left, rect.top, rect.right, rect.bottom)


def _get_primary_monitor() -> tuple[MonitorArea, MonitorArea]:
    primary_bounds: MonitorArea | None = None
    primary_work: MonitorArea | None = None

    @MONITORENUMPROC
    def callback(hmonitor, _hdc, _rect, _lparam):
        nonlocal primary_bounds, primary_work
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            if info.dwFlags & MONITORINFOF_PRIMARY:
                primary_bounds = _rect_to_area(info.rcMonitor)
                primary_work = _rect_to_area(info.rcWork)
        return True

    user32.EnumDisplayMonitors(0, 0, callback, 0)
    if primary_bounds is None or primary_work is None:
        raise RuntimeError("Primary monitor not found.")
    return primary_bounds, primary_work


def _get_window_title(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    title = buffer.value.strip()
    return title or "(untitled window)"


def _is_application_window(hwnd: int) -> bool:
    if not user32.IsWindowVisible(hwnd):
        return False

    if hwnd == user32.GetShellWindow():
        return False

    if user32.GetWindow(hwnd, GW_OWNER):
        return False

    title_length = user32.GetWindowTextLengthW(hwnd)
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    is_app_window = bool(ex_style & WS_EX_APPWINDOW)
    is_tool_window = bool(ex_style & WS_EX_TOOLWINDOW)

    if title_length <= 0 and not is_app_window:
        return False

    if is_tool_window and not is_app_window:
        return False

    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False

    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        return False

    return True


def _move_window(hwnd: int, left: int, top: int, width: int, height: int) -> None:
    if user32.IsIconic(hwnd):
        placement = WINDOWPLACEMENT()
        placement.length = WINDOWPLACEMENT_SIZE
        if user32.GetWindowPlacement(hwnd, ctypes.byref(placement)):
            placement.rcNormalPosition.left = left
            placement.rcNormalPosition.top = top
            placement.rcNormalPosition.right = left + width
            placement.rcNormalPosition.bottom = top + height
            user32.SetWindowPlacement(hwnd, ctypes.byref(placement))
        return

    flags = SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
    user32.SetWindowPos(hwnd, 0, left, top, 0, 0, flags)


def _get_process_name(hwnd: int) -> str:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""

    try:
        buffer = ctypes.create_unicode_buffer(260)
        size = wintypes.DWORD(len(buffer))
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return os.path.basename(buffer.value)
    finally:
        kernel32.CloseHandle(handle)
    return ""


def _is_off_screen(hwnd: int, primary_bounds: MonitorArea) -> bool:
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False
    return not primary_bounds.intersects(_rect_to_area(rect))


def list_off_screen_windows() -> list[OffScreenWindow]:
    """Return application windows that are not within the primary monitor."""
    primary_bounds, _work_area = _get_primary_monitor()
    windows: list[OffScreenWindow] = []

    @WNDENUMPROC
    def callback(hwnd, _lparam):
        if not _is_application_window(hwnd):
            return True
        if not _is_off_screen(hwnd, primary_bounds):
            return True

        windows.append(
            OffScreenWindow(
                hwnd=hwnd,
                title=_get_window_title(hwnd),
                process_name=_get_process_name(hwnd),
            )
        )
        return True

    user32.EnumWindows(callback, 0)
    windows.sort(key=lambda item: item.label.casefold())
    return windows


def _move_single_window(
    hwnd: int,
    work_area: MonitorArea,
    offset: int,
) -> str | None:
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None

    width = rect.right - rect.left
    height = rect.bottom - rect.top
    target_left = work_area.left + offset
    target_top = work_area.top + offset
    left, top = work_area.clamp_position(target_left, target_top, width, height)

    _move_window(hwnd, left, top, width, height)
    return _get_window_title(hwnd)


def move_windows(hwnds: list[int]) -> list[str]:
    """Move the given windows onto screen 1."""
    _primary_bounds, work_area = _get_primary_monitor()
    moved_titles: list[str] = []
    offset = 0
    offset_step = 30

    for hwnd in hwnds:
        title = _move_single_window(hwnd, work_area, offset)
        if title is not None:
            moved_titles.append(title)
            offset += offset_step

    return moved_titles


def move_windows_to_screen1() -> list[str]:
    """Move all windows outside the primary monitor onto screen 1."""
    windows = list_off_screen_windows()
    return move_windows([window.hwnd for window in windows])
