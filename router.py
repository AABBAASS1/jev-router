import os
from typesafe_sdk import Choice, Noul, TypeSafeClient
from dotenv import load_dotenv
from agents import AGENTS, launch_agent

load_dotenv("secrets.env")
os.environ["TYPESAFE_API_KEY"] = os.getenv("JEV_API_KEY")

client = TypeSafeClient()


def ask_jev(task):
    response = client.system_one(
        state=f"Task: {task}",
        questions={
            "agent": Choice(
                instructions="Which AI agent should handle this task?",
                criteria={
                    name: data["description"] for name, data in AGENTS.items()
                },
            ),
            "needs_approval": Noul(
                instructions="Does this task need user approval before running?"
            ),
        },
    )
    return (
        response.answers["agent"].choice,
        response.answers["agent"].confidence,
        response.answers["needs_approval"].noul,
    )


def route(task):
    print(f"\ntask: {task}")
    print("asking jev...")
    agent, confidence, approval = ask_jev(task)
    print(f"agent: {agent} ({confidence:.0%})")
    if approval > 0.7:
        confirm = input(f"needs approval ({approval:.0%}). go? (y/n): ")
        if confirm.lower() != "y":
            print("cancelled")
            return
    launch_agent(agent, task)


if __name__ == "__main__":
    task = input("task: ")
    route(task)
