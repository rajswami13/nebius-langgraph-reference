"""Token Factory chat model factory.

Token Factory is OpenAI-compatible, so LangChain's ChatOpenAI works as-is once
it is pointed at the Nebius base URL. Keeping this in one place means a partner
only changes one function to swap providers, models, or defaults.
"""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1")
DEFAULT_MODEL = os.getenv("NEBIUS_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507")


class NebiusChatOpenAI(ChatOpenAI):
    """ChatOpenAI with a fix for streamed token usage on Token Factory.

    Some Token Factory models (e.g. Qwen3-235B, gpt-oss-120b) attach *cumulative*
    usage to every streamed chunk instead of only the final one. LangChain sums
    usage across chunks, so streamed calls over-report tokens 4-10x. Per the
    OpenAI spec, usage belongs only on the final chunk with empty `choices`, so
    we drop it from content chunks. Spec-compliant models are unaffected.
    See conformance/test_streaming.py::test_stream_usage_matches_invoke.
    """

    def _convert_chunk_to_generation_chunk(self, chunk, default_chunk_class, base_generation_info):
        if chunk.get("choices") and chunk.get("usage"):
            chunk = {**chunk, "usage": None}
        return super()._convert_chunk_to_generation_chunk(chunk, default_chunk_class, base_generation_info)


def make_chat_model(model: str | None = None, **kwargs) -> ChatOpenAI:
    """Return a ChatOpenAI client bound to Nebius Token Factory."""
    api_key = os.getenv("NEBIUS_API_KEY")
    if not api_key:
        raise RuntimeError("NEBIUS_API_KEY is not set. Copy .env.example to .env and add your key.")
    params = {
        "model": model or DEFAULT_MODEL,
        "base_url": NEBIUS_BASE_URL,
        "api_key": api_key,
        "temperature": 0,
        "timeout": 60,
        "max_retries": 2,
        # Ask for token usage on streamed responses too, so traces carry token counts.
        "stream_usage": True,
    }
    params.update(kwargs)
    return NebiusChatOpenAI(**params)
