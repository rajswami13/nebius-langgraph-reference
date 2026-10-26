"""Measure how often a forced tool_choice is honored, per model (it can be intermittent).

A run counts as honored only if the response contains well-formed tool calls and they
satisfy the request: for a named tool, every call is to that tool; for "any", at least
one call to an offered tool. Wrong-tool and malformed responses are reported separately.

    uv run python scripts/probe_tool_choice.py 10 moonshotai/Kimi-K3 openai/gpt-oss-120b
"""
import sys
from collections import Counter

from nebius_agent.llm import NEBIUS_BASE_URL, make_chat_model

WEATHER = {"name": "get_weather", "description": "Get the current weather for a city.",
           "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}
TIME = {"name": "get_time", "description": "Get the current local time in a city.",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}
OFFERED = {WEATHER["name"], TIME["name"]}


def classify(msg, choice: str) -> str:
    if msg.invalid_tool_calls:
        return "malformed"
    names = [tc["name"] for tc in msg.tool_calls]
    if not names:
        return "no call"
    if choice == "any":
        return "honored" if set(names) <= OFFERED else "wrong tool"
    return "honored" if all(n == choice for n in names) else "wrong tool"


runs = int(sys.argv[1])
print(f"endpoint: {NEBIUS_BASE_URL}  prompt: 'Hi there!'  runs per mode: {runs}\n")
for model in sys.argv[2:]:
    llm = make_chat_model(model, max_tokens=256)
    for label, choice in [("named tool_choice=get_time", "get_time"), ('tool_choice="any" (required)', "any")]:
        bound = llm.bind_tools([WEATHER, TIME], tool_choice=choice)
        outcomes = Counter(classify(bound.invoke("Hi there!"), choice) for _ in range(runs))
        other = ", ".join(f"{k} {v}" for k, v in sorted(outcomes.items()) if k != "honored")
        print(f"{model:40s} {label:32s} honored {outcomes['honored']}/{runs}" + (f"  ({other})" if other else ""))
