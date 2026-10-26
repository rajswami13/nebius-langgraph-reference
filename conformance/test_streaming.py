"""Streaming: text deltas, streamed tool-call arguments, and token usage accounting."""
import os

import cases
from openai import OpenAI


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


def test_stream_usage_matches_invoke(llm):
    """Token counts from a streamed call must equal the non-streamed call (cost tracking depends on it)."""
    prompt = "Count from 1 to 5."
    streamed, _ = _aggregate(llm.stream(prompt))
    invoked = llm.invoke(prompt)
    assert streamed.usage_metadata, "no usage reported on stream"
    assert streamed.usage_metadata["input_tokens"] == invoked.usage_metadata["input_tokens"]


def test_server_usage_only_on_final_chunk(model):
    """Raw server check (no LangChain): per the OpenAI spec, usage appears only on the final, empty-choices chunk.

    A failure here is a Token Factory issue, not a framework one. nebius_agent.llm works around it.
    """
    client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1", api_key=os.environ["NEBIUS_API_KEY"])
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Count from 1 to 5."}],
        stream=True,
        stream_options={"include_usage": True},
        max_tokens=50,
    )
    content_chunks_with_usage = sum(1 for c in stream if c.choices and c.usage)
    assert content_chunks_with_usage == 0, f"{content_chunks_with_usage} content chunks carried usage"
