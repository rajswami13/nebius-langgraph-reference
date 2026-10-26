"""Tool calling through LangChain/LangGraph abstractions (not the raw SDK)."""
import cases
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def _cities(tool_calls):
    return {tc["args"].get("city", "").lower() for tc in tool_calls}


def test_single_tool_call(llm):
    msg = llm.bind_tools([cases.WEATHER_TOOL]).invoke(cases.SINGLE_CALL_PROMPT)
    assert msg.tool_calls, f"model answered without calling the tool: {msg.content[:120]!r}"
    tc = msg.tool_calls[0]
    assert tc["name"] == "get_weather"
    assert isinstance(tc["args"], dict), "args must be parsed into a dict"
    assert "amsterdam" in tc["args"]["city"].lower()
    assert tc["id"], "tool call must carry an id for the result round-trip"
    assert not msg.invalid_tool_calls


def test_forced_tool_choice(llm):
    msg = llm.bind_tools([cases.WEATHER_TOOL, cases.TIME_TOOL], tool_choice="get_time").invoke(cases.FORCED_CALL_PROMPT)
    assert [tc["name"] for tc in msg.tool_calls] == ["get_time"]


def test_required_tool_choice(llm):
    msg = llm.bind_tools([cases.WEATHER_TOOL], tool_choice="any").invoke(cases.FORCED_CALL_PROMPT)
    assert msg.tool_calls and msg.tool_calls[0]["name"] == "get_weather"


def test_parallel_tool_calls(llm):
    msg = llm.bind_tools([cases.WEATHER_TOOL]).invoke(cases.PARALLEL_CALL_PROMPT)
    assert len(msg.tool_calls) >= 2, f"expected 2 parallel calls, got {len(msg.tool_calls)}"
    assert {"amsterdam", "paris"} <= _cities(msg.tool_calls)
    assert len({tc["id"] for tc in msg.tool_calls}) == len(msg.tool_calls), "tool call ids must be unique"


def test_tool_result_roundtrip(llm):
    bound = llm.bind_tools([cases.WEATHER_TOOL])
    first = bound.invoke(cases.SINGLE_CALL_PROMPT)
    assert first.tool_calls
    history = [
        HumanMessage(cases.SINGLE_CALL_PROMPT),
        first,
        ToolMessage(cases.ROUNDTRIP_TOOL_RESULT, tool_call_id=first.tool_calls[0]["id"]),
    ]
    final = bound.invoke(history)
    assert isinstance(final, AIMessage) and not final.tool_calls
    assert cases.ROUNDTRIP_EXPECT in final.content, f"answer ignored the tool result: {final.content[:200]!r}"


def test_langgraph_agent_end_to_end(llm):
    from nebius_agent.graph import build_agent

    result = build_agent(llm=llm).invoke(
        {"messages": [("user", cases.AGENT_PROMPT)]}, {"configurable": {"thread_id": "conformance"}}
    )
    used = {m.name for m in result["messages"] if m.type == "tool"}
    assert cases.AGENT_EXPECT_TOOLS <= used, f"agent used tools {used}"
    answer = result["messages"][-1].content
    assert any(x in answer for x in cases.AGENT_EXPECT_ANSWER), f"wrong final answer: {answer[:200]!r}"
