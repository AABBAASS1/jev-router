from __future__ import annotations

import platform

from .base import Launcher


def get_launcher() -> Launcher:
    system = platform.system()
    if system == "Darwin":
        from .mac import MacLauncher

        return MacLauncher()
    if system == "Windows":
        from .windows import WindowsLauncher

        return WindowsLauncher()
    if system == "Linux":
        from .linux import LinuxLauncher

        return LinuxLauncher()

    raise NotImplementedError(f"no launcher for {system}")
