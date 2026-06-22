"""Display mode switching via Windows DisplaySwitch.exe."""

import os
import subprocess


def _displayswitch_path() -> str:
    return os.path.join(os.environ["SystemRoot"], "System32", "DisplaySwitch.exe")


def set_first_screen_only() -> None:
    """Show desktop on the primary monitor only."""
    subprocess.run([_displayswitch_path(), "/internal"], check=True)


def set_extend() -> None:
    """Extend desktop across all connected monitors."""
    subprocess.run([_displayswitch_path(), "/extend"], check=True)
