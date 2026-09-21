from launcher import get_launcher

# base name only — launcher finds Claude.app / Claude Personal.app / etc.
AGENTS = {
    "claude": {
        "description": (
            "Complex multi-file reasoning, large codebase analysis, architectural "
            "refactors, subtle bug identification, shell-heavy or infra tasks, "
            "terminal-native workflows, code review requiring deep understanding"
        ),
        "app_candidates": ["Claude"],
        "web_url": "https://claude.ai",
        "site_key": "claude",
    },
    "chatgpt": {
        "description": (
            "General chat, research, writing, brainstorming, and everyday Q&A; "
            "also useful for background-style coding help and explanations"
        ),
        "app_candidates": ["ChatGPT"],
        "web_url": "https://chatgpt.com",
        "site_key": "chatgpt",
    },
    "cursor": {
        "description": (
            "Real-time pair programming, inline code completion, frontend and UI "
            "work, day-to-day feature writing, multi-file diffs with visual review, "
            "quick edits inside an existing project"
        ),
        "app_candidates": ["Cursor"],
        "web_url": "https://cursor.com",
        "site_key": "cursor",
    },
    "antigravity": {
        "description": (
            "Full autonomous end-to-end development, planning and executing "
            "multi-step tasks across files, browser-based verification, scheduling "
            "recurring tasks, parallel subagents, Google Cloud integration"
        ),
        "app_candidates": ["Antigravity"],
        # no antigravity install → gemini, not antigravity.google
        "web_url": "https://gemini.google.com",
        "site_key": "gemini",
    },
}

WEB_SITES = {
    "gemini": {
        "composer_selectors": [
            'div[contenteditable="true"]',
            "rich-textarea div[contenteditable='true']",
            '[aria-label*="Enter a prompt" i]',
            '[aria-label*="Prompt" i]',
        ],
        "send_selectors": [
            'button[aria-label="Send message"]',
            'button[aria-label*="Send" i]',
            'button[data-test-id="send-button"]',
        ],
    },
    "claude": {
        "composer_selectors": [
            'div[contenteditable="true"]',
            'div.ProseMirror[contenteditable="true"]',
            '[aria-label*="Write" i][contenteditable="true"]',
            "fieldset div[contenteditable='true']",
        ],
        "send_selectors": [
            'button[aria-label="Send message"]',
            'button[aria-label*="Send" i]',
            'button[type="submit"]',
        ],
    },
    "chatgpt": {
        "composer_selectors": [
            "#prompt-textarea",
            'div[contenteditable="true"]#prompt-textarea',
            'div[contenteditable="true"][id*="prompt"]',
            'textarea[name="prompt-textarea"]',
            'div[contenteditable="true"]',
        ],
        "send_selectors": [
            'button[data-testid="send-button"]',
            'button[aria-label*="Send" i]',
            'button#composer-submit-button',
        ],
    },
    "cursor": {
        "composer_selectors": [
            'div[contenteditable="true"]',
            "textarea",
            '[role="textbox"]',
        ],
        "send_selectors": [
            'button[aria-label*="Send" i]',
            'button[type="submit"]',
        ],
    },
}


def launch_agent(agent_name: str, task: str) -> None:
    if agent_name not in AGENTS:
        print(f"unknown agent: {agent_name}")
        return

    agent = AGENTS[agent_name]
    launcher = get_launcher()
    app_id = launcher.resolve_app(agent["app_candidates"])

    if app_id:
        print(f"opening {app_id}")
        launcher.open_desktop(app_id, task)
    else:
        print(f"no app, opening {agent['web_url']}")
        launcher.open_web(agent["web_url"], agent["site_key"], task)

    input("enter when done...")
