# LangGraph on Nebius Token Factory: reference agent and conformance kit

A working LangGraph agent running on [Nebius Token Factory](https://tokenfactory.nebius.com), with OpenTelemetry tracing and a test suite that checks tool calling, structured output and streaming through LangChain's abstractions, model by model.

**What you get**

- **Reference agent** ([src/nebius_agent/graph.py](src/nebius_agent/graph.py)): a LangGraph tool loop with two tools, a price lookup and a calculator. It runs on tool-capable Token Factory models (see [Model compatibility](#model-compatibility)).
- **Drop-in model factory** ([src/nebius_agent/llm.py](src/nebius_agent/llm.py)): `make_chat_model()` returns a LangChain chat model already pointed at Token Factory. It includes a fix for a streaming token-usage issue (see [Known issues](#known-issues)).
- **Tracing** ([src/nebius_agent/tracing.py](src/nebius_agent/tracing.py)): OpenTelemetry spans via OpenInference. Every run prints a span tree to the console, and if you configure an endpoint it also sends spans over OTLP to Phoenix, Langfuse, Jaeger, Grafana or Datadog.
- **Conformance kit** ([conformance/](conformance/)): 13 checks × N models, run live against Token Factory. Each run writes a dated pass/fail matrix with failure details to [conformance/results/](conformance/results/).

## Quickstart (5 minutes)

You need Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/rajswami13/nebius-langgraph-reference
cd nebius-langgraph-reference
cp .env.example .env          # then paste your Token Factory API key into .env
uv sync
uv run nebius-agent
```

Expected output:

```
  [tool call] get_gpu_price({'gpu_type': 'H200'})
  [tool result] get_gpu_price -> H200: $3.50 per GPU-hour (mock price)
  [tool call] calculate({'expression': '8 * 72 * 3.5'})
  [tool result] calculate -> 2016.0

Running 8 H200 GPUs for 72 hours would cost $2,016.

trace_id=e3e359ef...  spans=14
[CHAIN] LangGraph (2743 ms)
  [AGENT] agent (864 ms)
    [LLM] NebiusChatOpenAI (862 ms) model=Qwen/Qwen3-235B-A22B-Instruct-2507 tokens=310+25 -> tool_calls=['get_gpu_price']
  [CHAIN] tools (1 ms)
    [TOOL] get_gpu_price (0 ms) args='H200' result='H200: $3.50 per GPU-hour (mock price)'
  ...
```

GPU prices in this demo are mock values, not Nebius pricing.

More options:

```bash
uv run nebius-agent "Compare 4 B200s vs 8 H100s for 24 hours"   # your own question
uv run nebius-agent --stream                                      # stream tokens
uv run nebius-agent --model moonshotai/Kimi-K3                    # another tool-capable model
```

Check that everything works:

```bash
uv run pytest tests                                                  # offline unit tests, no API key needed
NEBIUS_TEST_MODELS="Qwen/Qwen3-235B-A22B-Instruct-2507" uv run pytest conformance -k end_to_end   # live smoke test
```

## Use it in your own code

Token Factory speaks the OpenAI API, so the integration comes down to the base URL. Use our factory to get the streaming-usage fix:

```python
from nebius_agent.llm import make_chat_model

llm = make_chat_model("deepseek-ai/DeepSeek-V4.1-Flash")
llm.bind_tools([my_tool]).invoke("...")
llm.with_structured_output(MySchema).invoke("...")
```

Or use plain `ChatOpenAI`:

```python
import os

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="Qwen/Qwen3-235B-A22B-Instruct-2507",
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=os.environ["NEBIUS_API_KEY"],
)
```

### Why not the official `langchain-nebius` package?

We ran the same conformance kit against `langchain-nebius` 0.1.3 (`ChatNebius`) on Qwen3-235B, DeepSeek-V4.1-Flash and GLM-5.3. Full results: [conformance/results/langchain-nebius.md](conformance/results/langchain-nebius.md).

```bash
NEBIUS_CLIENT=langchain-nebius NEBIUS_TEST_MODELS="Qwen/Qwen3-235B-A22B-Instruct-2507,deepseek-ai/DeepSeek-V4.1-Flash,zai-org/GLM-5.3" \
  uv run --with langchain-nebius==0.1.3 pytest conformance -n 8 -k "not server_usage"
```

| check | `ChatOpenAI` + our factory | `ChatNebius` 0.1.3 |
|---|---|---|
| tool calling (single, parallel, forced, round-trip) and the LangGraph agent end to end | ✅ | ✅ |
| structured output, `function_calling` | ✅ | ✅ |
| structured output, `json_schema` / `json_mode` | ✅ | ❌ crashes: `root_client` is never set, so LangChain's `.parse()` path has no client |
| token usage on streamed calls | ✅ | ❌ none reported (`stream_usage` not enabled) |
| default endpoint | `api.tokenfactory.nebius.com` | `api.studio.nebius.ai` (legacy domain) |

`ChatNebius` defaults to `method="function_calling"`, which works. However, `ChatOpenAI` defaults to `json_schema`, so code ported from OpenAI, or code that asks for `json_schema` explicitly, crashes on `ChatNebius`. These fixes should go upstream into `langchain-nebius`. Until then, use `make_chat_model()`.

## Tracing

Every run prints its trace. To view traces in a UI, run any OTLP backend. For example, [Arize Phoenix](https://github.com/Arize-ai/phoenix):

```bash
uvx arize-phoenix serve                                          # UI at http://localhost:6006
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006 uv run nebius-agent
```

Spans follow the [OpenInference](https://github.com/Arize-ai/openinference) semantic conventions on top of OpenTelemetry. They carry the model name, prompts and completions, token counts, tool names, arguments and results. A sample trace is in [traces/](traces/).

## Model compatibility

Run the conformance kit yourself (about 30 seconds):

```bash
uv run pytest conformance -n 8                                    # default 7 models
NEBIUS_TEST_MODELS="zai-org/GLM-5.3,moonshotai/Kimi-K3" uv run pytest conformance -n 8
```

Results from the latest run (full matrix, provenance and failure details in [conformance/results/chatopenai.md](conformance/results/chatopenai.md)):

| capability (via LangChain) | Qwen3-235B | Kimi-K3 | DeepSeek-V4.1-Flash | GLM-5.3 | gpt-oss-120b | muse-spark-open | gemma-3-27b |
|---|---|---|---|---|---|---|---|
| single tool call | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| parallel tool calls | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| forced `tool_choice` (10 tries) | ✅ 10/10 | ❌ 2/10, 0/10 | ✅ | ✅ | ❌ 0/10 | ✅ | ⚠️ |
| tool result round-trip | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| LangGraph agent end to end | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| structured output (all 3 methods) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| streaming text and tool calls | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| streamed token usage correct | ✅* | ✅ | ✅ | ✅ | ✅* | ✅ | ✅* |

\* Correct only with the fix in `make_chat_model()`. ⚠️ Passed in the latest run but failed in an earlier one, so it's inconsistent.

Not every model passing every check is expected: the matrix shows which models to pick for agents.

**Recommended for agents:** Qwen3-235B-A22B-Instruct-2507 (fast, passes everything), DeepSeek-V4.1-Flash, GLM-5.3 or muse-spark-open.

## Known issues

These issues were found by the conformance kit and are reproducible with the scripts in [scripts/](scripts/).

1. **Streamed token usage is over-counted by client SDKs (Qwen3-235B, gpt-oss-120b, gemma-3-27b).**
   - **Server behavior:** These models attach cumulative `usage` to every streamed chunk. The OpenAI spec sends it once, on the final chunk.
   - **Effect:** LangChain sums usage across chunks, so the inflation grows with response length: 6–39× on a short prompt in [our probe](evidence/stream-usage-probe.txt). Any token count computed client-side (LangSmith, Langfuse, your own dashboards) is wrong. We have not examined Nebius invoices, which are computed server-side.
   - **Fix:** `NebiusChatOpenAI` in [llm.py](src/nebius_agent/llm.py) drops usage from content chunks. [tests/test_offline.py](tests/test_offline.py) shows the fix and the bug with synthetic chunks.
   - **Reproduce:** `uv run python scripts/probe_stream_usage.py <model>`.
   - **Server-side fix needed:** yes.
2. **`tool_choice` is silently ignored, fully or intermittently (Kimi-K3, gpt-oss-120b).**
   - **Server behavior:** The request is accepted, but the model often answers in plain text instead of calling the required tool, and no error is returned. Over 10 tries ([evidence](evidence/tool-choice-probe.txt)):
     - Kimi-K3 honored a named tool 2 times and "must call a tool" 0 times. Every failure was no tool call at all, never a wrong tool.
     - gpt-oss-120b honored neither.
     - Qwen3-235B honored both 10 out of 10 times.
   - **Note:** Because it's intermittent, a single conformance run can show Kimi-K3 passing. Use `scripts/probe_tool_choice.py` for rates.
   - **Effect:** This breaks `with_structured_output(method="function_calling")` patterns that rely on forcing, as well as "must call a tool" agent steps.
   - **Workaround:** Use `method="json_schema"` for structured output with these models.
3. **gpt-oss-120b calls tools one at a time** instead of in parallel. It is functionally fine, but it adds latency to agent loops.
4. **gemma-3-27b-it does not call tools in auto mode.** It answers with made-up data instead, for example inventing today's weather. Don't use it for tool-using agents.
5. **`parallel_tool_calls=False` is ignored (Qwen3-235B).**
   - **Server behavior:** With three dependent tools (price → calculate → convert), Qwen3-235B returned all three calls in one turn on every try, even with `parallel_tool_calls=False` ([evidence](evidence/parallel-tool-calls-probe.txt)). DeepSeek-V4.1-Flash, GLM-5.3, Kimi-K3, gpt-oss-120b and muse-spark-open each returned one call per turn. That is consistent with honoring the flag, though it can't be told apart from simply calling tools one at a time.
   - **Effect:** The model guesses the inputs to later steps before it has seen earlier results. Found while rehearsing a "add a currency tool" change: the agent answered $2,592 instead of $2,016.
   - **Workaround:** The agent's system prompt in [graph.py](src/nebius_agent/graph.py) tells the model to call one tool at a time and wait for each result. That produced 6 correct answers in 6 runs.
   - **Reproduce:** `uv run python scripts/probe_parallel_tool_calls.py 3 <model>`.

## Running on Nebius infrastructure

**What exists today:** the [Dockerfile](Dockerfile) packages the CLI, which answers one question and exits. That fits a Kubernetes Job or a batch run as-is. The Dockerfile has not been built yet, because Docker wasn't available where this was written.

**Proposed production architecture.** This isn't built; it shows how the same graph would run as a service:

```
             ┌──────────────────────── Nebius Managed Kubernetes ────────────────────────┐
 client ───▶ │  agent pods (this image, stateless, HPA)  ──OTLP──▶  OTel Collector ──▶ Phoenix / Langfuse
             │        │                    │                                              │
             │        │ checkpoints        │ HTTPS (OpenAI API)                           │
             │        ▼                    ▼                                              │
             │  Managed PostgreSQL    Token Factory  (models; no GPUs to run yourself)   │
             └──────────────────────────────────────────────────────────────────────────┘
```

- **Agent runtime:** the same `build_agent()` graph behind a small HTTP or queue-worker wrapper, which this repo does not include. That wrapper adds health checks and request timeouts, and it is deployed on Nebius Managed Kubernetes behind a service. Pods hold no state, so they scale out horizontally on CPU nodes. The agent itself needs no GPUs, because inference happens in Token Factory.
- **State:** swap `InMemorySaver` for `langgraph-checkpoint-postgres` backed by Nebius Managed PostgreSQL. Conversations (`thread_id`) then survive pod restarts and can resume on any replica.
- **Models:** Token Factory over HTTPS from inside the same cloud. The API key is stored in a Kubernetes Secret.
- **Observability:** an OTel Collector receives the OTLP spans and forwards them to Phoenix or Langfuse running on the same cluster, or to any vendor you choose.
- **Scaling knobs:** pod autoscaling on request concurrency, Token Factory rate limits per key, and model choice per node (for example, a fast model for routing and a large one for reasoning).

```bash
docker build -t nebius-agent .            # untested, see above
docker run --rm -e NEBIUS_API_KEY nebius-agent "How much do 2 B200s cost for a week?"
```

## Certifying the next framework

[conformance/cases.py](conformance/cases.py) holds framework-neutral cases: prompts, tool schemas, a Pydantic schema and expected answers. The `test_*.py` files are the LangChain/LangGraph adapter. To certify another framework (CrewAI, PydanticAI, Vercel AI SDK), write a new adapter that runs the same cases through that framework's API. The results matrix stays directly comparable across partners.

## Repo layout

```
src/nebius_agent/   llm.py (model factory + fix) · tools.py · graph.py (agent) · tracing.py · cli.py
tests/              offline unit tests (run in CI, no API key)
conformance/        cases.py (neutral specs) · test_tool_calling.py · test_structured_output.py · test_streaming.py
conformance/results/  latest live results per client, with provenance and failure details
scripts/            probe_raw.py (raw-SDK tool-call baseline) · probe_stream_usage.py · probe_tool_choice.py · probe_parallel_tool_calls.py (issue repros)
evidence/           saved probe output backing the known-issues claims
traces/             sample trace (console tree + OTel JSON lines)
```

## Ecosystem recommendation (Part 2)

The one-page recommendation to the Nebius exec team is in [docs/ecosystem-recommendation.pdf](docs/ecosystem-recommendation.pdf). The same text is also in [Markdown](docs/ecosystem-recommendation.md). It covers which three partners to prioritize, how to staff 4 FDEs, the trade-off, and one ask.

## How this was built

This was built with Claude Code running Claude Opus 5.5. [docs/build-log/BUILD_NOTES.md](docs/build-log/BUILD_NOTES.md) records the decisions, the corrections after an external review, and the validation status.
