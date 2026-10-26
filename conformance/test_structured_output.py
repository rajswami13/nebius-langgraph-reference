"""Structured output via LangChain's with_structured_output, across all three methods.

Partners hit different methods depending on their stack, and they map to
different server features: json_schema -> response_format json_schema,
function_calling -> forced tool call, json_mode -> response_format json_object.
"""
import cases
import pytest


@pytest.mark.parametrize("method", ["json_schema", "function_calling", "json_mode"])
def test_structured_output(llm, method):
    prompt = cases.EXTRACTION_PROMPT
    if method == "json_mode":  # json_mode does not send the schema; the prompt must describe it
        prompt += f"\nRespond only with JSON matching this schema: {cases.Order.model_json_schema()}"
    result = llm.with_structured_output(cases.Order, method=method).invoke(prompt)
    assert isinstance(result, cases.Order), f"got {type(result).__name__}: {result!r}"
    got = result.model_dump()
    got["city"] = got["city"].removesuffix(" team")
    assert got == cases.EXTRACTION_EXPECT
