# Token Factory ecosystem: priorities for the next two quarters

**To:** Nebius exec team · **Re:** which partners to prioritize, how to staff 4 FDEs, one ask

## Bottom line

Most agent frameworks already **list** Token Factory, but none treats it as the default, and a listing doesn't guarantee a working integration. In a 2.5-hour reference build on LangGraph, I found four issues that no listing or doc warns about:

| Issue | Where | Impact |
|---|---|---|
| Streamed responses over-report tokens 4–10× | Token Factory server (Qwen3-235B, gpt-oss-120b, gemma-3) | Partners' cost tracking and billing are wrong |
| `tool_choice` accepted but silently ignored | Token Factory server (Kimi-K3, gpt-oss-120b) | "Must call a tool" agent steps break |
| Two of three structured-output modes crash; no streamed usage | Our official `langchain-nebius` 0.1.3 | Our flagship partnership ships a broken client |
| Model invents answers instead of calling tools | gemma-3-27b | Silent wrong answers |

**Recommendation:** for the next two quarters, turn three listings into certified integrations that work by default, and build the machine that keeps ten of them working.

## Three partners, in order

Ranking criteria: developer reach × tokens per developer × the gap between "listed" and "default."

**1. LangChain / LangGraph (Q1).** Largest agent framework. The partnership is already announced (Deep Agents), but the package underneath it is broken, so this is the fastest path to revenue and the biggest risk if left alone.
- **What we deliver:**
  - fix `langchain-nebius` and take ownership of it;
  - get it into LangChain's standard integration tests;
  - tuned Deep Agents profiles for our top open models;
  - correct Nebius pricing in LangSmith cost tracking.
- **What Nebius offers:**
  - a named FDE owner with a bug SLA on the package;
  - inference credits for Deep Agents users;
  - co-marketing at every open-model launch;
  - capacity for LangChain's own evals.

**2. Vercel: AI SDK + AI Gateway (start Q1, land Q2).** Reaches the TypeScript/Next.js half of the agent market, and Gateway traffic is paid tokens that flow to us directly. Today Gateway lists only part of our catalog (5 models at last check, against 30 on Token Factory), and the AI SDK has no native Nebius provider.
- **What we deliver:**
  - our full agent-capable catalog on Gateway;
  - day-0 listings for new open models;
  - a native AI SDK provider;
  - agent templates that deploy on Vercel.
- **What Nebius offers:**
  - wholesale pricing or a revenue share on Gateway traffic;
  - committed rate limits;
  - early access to new models.

**3. An open-source coding agent: Cline first, OpenCode as the alternate (Q2).** Coding agents use the most tokens per developer, and they rely heavily on tool calls, which is exactly where we found server bugs (for example, ignored `tool_choice` on Kimi models). The Q3 integrations exist; we're not the recommended provider yet.
- **What we deliver:**
  - certified coding models (tool calls that pass the kit);
  - a recommended Nebius preset in the agent;
  - latency tuning.
- **What Nebius offers:**
  - credits for the partner's users;
  - fast-inference capacity for coding models;
  - a revenue share on referred tokens.

## Staffing: 4 FDEs

| FDE | Q1 | Q2 |
|---|---|---|
| **1: Python frameworks** | LangChain / LangGraph | PydanticAI, CrewAI, LlamaIndex, OpenAI Agents SDK (via the kit) |
| **2: TypeScript and platforms** | Vercel AI SDK + Gateway | Mastra, n8n |
| **3: Coding agents** | Coding-model tool-call quality | Cline, then OpenCode |
| **4: Ecosystem platform** | Conformance kit runs nightly across every model × framework | Public compatibility page, partner self-certification, bug triage to the inference team |

**How this reaches ten partners:** the four FDEs land the first three by hand. For partners 4–10 (OpenAI Agents SDK, PydanticAI, CrewAI, LlamaIndex, Mastra, n8n, OpenCode), each partner runs our conformance kit in its own CI, and FDE time is capped at roughly one week per partner. The OpenAI Agents SDK is cheap to add: Token Factory already answers the Responses API.

## The trade-off

We go deep on three partners and put one of four FDEs on the platform instead of on a fourth partner. The cost: for two quarters, partners 4–10 get only self-serve support, and a competitor (Together, Fireworks, Groq) may win the default slot in a framework such as Mastra or n8n first. We accept that because a broken integration, like today's `langchain-nebius`, costs us more trust than a missing one.

## One ask

**Make the conformance kit a release gate, with an owner on the inference team.** No model ships on Token Factory until it passes the kit, and compatibility bugs the kit finds get a 2-week fix SLA. Two of the four issues above are server-side. FDEs can work around a server bug in one framework, but not in ten.
