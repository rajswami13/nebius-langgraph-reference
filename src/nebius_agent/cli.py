"""Run the reference agent from the command line.

    uv run nebius-agent "How much do 8 H200s cost for 72 hours?"
    uv run nebius-agent --stream --model moonshotai/Kimi-K3 "..."
"""
import argparse
import uuid

from nebius_agent.tracing import dump_trace, print_trace, setup_tracing

DEFAULT_QUESTION = "How much would it cost to run 8 H200 GPUs for 72 hours?"


def main() -> None:
    p = argparse.ArgumentParser(description="Reference LangGraph agent on Nebius Token Factory")
    p.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    p.add_argument("--model", help="Token Factory model id (default: $NEBIUS_MODEL or Qwen3-235B)")
    p.add_argument("--stream", action="store_true", help="stream tokens as they are generated")
    p.add_argument("--dump-trace", metavar="PATH", help="also write the trace as JSON lines")
    args = p.parse_args()

    setup_tracing()  # must run before the graph is built so LangChain is instrumented
    from nebius_agent.graph import build_agent

    agent = build_agent(args.model)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    inputs = {"messages": [("user", args.question)]}

    if args.stream:
        for chunk, meta in agent.stream(inputs, config, stream_mode="messages"):
            if meta["langgraph_node"] == "agent" and chunk.content:
                print(chunk.content, end="", flush=True)
            elif meta["langgraph_node"] == "tools":
                print(f"\n  [tool {chunk.name}] -> {chunk.content}", flush=True)
        print()
    else:
        result = agent.invoke(inputs, config)
        for m in result["messages"]:
            if m.type == "ai" and m.tool_calls:
                for tc in m.tool_calls:
                    print(f"  [tool call] {tc['name']}({tc['args']})")
            elif m.type == "tool":
                print(f"  [tool result] {m.name} -> {m.content}")
        print(f"\n{result['messages'][-1].content}")

    print_trace()
    if args.dump_trace:
        dump_trace(args.dump_trace)


if __name__ == "__main__":
    main()
