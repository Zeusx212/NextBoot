"""
Elevation helper module for NextBoot.
Checks for administrator privileges and provides UAC elevation.
"""

import sys
import os
import ctypes

def is_admin() -> bool:
    """Check if the current process has administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def elevate_process(args=None) -> bool:
    """
    Relaunches the current script with Administrator privileges using Windows UAC 'runas'.
    Returns True if ShellExecute was successfully dispatched, False if user cancelled or error.
    """
    if is_admin():
        return True

    try:
        # Determine script or executable
        if getattr(sys, 'frozen', False):
            # Running as compiled PyInstaller executable
            executable = sys.executable
            parameters = " ".join(f'"{a}"' for a in (args or sys.argv[1:]))
        else:
            # Running as Python script
            executable = sys.executable
            script = os.path.abspath(sys.argv[0])
            extra_args = args or sys.argv[1:]
            param_list = [f'"{script}"'] + [f'"{a}"' for a in extra_args]
            parameters = " ".join(param_list)

        # 1 = SW_SHOWNORMAL
        hinstance = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            parameters,
            None,
            1
        )
        # ShellExecute returns > 32 on success
        return hinstance > 32
    except Exception as e:
        print(f"Elevation request failed: {e}")
        return False
