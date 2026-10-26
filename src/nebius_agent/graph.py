"""The reference agent: an explicit LangGraph tool loop.

    START -> agent --(tool calls?)--> tools -> agent ... -> END

We build the graph by hand instead of using the prebuilt ReAct helper so every
step is visible and easy to change live (add a node, swap a tool, add memory).
"""
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from nebius_agent.llm import make_chat_model
from nebius_agent.tools import TOOLS

SYSTEM_PROMPT = (
    "You are a GPU cost assistant. Always use get_gpu_price to look up prices and "
    "calculate for any arithmetic; never guess numbers. Keep answers short and show the math."
)


def build_agent(model: str | None = None, checkpointer=None):
    llm = make_chat_model(model).bind_tools(TOOLS)

    def agent(state: MessagesState):
        return {"messages": [llm.invoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    # In production, swap InMemorySaver for a Postgres checkpointer (see README).
    return graph.compile(checkpointer=checkpointer or InMemorySaver())
