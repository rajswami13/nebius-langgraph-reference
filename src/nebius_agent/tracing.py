"""OpenTelemetry tracing for LangChain/LangGraph via OpenInference.

- Always: spans are collected in memory and printed as a compact tree.
- If OTEL_EXPORTER_OTLP_ENDPOINT is set (e.g. http://localhost:6006 for Phoenix),
  spans are also exported over OTLP/HTTP to any OTel backend
  (Phoenix, Langfuse, Jaeger, Grafana Tempo, Datadog, ...).
"""
import json
import os

from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)


class _MemoryExporter(SpanExporter):
    def __init__(self):
        self.spans: list[ReadableSpan] = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


_memory = _MemoryExporter()
_provider: TracerProvider | None = None


def setup_tracing(service_name: str = "nebius-langgraph-agent") -> TracerProvider:
    global _provider
    if _provider:
        return _provider
    _provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    _provider.add_span_processor(SimpleSpanProcessor(_memory))
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        _provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(_provider)
    LangChainInstrumentor().instrument(tracer_provider=_provider)
    return _provider


def _describe(span: ReadableSpan) -> str:
    a = span.attributes or {}
    kind = a.get("openinference.span.kind", "")
    ms = (span.end_time - span.start_time) / 1e6
    extra = ""
    if kind == "LLM":
        extra = f" model={a.get('llm.model_name')} tokens={a.get('llm.token_count.prompt')}+{a.get('llm.token_count.completion')}"
        calls = [a[k] for k in a if k.startswith("llm.output_messages") and k.endswith("tool_call.function.name")]
        if calls:
            extra += f" -> tool_calls={calls}"
    elif kind == "TOOL":
        out = a.get("output.value", "")
        try:
            out = json.loads(out)["data"]["content"]  # unwrap serialized ToolMessage
        except (ValueError, KeyError, TypeError):
            pass
        extra = f" args={a.get('input.value')!r} result={str(out)[:80]!r}"
    return f"[{kind or 'SPAN'}] {span.name} ({ms:.0f} ms){extra}"


def print_trace() -> None:
    """Print the most recent trace as an indented span tree."""
    if _provider:
        _provider.force_flush()
    if not _memory.spans:
        print("(no spans recorded)")
        return
    trace_id = _memory.spans[-1].context.trace_id
    spans = [s for s in _memory.spans if s.context.trace_id == trace_id]
    children: dict[int | None, list[ReadableSpan]] = {}
    for s in spans:
        children.setdefault(s.parent.span_id if s.parent else None, []).append(s)

    def walk(parent_id, depth):
        for s in sorted(children.get(parent_id, []), key=lambda s: s.start_time):
            print("  " * depth + _describe(s))
            walk(s.context.span_id, depth + 1)

    print(f"\ntrace_id={trace_id:032x}  spans={len(spans)}")
    walk(None, 0)


def dump_trace(path: str) -> None:
    """Write the most recent trace's spans as JSON lines (for committing a sample trace)."""
    if _provider:
        _provider.force_flush()
    trace_id = _memory.spans[-1].context.trace_id
    with open(path, "w") as f:
        for s in _memory.spans:
            if s.context.trace_id == trace_id:
                f.write(json.dumps(json.loads(s.to_json())) + "\n")
