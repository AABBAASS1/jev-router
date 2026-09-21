from __future__ import annotations

import platform
import subprocess


def copy_text(text: str) -> None:
    system = platform.system()
    if system == "Darwin":
        subprocess.run("pbcopy", text=True, input=text, check=False)
        return
    if system == "Windows":
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
            input=text,
            text=True,
            check=False,
        )
        return
    for cmd in (
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ):
        try:
            subprocess.run(cmd, input=text, text=True, check=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    print("no clipboard tool (wl-copy / xclip / xsel)")
