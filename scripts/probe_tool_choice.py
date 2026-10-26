"""Measure how often a forced tool_choice is honored, per model (it can be intermittent).

    uv run python scripts/probe_tool_choice.py 10 moonshotai/Kimi-K3 openai/gpt-oss-120b
"""
import sys

from nebius_agent.llm import NEBIUS_BASE_URL, make_chat_model

WEATHER = {"name": "get_weather", "description": "Get the current weather for a city.",
           "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}
TIME = {"name": "get_time", "description": "Get the current local time in a city.",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}

runs = int(sys.argv[1])
print(f"endpoint: {NEBIUS_BASE_URL}  prompt: 'Hi there!'  runs per mode: {runs}\n")
for model in sys.argv[2:]:
    llm = make_chat_model(model, max_tokens=256)
    for label, choice in [("named tool_choice=get_time", "get_time"), ('tool_choice="any" (required)', "any")]:
        bound = llm.bind_tools([WEATHER, TIME], tool_choice=choice)
        ok = sum(1 for _ in range(runs) if bound.invoke("Hi there!").tool_calls)
        print(f"{model:40s} {label:32s} honored {ok}/{runs}")
