from __future__ import annotations

import base64
import json
import subprocess
import time
from pathlib import Path


class MacLauncher:
    def resolve_app(self, candidates: list[str]) -> str | None:
        roots = [Path("/Applications"), Path.home() / "Applications"]
        for prefix in candidates:
            for root in roots:
                if not root.is_dir():
                    continue
                exact = root / f"{prefix}.app"
                if exact.is_dir():
                    return prefix
                matches = sorted(
                    (
                        p.stem
                        for p in root.glob(f"{prefix}*.app")
                        if p.is_dir() and self._is_app_variant(p.stem, prefix)
                    ),
                    key=str.casefold,
                )
                if matches:
                    return matches[0]
        return None

    @staticmethod
    def _is_app_variant(stem: str, prefix: str) -> bool:
        # allow "Claude Work", skip "Claude Code URL Handler"
        if stem.casefold() == prefix.casefold():
            return True
        if not stem.casefold().startswith(prefix.casefold()):
            return False
        rest = stem[len(prefix) :]
        if not rest.startswith(" ") and not rest.startswith("-"):
            return False
        return len(rest.strip().replace("-", " ").split()) == 1

    def open_desktop(self, app_id: str, task: str) -> None:
        subprocess.run(["open", "-a", app_id], check=False)
        time.sleep(3)
        print("new chat...")
        self._start_new_chat(app_id)
        time.sleep(1.5)
        if self._try_type_into_app(app_id, task):
            return
        if self._try_paste_into_app(app_id, task):
            print("pasted")
            return
        self._copy_task(task)
        print("couldn't type — enable Accessibility for Terminal, or cmd+v")

    def _start_new_chat(self, app_name: str) -> None:
        process = self._process_name(app_name)
        script = f'''
        tell application "{app_name}" to activate
        delay 0.8
        tell application "System Events"
            tell process "{process}"
                keystroke "n" using command down
            end tell
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        if result.returncode != 0 and process != app_name:
            # process name sometimes == bundle name
            script2 = script.replace(
                f'tell process "{process}"', f'tell process "{app_name}"'
            )
            result = subprocess.run(
                ["osascript", "-e", script2], capture_output=True, text=True
            )
        if result.returncode != 0:
            print("cmd+n failed, continuing anyway")

    @staticmethod
    def _process_name(app_name: str) -> str:
        # "Claude Personal.app" still shows up as process "Claude"
        for brand in ("Claude", "ChatGPT", "Cursor", "Antigravity"):
            if app_name == brand or app_name.startswith(brand + " "):
                return brand
        return app_name

    def open_web(self, url: str, site_key: str, task: str) -> None:
        subprocess.run(["open", "-a", "Safari", url], check=False)
        time.sleep(4)

        if self._submit_via_safari_js(site_key, task):
            print("sent")
            return

        print("safari js failed — need Develop → Allow JavaScript from Apple Events")
        if self._try_paste_into_safari(task):
            print("pasted")
            return

        print("trying playwright...")
        from .web_playwright import open_web_with_playwright

        if open_web_with_playwright(url, site_key, task):
            return

        self._copy_task(task)
        print(f"opened {url} — cmd+v to paste")

    def _try_type_into_app(self, app_name: str, task: str) -> bool:
        safe = self._escape_applescript_string(task)
        process = self._process_name(app_name)
        script = f'''
        tell application "{app_name}" to activate
        delay 1
        tell application "System Events"
            tell process "{process}"
                keystroke "{safe}"
                delay 0.5
                keystroke return
            end tell
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        if result.returncode != 0:
            return False
        print("sent")
        return True

    def _try_paste_into_app(self, app_name: str, task: str) -> bool:
        self._copy_task(task, quiet=True)
        process = self._process_name(app_name)
        script = f'''
        tell application "{app_name}" to activate
        delay 0.5
        tell application "System Events"
            tell process "{process}"
                keystroke "v" using command down
                delay 0.3
                keystroke return
            end tell
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        return result.returncode == 0

    def _submit_via_safari_js(self, site_key: str, task: str) -> bool:
        from agents import WEB_SITES

        site = WEB_SITES.get(site_key)
        if not site:
            print(f"no selectors for {site_key}")
            return False

        ready = self._run_safari_js(
            "document.readyState === 'complete' ? '1' : '0'"
        )
        if ready is None:
            return False
        for _ in range(19):
            if ready.strip().strip('"') == "1":
                break
            time.sleep(0.5)
            ready = self._run_safari_js(
                "document.readyState === 'complete' ? '1' : '0'"
            )
            if ready is None:
                return False

        composers = json.dumps(site["composer_selectors"])
        senders = json.dumps(site["send_selectors"])
        task_json = json.dumps(task)

        # insertText > setting .value — react/quill ignore the latter
        js = f"""
        (function() {{
          var composers = {composers};
          var senders = {senders};
          var text = {task_json};

          function find(sels) {{
            for (var i = 0; i < sels.length; i++) {{
              var el = document.querySelector(sels[i]);
              if (el) return el;
            }}
            return null;
          }}

          var box = find(composers);
          if (!box) return 'NO_COMPOSER';

          box.focus();
          try {{
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, text);
          }} catch (e) {{}}

          if (box.tagName === 'TEXTAREA' || box.tagName === 'INPUT') {{
            var proto = box.tagName === 'TEXTAREA'
              ? window.HTMLTextAreaElement.prototype
              : window.HTMLInputElement.prototype;
            var desc = Object.getOwnPropertyDescriptor(proto, 'value');
            if (desc && desc.set) desc.set.call(box, text);
            else box.value = text;
            box.dispatchEvent(new Event('input', {{ bubbles: true }}));
            box.dispatchEvent(new Event('change', {{ bubbles: true }}));
          }} else if (!(box.textContent || '').trim()) {{
            box.textContent = text;
            box.dispatchEvent(new InputEvent('input', {{ bubbles: true, data: text }}));
          }}

          var btn = find(senders);
          if (btn) {{
            btn.click();
            return 'OK';
          }}
          box.dispatchEvent(new KeyboardEvent('keydown', {{
            key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
          }}));
          return 'OK_ENTER';
        }})();
        """

        for attempt in range(12):
            result = self._run_safari_js(js)
            if result is None:
                return False
            cleaned = result.strip().strip('"')
            if cleaned in ("OK", "OK_ENTER"):
                return True
            if cleaned == "NO_COMPOSER" and attempt < 11:
                time.sleep(1)
                continue
            if cleaned == "NO_COMPOSER":
                print("no chat box — sign in and retry")
                return False
            print(f"safari js: {cleaned}")
            return cleaned.startswith("OK")
        return False

    def _run_safari_js(self, javascript: str) -> str | None:
        # base64 so we don't fight applescript string escaping
        b64 = base64.b64encode(javascript.encode("utf-8")).decode("ascii")
        script = f'''
        set jsB64 to "{b64}"
        set jsText to do shell script "echo " & quoted form of jsB64 & " | base64 -D"
        tell application "Safari"
            if (count of documents) is 0 then return "NO_DOC"
            set pageResult to do JavaScript jsText in document 1
            try
                return pageResult as text
            on error
                return "OK"
            end try
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        if result.returncode != 0:
            err = result.stderr.strip()
            if "Allow JavaScript from Apple Events" in err:
                print("turn on: Safari → Develop → Allow JavaScript from Apple Events")
            elif err:
                print(f"safari: {err}")
            return None
        return result.stdout

    def _try_paste_into_safari(self, task: str) -> bool:
        self._copy_task(task, quiet=True)
        script = '''
        tell application "Safari" to activate
        delay 0.8
        tell application "System Events"
            tell process "Safari"
                keystroke "v" using command down
                delay 0.4
                keystroke return
            end tell
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        return result.returncode == 0

    @staticmethod
    def _copy_task(task: str, quiet: bool = False) -> None:
        subprocess.run("pbcopy", text=True, input=task, check=False)
        if not quiet:
            print("copied — cmd+v")

    @staticmethod
    def _escape_applescript_string(text: str) -> str:
        return text.replace("\\", "\\\\").replace('"', '\\"')
