# Token Factory ecosystem: priorities for Q1–Q2 2027

**To:** Nebius exec team · **Timing:** assumes a January 2027 kickoff · **Evidence:** [github.com/rajswami13/nebius-langgraph-reference](https://github.com/rajswami13/nebius-langgraph-reference)

## Bottom line

Most agent frameworks list Token Factory, but a listing doesn't guarantee a working integration. A one-day LangGraph build found four defects that no listing warns about. **Over the next two quarters, turn three listings into certified integrations, and build the test system that keeps ten of them working.**

| Defect | Where | Effect |
|---|---|---|
| Usage repeated on every streamed chunk | Server: 3 models | SDK-reported token counts inflated 6–39×. Invoices not examined. |
| `tool_choice` ignored, with no error | Server: Kimi-K3 (honored 0–2 of 10), gpt-oss-120b (0 of 10) | "Must call a tool" steps fail silently |
| Two structured-output modes crash; streams report no usage | `langchain-nebius` 0.1.3 | Code ported from `ChatOpenAI` breaks |
| Answers without calling tools | gemma-3-27b | Invented data |

## Three partners, in order

The order reflects our assumptions about developer reach and token volume. We validate it in month 1 with partner-tagged usage.

| Partner | Why | We deliver | Nebius offers | We ask of the partner |
|---|---|---|---|---|
| **1. LangChain / LangGraph** (Q1) | The partnership is announced; the SDK under it has the defects above | A fixed `langchain-nebius` that Nebius maintains, in LangChain's integration tests; Deep Agents profiles | A named owner with a bug SLA, credits for Deep Agents users, launch co-marketing | Placement as a recommended open-model provider; joint launches |
| **2. Vercel AI SDK + Gateway** (start Q1, launch Q2) | Reaches TypeScript developers. Gateway lists 8 Nebius models ([snapshot](../evidence/vercel-gateway-nebius-models.md)), and earns us revenue only when it routes traffic to us | Our agent-capable catalog on Gateway, day-0 listings, a certified OpenAI-compatible path, templates | Wholesale pricing or a revenue share; committed rate limits | Routing preference for models we serve; distribution of the templates |
| **3. Cline, with OpenCode as the alternate** (Q2) | Coding agents rely heavily on tool calls, where the server defects hurt most | Certified coding models, a Nebius preset, latency tuning | User credits, fast-inference capacity, a revenue share | Placement as a recommended provider |

The asks are negotiating goals; none is agreed yet.

## Staffing: 4 FDEs

| FDE | Q1 2027 | Q2 2027 |
|---|---|---|
| Python | LangChain | Maintain LangChain first; then PydanticAI, CrewAI, OpenAI Agents SDK* |
| TypeScript | Vercel | Vercel launch, then Mastra |
| Coding agents | Tool-call quality for coding models | Cline, then OpenCode |
| Platform | Nightly conformance runs, models × frameworks | Public compatibility page; partner self-certification |

**Proposed milestones.** Q1: LangChain certified and Vercel pilot running. Q2: Vercel and Cline certified.

**Partners 4–10** get limited enablement: the partner owns the implementation and runs our test kit in its own CI, with at most one FDE-week each. Maintaining shipped integrations always comes first.

\*Token Factory serves the stateless Responses API. Multi-turn and tool behavior are untested, so this estimate is provisional.

**Success per partner**, with targets set in week 2:
- the integration is released upstream and its docs are live;
- activated developers, measured with partner-tagged keys;
- weekly production integrations;
- paid tokens that come through the partner.

## The trade-off

We choose depth over breadth: one of the four FDEs builds the platform instead of landing a fourth partner. Partners 4–10 get only limited enablement for two quarters, and a competitor may win the default slot in Mastra or n8n first. We accept that, because a broken integration costs more trust than a missing one.

## One ask

**A capability-based release gate, owned by the inference team.**
- Each model must pass the checks for the capabilities it advertises before launch.
- Models marketed for agents must also pass the full agent-ready suite.
- For a severity-1 compatibility bug, the inference team ships a mitigation within 48 hours and a permanent fix within 2 weeks (proposed targets, to agree with the inference team).
- Exceptions need the inference lead's sign-off.

Two of the four defects above are server-side. FDEs can work around a server bug in one framework, but not in ten.
