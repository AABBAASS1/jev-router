from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .clipboard import copy_text
from .web_playwright import open_web_with_playwright


class WindowsLauncher:
    def resolve_app(self, candidates: list[str]) -> str | None:
        for prefix in candidates:
            hit = self._find_exe(prefix)
            if hit:
                return str(hit)
        return None

    def open_desktop(self, app_id: str, task: str) -> None:
        path = Path(app_id)
        if path.is_file():
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen([app_id], shell=False)
        time.sleep(3)
        print("new chat...")
        self._send_keys("^n")
        time.sleep(1.5)
        copy_text(task)
        self._send_keys("^v")
        time.sleep(0.4)
        self._send_keys("{ENTER}")
        print("sent (hope the window was focused)")

    def open_web(self, url: str, site_key: str, task: str) -> None:
        if open_web_with_playwright(url, site_key, task):
            return
        os.startfile(url)  # type: ignore[attr-defined]
        copy_text(task)
        print(f"opened {url} — ctrl+v to paste")

    def _find_exe(self, prefix: str) -> Path | None:
        home = Path.home()
        local = Path(os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local")))
        roaming = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
        pf = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        pf86 = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))

        search_roots = [
            local / "Programs",
            local,
            roaming,
            pf,
            pf86,
            home / "AppData" / "Local" / "Programs",
        ]

        exact_guesses = [
            local / "Programs" / prefix / f"{prefix}.exe",
            local / "Programs" / prefix.lower() / f"{prefix}.exe",
            local / f"Anthropic{prefix}" / f"{prefix.lower()}.exe",
            local / "AnthropicClaude" / "claude.exe",
            local / "Programs" / "cursor" / "Cursor.exe",
            local / "Programs" / "ChatGPT" / "ChatGPT.exe",
        ]
        for guess in exact_guesses:
            if guess.is_file() and self._name_matches(guess.stem, prefix):
                return guess

        matches: list[Path] = []
        for root in search_roots:
            if not root.is_dir():
                continue
            try:
                for path in root.rglob(f"{prefix}*.exe"):
                    if path.is_file() and self._name_matches(path.stem, prefix):
                        matches.append(path)
                for path in root.rglob(f"{prefix.lower()}*.exe"):
                    if path.is_file() and self._name_matches(path.stem, prefix):
                        matches.append(path)
            except (PermissionError, OSError):
                continue

        if not matches:
            return None
        matches = sorted(set(matches), key=lambda p: (len(p.parts), str(p).casefold()))
        return matches[0]

    @staticmethod
    def _name_matches(stem: str, prefix: str) -> bool:
        s, p = stem.casefold(), prefix.casefold()
        if s == p:
            return True
        if not s.startswith(p):
            return False
        rest = stem[len(prefix) :]
        if not rest:
            return True
        if not (rest.startswith(" ") or rest.startswith("-") or rest.startswith("_")):
            return False
        return len(rest.strip().replace("-", " ").replace("_", " ").split()) <= 1

    @staticmethod
    def _send_keys(keys: str) -> None:
        safe = keys.replace("'", "''")  # powershell single-quote escape
        script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            f"[System.Windows.Forms.SendKeys]::SendWait('{safe}')"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )
