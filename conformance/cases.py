"""Framework-neutral conformance cases for agent frameworks on Token Factory.

Each case is plain data: a prompt, the tools or schema involved, and what a
correct response must contain. Adapters (test_*.py) run these through a
specific framework's abstractions. To certify the next framework, write a new
adapter against the same cases; the matrix stays comparable across partners.
"""
from typing import Literal

from pydantic import BaseModel, Field

# --- Tool calling -----------------------------------------------------------

WEATHER_TOOL = {
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "City name"}},
        "required": ["city"],
    },
}
TIME_TOOL = {
    "name": "get_time",
    "description": "Get the current local time in a city.",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
}

SINGLE_CALL_PROMPT = "What's the weather in Amsterdam right now?"
FORCED_CALL_PROMPT = "Hi there!"  # no reason to call a tool unless forced
PARALLEL_CALL_PROMPT = "What's the weather in Amsterdam and in Paris? Look up both."
ROUNDTRIP_TOOL_RESULT = '{"city": "Amsterdam", "temperature_c": 17, "conditions": "light rain"}'
ROUNDTRIP_EXPECT = "17"

AGENT_PROMPT = "How much would it cost to run 8 H200 GPUs for 72 hours?"
AGENT_EXPECT_TOOLS = {"get_gpu_price", "calculate"}
AGENT_EXPECT_ANSWER = ("2,016", "2016")

# --- Structured output ------------------------------------------------------

EXTRACTION_PROMPT = (
    "Extract the order: 'Hi, this is order A-1234. Please reserve 3 H100 GPUs "
    "for our Berlin team, it's urgent.'"
)


class Order(BaseModel):
    order_id: str = Field(description="Order identifier, e.g. A-1234")
    gpu_type: str = Field(description="GPU model, e.g. H100")
    quantity: int
    city: str
    priority: Literal["low", "normal", "high"]


EXTRACTION_EXPECT = {"order_id": "A-1234", "gpu_type": "H100", "quantity": 3, "city": "Berlin", "priority": "high"}

# --- Streaming --------------------------------------------------------------

STREAM_TEXT_PROMPT = "Write two sentences about the North Sea."
