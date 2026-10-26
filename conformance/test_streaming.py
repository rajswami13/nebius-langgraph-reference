"""Streaming: text deltas, streamed tool-call arguments, and token usage accounting."""
import os

import cases
from openai import OpenAI

from nebius_agent.llm import NEBIUS_BASE_URL


def _aggregate(stream):
    agg = None
    n = 0
    for chunk in stream:
        n += 1
        agg = chunk if agg is None else agg + chunk
    return agg, n


def test_stream_text(llm):
    agg, n = _aggregate(llm.stream(cases.STREAM_TEXT_PROMPT))
    assert n > 2, f"expected incremental chunks, got {n}"
    assert len(agg.content) > 20


def test_stream_tool_call(llm):
    agg, _ = _aggregate(llm.bind_tools([cases.WEATHER_TOOL]).stream(cases.SINGLE_CALL_PROMPT))
    assert agg.tool_calls, "streamed tool-call chunks did not assemble into a tool call"
    assert agg.tool_calls[0]["name"] == "get_weather"
    assert "amsterdam" in agg.tool_calls[0]["args"]["city"].lower()
    assert not agg.invalid_tool_calls


def test_stream_usage_counted_once(llm):
    """A streamed call's token usage must be reported once and add up (cost tracking depends on it).

    Checked within one stream, so differing completion lengths between generations don't matter.
    Input tokens are also compared with a non-streamed call, since the prompt is identical.
    """
    prompt = "Count from 1 to 5."
    chunks = list(llm.stream(prompt))
    with_usage = [c for c in chunks if c.usage_metadata]
    assert len(with_usage) == 1, f"usage reported on {len(with_usage)} chunks; expected exactly 1"
    agg = chunks[0]
    for c in chunks[1:]:
        agg = agg + c
    u, final = agg.usage_metadata, with_usage[0].usage_metadata
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        assert u[key] == final[key], f"{key}: aggregated {u[key]} != reported {final[key]}"
    assert u["output_tokens"] > 0
    assert u["total_tokens"] == u["input_tokens"] + u["output_tokens"]
    assert u["input_tokens"] == llm.invoke(prompt).usage_metadata["input_tokens"]


def test_server_usage_only_on_final_chunk(model):
    """Raw server check (no LangChain): per the OpenAI spec, usage appears exactly once, on a final
    chunk with empty `choices`.

    A failure here is a Token Factory issue, not a framework one. nebius_agent.llm works around it.
    """
    client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=os.environ["NEBIUS_API_KEY"])
    chunks = list(client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Count from 1 to 5."}],
        stream=True,
        stream_options={"include_usage": True},
        max_tokens=50,
    ))
    content_chunks_with_usage = sum(1 for c in chunks if c.choices and c.usage)
    assert content_chunks_with_usage == 0, f"{content_chunks_with_usage} content chunks carried usage"
    last = chunks[-1]
    assert not last.choices and last.usage, "no final usage-only chunk"
    assert last.usage.prompt_tokens > 0 and last.usage.completion_tokens > 0
