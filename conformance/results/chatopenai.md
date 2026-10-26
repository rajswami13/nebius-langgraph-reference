# Conformance results: `chatopenai` client on Token Factory

- **Date (UTC):** 2026-10-26 05:51
- **Client:** `chatopenai`
- **Commit:** `df9913d (uncommitted changes)`
- **Endpoint:** `https://api.tokenfactory.nebius.com/v1`
- **Packages:** `langchain-core==1.7.0`, `langchain-openai==1.7.2`, `langgraph==1.2.17`, `openai==3.37.0`
- **Command:** `pytest conformance -n 8 -p no:cacheprovider`
- **Models:** `Qwen/Qwen3-235B-A22B-Instruct-2507`, `moonshotai/Kimi-K3`, `deepseek-ai/DeepSeek-V4.1-Flash`, `zai-org/GLM-5.3`, `openai/gpt-oss-120b`, `meta-models/muse-spark-open`, `google/gemma-3-27b-it`

✅ pass · ❌ fail · ⚪ skipped

| test | Qwen3-235B-A22B-Instruct-2507 | Kimi-K3 | DeepSeek-V4.1-Flash | GLM-5.3 | gpt-oss-120b | muse-spark-open | gemma-3-27b-it |
|---|---|---|---|---|---|---|---|
| `streaming::test_server_usage_only_on_final_chunk` | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| `streaming::test_stream_text` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `streaming::test_stream_tool_call` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `streaming::test_stream_usage_counted_once` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `structured_output::test_structured_output[function_calling]` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `structured_output::test_structured_output[json_mode]` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `structured_output::test_structured_output[json_schema]` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `tool_calling::test_forced_tool_choice` | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `tool_calling::test_langgraph_agent_end_to_end` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `tool_calling::test_parallel_tool_calls` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| `tool_calling::test_required_tool_choice` | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `tool_calling::test_single_tool_call` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `tool_calling::test_tool_result_roundtrip` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

## Failure details

- `streaming::test_server_usage_only_on_final_chunk` · `Qwen/Qwen3-235B-A22B-Instruct-2507`: AssertionError: 6 content chunks carried usage
- `streaming::test_server_usage_only_on_final_chunk` · `google/gemma-3-27b-it`: AssertionError: 23 content chunks carried usage
- `streaming::test_server_usage_only_on_final_chunk` · `openai/gpt-oss-120b`: AssertionError: 16 content chunks carried usage
- `streaming::test_stream_tool_call` · `google/gemma-3-27b-it`: AssertionError: streamed tool-call chunks did not assemble into a tool call
- `tool_calling::test_forced_tool_choice` · `moonshotai/Kimi-K3`: AssertionError: assert [] == ['get_time']
- `tool_calling::test_forced_tool_choice` · `openai/gpt-oss-120b`: AssertionError: assert [] == ['get_time']
- `tool_calling::test_langgraph_agent_end_to_end` · `google/gemma-3-27b-it`: AssertionError: agent used tools set()
- `tool_calling::test_parallel_tool_calls` · `google/gemma-3-27b-it`: AssertionError: expected 2 parallel calls, got 0
- `tool_calling::test_parallel_tool_calls` · `openai/gpt-oss-120b`: AssertionError: expected 2 parallel calls, got 1
- `tool_calling::test_required_tool_choice` · `moonshotai/Kimi-K3`: AssertionError: assert ([])
- `tool_calling::test_required_tool_choice` · `openai/gpt-oss-120b`: AssertionError: assert ([])
- `tool_calling::test_single_tool_call` · `google/gemma-3-27b-it`: AssertionError: model answered without calling the tool: 'As of November 21, 2023, at 1:45 PM CET, the weather in Amsterdam is:\n\n*   **Temperature:** 8°C (46°F)\n*   **Condition:*'
- `tool_calling::test_tool_result_roundtrip` · `google/gemma-3-27b-it`: AssertionError: assert []
