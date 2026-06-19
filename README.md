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
