from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from .clipboard import copy_text
from .web_playwright import open_web_with_playwright


class LinuxLauncher:
    def resolve_app(self, candidates: list[str]) -> str | None:
        for prefix in candidates:
            hit = self._find_app(prefix)
            if hit:
                return hit
        return None

    def open_desktop(self, app_id: str, task: str) -> None:
        if app_id.endswith(".desktop"):
            subprocess.Popen(
                ["gtk-launch", Path(app_id).stem],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                [app_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        time.sleep(3)
        print("new chat...")
        self._xdotool_keys("ctrl+n")
        time.sleep(1.5)
        copy_text(task)
        self._xdotool_keys("ctrl+v")
        time.sleep(0.4)
        self._xdotool_keys("Return")
        if shutil.which("xdotool"):
            print("sent")
        else:
            print("copied — install xdotool or ctrl+v")

    def open_web(self, url: str, site_key: str, task: str) -> None:
        if open_web_with_playwright(url, site_key, task):
            return
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        copy_text(task)
        print(f"opened {url} — ctrl+v to paste")

    def _find_app(self, prefix: str) -> str | None:
        for name in (prefix, prefix.lower(), prefix.replace(" ", "-").lower()):
            path = shutil.which(name)
            if path:
                return path

        desktop_dirs = [
            Path("/usr/share/applications"),
            Path("/usr/local/share/applications"),
            Path.home() / ".local" / "share" / "applications",
        ]
        matches: list[Path] = []
        for root in desktop_dirs:
            if not root.is_dir():
                continue
            for path in root.glob("*.desktop"):
                if self._name_matches(path.stem, prefix) or self._desktop_name_matches(
                    path, prefix
                ):
                    matches.append(path)

        if matches:
            return str(sorted(matches, key=lambda p: p.name.casefold())[0])

        for root in (Path("/opt"), Path.home() / ".local" / "bin"):
            if not root.is_dir():
                continue
            for path in root.rglob(prefix):
                if path.is_file() and os.access(path, os.X_OK):
                    return str(path)
            for path in root.rglob(prefix.lower()):
                if path.is_file() and os.access(path, os.X_OK):
                    return str(path)
        return None

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
        if rest[0] not in " -_.":
            return False
        return len(rest.strip(" .-_").replace("-", " ").split()) <= 1

    @staticmethod
    def _desktop_name_matches(path: Path, prefix: str) -> bool:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return False
        for line in text.splitlines():
            if line.startswith("Name="):
                return LinuxLauncher._name_matches(line.split("=", 1)[1].strip(), prefix)
        return False

    @staticmethod
    def _xdotool_keys(keys: str) -> None:
        if not shutil.which("xdotool"):
            return
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", keys],
            capture_output=True,
            check=False,
        )
