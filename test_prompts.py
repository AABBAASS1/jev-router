from __future__ import annotations

import argparse
import sys

from agents import AGENTS, launch_agent
from router import ask_jev

# (prompt, soft expected agent — mismatch is ok, just logged)
PROMPTS = [
    (
        "Refactor this React component to use TypeScript and fix the layout bugs "
        "in the sidebar — I want to pair on it live in the editor.",
        "cursor",
    ),
    (
        "Write a detailed architecture decision record comparing event sourcing "
        "vs CRUD for our order system, with trade-offs and a recommendation.",
        "chatgpt",
    ),
    (
        "Trace a subtle race condition across three Python services and propose "
        "a fix with tests — deep multi-file reasoning.",
        "claude",
    ),
    (
        "Autonomously plan and execute an end-to-end feature: scaffold the API, "
        "wire the UI, run browser checks, and open a PR when done.",
        "antigravity",
    ),
    (
        "Explain skincare ingredients for dry skin in plain language and suggest "
        "three drugstore products.",
        "chatgpt",
    ),
]


def run_routing_tests(*, launch: bool = False) -> int:
    print(f"{len(PROMPTS)} prompts\n")
    results = []
    failures = 0

    for i, (prompt, hint) in enumerate(PROMPTS, start=1):
        short = prompt[:80] + ("…" if len(prompt) > 80 else "")
        print(f"[{i}/{len(PROMPTS)}] {short}")
        try:
            agent, confidence, approval = ask_jev(prompt)
        except Exception as exc:
            print(f"  fail: {exc}\n")
            failures += 1
            results.append((i, prompt, None, None, False))
            continue

        ok = agent in AGENTS
        if not ok:
            print(f"  fail: weird agent {agent!r}")
            failures += 1
        else:
            note = "" if agent == hint else f" (hint was {hint})"
            print(f"  → {agent}  {confidence:.0%}  approval={approval:.0%}{note}")

        results.append((i, prompt, agent, confidence, ok))

        if launch and ok:
            print(f"  launching {agent}")
            launch_agent(agent, prompt)
        print()

    print("---")
    for i, prompt, agent, confidence, ok in results:
        tag = "ok" if ok else "fail"
        a = agent or "?"
        c = f"{confidence:.0%}" if confidence is not None else "-"
        print(f"  {tag}  #{i} {a:12} {c:>4}  {prompt[:48]}…")

    print(f"\n{len(results) - failures}/{len(results)} ok")
    # hints are soft; only API / unknown agent counts as fail
    return 1 if failures else 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--launch", action="store_true", help="actually open agents")
    args = p.parse_args()
    sys.exit(run_routing_tests(launch=args.launch))


if __name__ == "__main__":
    main()
