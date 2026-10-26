"""Check how Token Factory reports token usage on streamed responses.

OpenAI's contract: with stream_options={"include_usage": True}, usage arrives once,
on a final chunk with empty choices. Clients (e.g. LangChain) sum usage across
chunks, so a server that repeats usage on every chunk inflates token counts.
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1", api_key=os.environ["NEBIUS_API_KEY"])

for model in sys.argv[1:]:
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Count from 1 to 10."}],
        stream=True,
        stream_options={"include_usage": True},
        max_tokens=100,
    )
    chunks = with_usage = 0
    last = None
    for c in stream:
        chunks += 1
        if c.usage:
            with_usage += 1
            last = c.usage
    print(f"{model:45s} chunks={chunks:3d} chunks_with_usage={with_usage:3d} final={last.prompt_tokens}+{last.completion_tokens}")
