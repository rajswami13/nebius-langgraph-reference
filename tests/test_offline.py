"""Offline unit tests: no API key or network needed. Run with `uv run pytest tests`."""
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI

from nebius_agent.llm import NebiusChatOpenAI
from nebius_agent.tools import calculate, get_gpu_price


def _chunk(content, usage, choices=True):
    return {
        "id": "c1",
        "model": "m",
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}] if choices else [],
        "usage": usage,
    }


# What Qwen3-235B on Token Factory actually sends: cumulative usage on every chunk, then a final usage-only chunk.
CUMULATIVE_STREAM = [
    _chunk("1", {"prompt_tokens": 16, "completion_tokens": 1, "total_tokens": 17}),
    _chunk(", 2, 3", {"prompt_tokens": 16, "completion_tokens": 9, "total_tokens": 25}),
    _chunk(", 4, 5.", {"prompt_tokens": 16, "completion_tokens": 15, "total_tokens": 31}),
    _chunk("", {"prompt_tokens": 16, "completion_tokens": 15, "total_tokens": 31}, choices=False),
]


def _aggregate_usage(model_cls):
    llm = model_cls(model="m", api_key="offline", base_url="http://offline")
    agg = None
    for raw in CUMULATIVE_STREAM:
        gen = llm._convert_chunk_to_generation_chunk(raw, AIMessageChunk, {})
        agg = gen.message if agg is None else agg + gen.message
    return agg.usage_metadata


def test_fix_reports_final_usage_once():
    u = _aggregate_usage(NebiusChatOpenAI)
    assert (u["input_tokens"], u["output_tokens"], u["total_tokens"]) == (16, 15, 31)


def test_plain_chatopenai_overcounts_cumulative_usage():
    """Documents the bug the fix exists for; if this starts failing, LangChain fixed it upstream."""
    u = _aggregate_usage(ChatOpenAI)
    assert u["input_tokens"] == 64 and u["output_tokens"] == 40


def test_calculator():
    assert calculate.invoke({"expression": "8 * 72 * 3.5"}) == "2016.0"
    assert calculate.invoke({"expression": "(2 + 3) ** 2"}) == "25"


def test_calculator_rejects_unsafe_input():
    assert calculate.invoke({"expression": "9 ** 9 ** 9"}).startswith("Error")
    assert calculate.invoke({"expression": "1+" * 200 + "1"}).startswith("Error")
    assert calculate.invoke({"expression": "__import__('os')"}).startswith("Error")


def test_gpu_price_lookup():
    assert "3.50" in get_gpu_price.invoke({"gpu_type": "h200"})
    assert get_gpu_price.invoke({"gpu_type": "TPU"}).startswith("Unknown")
