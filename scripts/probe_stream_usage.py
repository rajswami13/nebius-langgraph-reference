"""Check how Token Factory reports token usage on streamed responses, and what LangChain makes of it.

OpenAI's contract: with stream_options={"include_usage": True}, usage arrives once,
on a final chunk with empty choices. Clients (e.g. LangChain) sum usage across
chunks, so a server that repeats usage on every chunk inflates token counts.

For each model this prints:
  raw    - chunks, how many carried usage, and the server's final usage
  plain  - usage after a stream through plain langchain_openai.ChatOpenAI
  fixed  - usage after a stream through nebius_agent's NebiusChatOpenAI

    uv run python scripts/probe_stream_usage.py Qwen/Qwen3-235B-A22B-Instruct-2507 zai-org/GLM-5.3
"""
import os
import sys

from langchain_openai import ChatOpenAI
from openai import OpenAI

from nebius_agent.llm import NEBIUS_BASE_URL, make_chat_model

PROMPT = "Count from 1 to 10."
client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=os.environ.get("NEBIUS_API_KEY") or make_chat_model().openai_api_key.get_secret_value())


def aggregate(llm):
    agg = None
    for chunk in llm.stream(PROMPT):
        agg = chunk if agg is None else agg + chunk
    u = agg.usage_metadata
    return u["input_tokens"], u["output_tokens"]


print(f"endpoint: {NEBIUS_BASE_URL}\nprompt: {PROMPT!r}\n")
for model in sys.argv[1:]:
    chunks = list(client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        stream=True,
        stream_options={"include_usage": True},
        max_tokens=100,
        temperature=0,
    ))
    final = chunks[-1].usage
    with_usage = sum(1 for c in chunks if c.usage)
    common = {"model": model, "base_url": NEBIUS_BASE_URL, "temperature": 0, "max_tokens": 100, "stream_usage": True}
    plain = aggregate(ChatOpenAI(api_key=client.api_key, **common))
    fixed = aggregate(make_chat_model(model, max_tokens=100))
    ratio = f"{plain[0] / fixed[0]:.1f}x in, {plain[1] / fixed[1]:.1f}x out" if fixed[0] and fixed[1] else "n/a"
    print(f"{model}")
    print(f"  raw    chunks={len(chunks)} chunks_with_usage={with_usage} final={final.prompt_tokens}+{final.completion_tokens}")
    print(f"  plain  ChatOpenAI       usage={plain[0]}+{plain[1]}   ({ratio} vs fixed)")
    print(f"  fixed  NebiusChatOpenAI usage={fixed[0]}+{fixed[1]}")
