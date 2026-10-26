# How this was built

A short decision record of the Claude Code session that built this repo. Every result below is from an actual run. The full redacted session transcript is available on request; it was produced with [export_session.py](export_session.py).

## Tooling

- **Coding agent:** Claude Code, in the VS Code extension
- **Model:** Claude Opus 5.5 (`claude-opus-5-5`)
- **Python toolchain:** `uv` with Python 3.12. The system Python was 3.9, which is too old for current LangGraph.

**Why this tool and model:** I use Claude Code in VS Code every day, so I could spend the time on the integration instead of on tooling. Opus 5.5 was the most capable model I had access to. That mattered here, because the work involved long multi-step debugging (tracing a token-count bug from a trace, to the raw API, to LangChain's internals) more than writing boilerplate.

## Sequence and key decisions

1. **Planning.** We chose LangGraph because it has the widest agent-framework reach and because tool calling crosses several layers there (`bind_tools`, the OpenAI adapter, the model's parser), which is where silent failures hide. For tracing we chose OpenTelemetry with OpenInference, which works with any backend.
2. **Endpoint discovery.** Both `api.tokenfactory.nebius.com` and `api.studio.nebius.com` served the same 30 models. We used the Token Factory domain.
3. **Raw baseline before any framework code.** We ran tool-call probes on 16 models with the plain OpenAI SDK ([scripts/probe_raw.py](../../scripts/probe_raw.py)). 15 of 16 returned clean tool calls. gemma-3-27b answered with invented weather instead.
4. **Reference agent.** We built the LangGraph tool loop by hand rather than using the prebuilt ReAct helper, so every step stays visible and easy to change. The demo question needs two tools in sequence. The first end-to-end run answered correctly ($2,016).
5. **First server finding.** The streaming trace showed about 10× the tokens of the non-streamed run. A raw probe showed that some models repeat cumulative usage on every chunk, and that LangChain sums it. We added `NebiusChatOpenAI` to drop usage from content chunks.
6. **Conformance kit.** Test cases are framework-neutral, and the LangChain tests are one adapter on top of them. The first matrix showed `tool_choice` being ignored on Kimi-K3 and gpt-oss-120b. Structured output passed on all 7 models.
7. **Published.** We created the public repo and verified that the README quickstart works from a fresh clone.
8. **Part 2 research.** Searches showed Nebius already has a LangChain partnership, a Vercel Gateway listing, and Q3 coding-agent integrations. That changed the recommendation from "integrate" to "certify and deepen."
9. **Official SDK check.** We ran `langchain-nebius` 0.1.3 through the same kit. Two of its three structured-output modes crash because `root_client` is never set, and streamed calls report no usage. One claim in our README was corrected before publishing: `ChatNebius` defaults to `function_calling`, which works.

## Corrections after an external review

An independent review checked commit `df9913d`. We verified each finding before acting on it:

| Finding | Outcome |
|---|---|
| `.env` loaded after tracing setup | Confirmed by reproduction and fixed. The OTLP exporter now registers. |
| End-to-end test ignored the client switch | Confirmed and fixed. No published claim was affected, because that test had been excluded from the ChatNebius run. |
| Usage test checked input tokens only | Confirmed and fixed. The test now requires exactly one usage chunk and consistent input, output and total. Offline tests use synthetic chunks. |
| Unbounded calculator exponent | Confirmed by reading the code and fixed. |
| Results file overwritten, no provenance | Fixed. Results are now per client, with date, commit, packages, endpoint, command and failure details. |
| Memo facts and claims | The Vercel model count was wrong (the live page shows 8, not 5). The "4–10×" inflation figure was too low: the saved probe shows 6–39×, growing with response length. Unsourced claims are now stated as assumptions. |

Re-measuring also corrected one of our own claims. `tool_choice` on Kimi-K3 fails intermittently, not every time: a named tool was honored 3 times in 10 and "must call a tool" 0 times. A single conformance run can therefore show it passing. The README now cites these rates.

## Validation status (latest)

- **Offline unit tests:** 5 passed, also in GitHub Actions CI.
- **Live conformance, `chatopenai` client:** 7 models × 13 checks. See [conformance/results/chatopenai.md](../../conformance/results/chatopenai.md). Failures are the documented model and server issues.
- **Live conformance, `langchain-nebius==0.1.3`:** 3 models. See [conformance/results/langchain-nebius.md](../../conformance/results/langchain-nebius.md).
- **Not verified:** the Docker image build and run (Docker was unavailable), deployment to Kubernetes, and receipt of traces by an OTLP backend.
