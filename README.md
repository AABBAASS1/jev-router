# Jev Router

CLI that asks Jev which agent should handle a task, then opens that app (or the website) and dumps the prompt in.

Mac / Windows / Linux. Agent catalog is OS-agnostic; `launcher/` has the platform bits.

## Agents

| key | app | web if missing |
|-----|-----|----------------|
| claude | Claude | claude.ai |
| chatgpt | ChatGPT | chatgpt.com |
| cursor | Cursor | cursor.com |
| antigravity | Antigravity | gemini.google.com |

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

`secrets.env`:

```
JEV_API_KEY=...
```

**Mac:** Safari → Develop → Allow JavaScript from Apple Events. Accessibility for Terminal if you want desktop auto-type.

**Win/Linux:** Playwright profile lives at `~/.jev-router/browser-profile` (sign in once). Linux desktop paste wants `xdotool`.

## Run

```bash
python router.py
python test_prompts.py          # routing smoke
python test_prompts.py --launch # also open agents
```

Flow: Jev picks agent → optional approval if noul > 0.7 → open app (new chat + send) or web → enter when done.
