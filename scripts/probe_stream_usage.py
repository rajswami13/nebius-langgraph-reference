"""Check how Token Factory reports token usage on streamed responses, and what LangChain makes of it.

OpenAI's contract: with stream_options={"include_usage": True}, usage arrives once,
on a final chunk with empty choices. Clients (e.g. LangChain) sum usage across
chunks, so a server that repeats usage on every chunk inflates token counts.

For each model this captures ONE raw stream, then replays exactly those chunks through
both LangChain converters, so the comparison is not affected by generation differences:
  server - chunks, how many carried usage, and the final usage the server reported
  plain  - usage as aggregated by plain langchain_openai.ChatOpenAI
  fixed  - usage as aggregated by nebius_agent's NebiusChatOpenAI

    uv run python scripts/probe_stream_usage.py Qwen/Qwen3-235B-A22B-Instruct-2507 zai-org/GLM-5.3
"""
import os
import sys

from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from openai import OpenAI

from nebius_agent.llm import NEBIUS_BASE_URL, NebiusChatOpenAI

PROMPT = "Count from 1 to 10."
client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=os.environ.get("NEBIUS_API_KEY"))


def replay(model_cls, chunks):
    converter = model_cls(model="replay", api_key="offline", base_url="http://offline")
    agg = None
    for raw in chunks:
        gen = converter._convert_chunk_to_generation_chunk(raw, AIMessageChunk, {})
        if gen:
            agg = gen.message if agg is None else agg + gen.message
    u = agg.usage_metadata or {}
    return u.get("input_tokens", 0), u.get("output_tokens", 0)


print(f"endpoint: {NEBIUS_BASE_URL}\nprompt: {PROMPT!r}\n")
for model in sys.argv[1:]:
    chunks = [c.model_dump() for c in client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        stream=True,
        stream_options={"include_usage": True},
        max_tokens=100,
    )]
    final = chunks[-1]["usage"]
    with_usage = sum(1 for c in chunks if c.get("usage"))
    plain, fixed = replay(ChatOpenAI, chunks), replay(NebiusChatOpenAI, chunks)
    ratio = f"{plain[0] / fixed[0]:.1f}x in, {plain[1] / fixed[1]:.1f}x out" if fixed[0] and fixed[1] else "n/a"
    print(f"{model}")
    print(f"  server chunks={len(chunks)} chunks_with_usage={with_usage} final={final['prompt_tokens']}+{final['completion_tokens']}")
    print(f"  plain  ChatOpenAI       usage={plain[0]}+{plain[1]}   ({ratio} vs server final)")
    print(f"  fixed  NebiusChatOpenAI usage={fixed[0]}+{fixed[1]}")
