from __future__ import annotations

from pathlib import Path

PROFILE_DIR = Path.home() / ".jev-router" / "browser-profile"

# don't close these — otherwise chromium dies right after send
_ACTIVE_SESSIONS: list = []


def open_web_with_playwright(url: str, site_key: str, task: str) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("need playwright: pip install playwright && playwright install chromium")
        return False

    from agents import WEB_SITES

    site = WEB_SITES.get(site_key)
    if not site:
        print(f"no selectors for {site_key}")
        return False

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    composers = site["composer_selectors"]
    senders = site["send_selectors"]

    try:
        playwright = sync_playwright().start()
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        _ACTIVE_SESSIONS.append((playwright, context))

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2000)

        _click_new_chat(page)
        page.wait_for_timeout(1000)

        box = None
        for sel in composers:
            try:
                loc = page.locator(sel).first
                loc.wait_for(state="visible", timeout=3000)
                box = loc
                break
            except Exception:
                continue

        if box is None:
            print("no chat box — sign in and retry")
            return False

        box.click()
        try:
            box.fill("")
        except Exception:
            pass
        try:
            box.press("ControlOrMeta+a")
            page.wait_for_timeout(100)
        except Exception:
            pass
        box.type(task, delay=10)

        sent = False
        for sel in senders:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=1500):
                    btn.click()
                    sent = True
                    break
            except Exception:
                continue

        if not sent:
            try:
                box.press("Enter")
                sent = True
            except Exception:
                pass

        print("sent" if sent else "typed but send failed — check the tab")
        return sent
    except Exception as exc:
        print(f"playwright blew up: {exc}")
        return False


def _click_new_chat(page) -> None:
    for sel in (
        'button[aria-label*="New chat" i]',
        'button[aria-label*="New conversation" i]',
        'div[aria-label*="New chat" i]',
        'button:has-text("New chat")',
        'a:has-text("New chat")',
        '[data-testid="new-chat-button"]',
        'a[href*="/new"]',
    ):
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=800):
                loc.click()
                return
        except Exception:
            continue
