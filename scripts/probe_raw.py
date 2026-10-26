"""Baseline: does the model emit a well-formed tool call via the raw OpenAI SDK?

Run this before blaming a framework. If the raw call fails, the issue is the
model/endpoint; if it passes but the framework fails, the issue is the adapter.
"""
import json
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

from nebius_agent.llm import NEBIUS_BASE_URL
import os

load_dotenv()
client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=os.environ["NEBIUS_API_KEY"])

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]

for model in sys.argv[1:]:
    t0 = time.time()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "What's the weather in Amsterdam?"}],
            tools=TOOLS,
            max_tokens=512,
            timeout=60,
        )
        calls = r.choices[0].message.tool_calls or []
        if calls:
            args = json.loads(calls[0].function.arguments)
            status = f"OK   {calls[0].function.name}({args})"
        else:
            status = f"NO-TOOL-CALL finish={r.choices[0].finish_reason} content={(r.choices[0].message.content or '')[:60]!r}"
    except Exception as e:
        status = f"ERR  {type(e).__name__}: {str(e)[:100]}"
    print(f"{model:45s} {time.time()-t0:5.1f}s  {status}", flush=True)
