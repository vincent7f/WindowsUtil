# WindowsUtil

Small Windows utilities for common desktop tasks.

## Display Mode Scripts

These batch files switch your multi-monitor display mode using the built-in Windows tool `DisplaySwitch.exe`. No extra software is required.

| Script | Display mode | Windows setting |
|--------|--------------|-----------------|
| [`display-first-screen-only.bat`](display-first-screen-only.bat) | Primary monitor only | **PC screen only** |
| [`display-extend.bat`](display-extend.bat) | Extended desktop | **Extend** |

### Usage

1. Connect your monitors or external display as usual.
2. Double-click the script you want, or run it from a terminal:

```bat
display-first-screen-only.bat
```

```bat
display-extend.bat
```

The display mode should change immediately. If it does not, open **Settings → System → Display** and confirm the mode there.

### Notes

- **First screen** means the **primary monitor** set in Windows display settings. If the wrong monitor stays on, change the primary display in **Settings → System → Display** first.
- `display-first-screen-only.bat` turns off output to secondary displays and keeps the desktop on the primary monitor only.
- `display-extend.bat` spreads the desktop across all connected displays so you can move windows between screens.
- Both scripts require Windows 7 or later.

## Move Windows to Screen 1

[`move-windows-to-screen1.bat`](move-windows-to-screen1.bat) finds application windows that are **not within the primary monitor (screen 1)** and moves them onto it.

This is useful when:

- A window opened on a secondary monitor and you want it on the main screen
- A monitor was disconnected and windows were left at off-screen coordinates

### Usage

Double-click the script, or run it from a terminal:

```bat
move-windows-to-screen1.bat
```

The script prints the title of each moved window and a summary count when finished.

### Notes

- **Screen 1** is the **primary monitor** set in Windows display settings (same as the display mode scripts above).
- Only normal application windows are moved; system windows, tool windows, and child dialogs are skipped.
- Windows are placed inside the primary monitor's working area (above the taskbar).
- Multiple moved windows are offset slightly so they do not stack on the exact same spot.
- Requires Windows PowerShell (included with Windows 7 and later).
