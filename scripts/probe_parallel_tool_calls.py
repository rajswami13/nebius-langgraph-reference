"""Check whether parallel_tool_calls=False is honored, per model, on the raw OpenAI API.

The question needs three dependent tools (price -> calculate -> convert). A model that
honors parallel_tool_calls=False returns at most one tool call per turn. A clean run
only means no violation was observed; it does not prove the parameter is enforced.

    uv run python scripts/probe_parallel_tool_calls.py 3 Qwen/Qwen3-235B-A22B-Instruct-2507 zai-org/GLM-5.3
"""
import sys

from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI

from nebius_agent.llm import NEBIUS_BASE_URL, make_chat_model
from nebius_agent.tools import calculate, get_gpu_price


@tool
def convert_currency(amount_usd: float, currency: str) -> str:
    """Convert a USD amount to EUR or GBP using mock exchange rates."""
    return ""


TOOLS = [convert_to_openai_tool(t) for t in (get_gpu_price, calculate, convert_currency)]
MESSAGES = [
    {"role": "system", "content": "Always use get_gpu_price to look up prices and calculate for any arithmetic; never guess numbers."},
    {"role": "user", "content": "How much would 8 H200s for 72 hours cost in euros?"},
]

client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=make_chat_model().openai_api_key.get_secret_value())
runs = int(sys.argv[1])
print(f"endpoint: {NEBIUS_BASE_URL}  runs per model: {runs}\n")
for model in sys.argv[2:]:
    counts = [
        len(client.chat.completions.create(
            model=model, messages=MESSAGES, tools=TOOLS, parallel_tool_calls=False, max_tokens=400,
        ).choices[0].message.tool_calls or [])
        for _ in range(runs)
    ]
    verdict = f"not violated in {runs} runs" if max(counts) <= 1 else "IGNORED"
    print(f"{model:40s} parallel_tool_calls=False -> tool calls per turn {counts}  {verdict}")
