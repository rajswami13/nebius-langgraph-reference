# Conformance results: `langchain-nebius` client on Token Factory

- **Date (UTC):** 2026-10-26 05:53
- **Client:** `langchain-nebius`
- **Commit:** `05aee37 (uncommitted changes)`
- **Endpoint:** `https://api.studio.nebius.ai/v1/ (package default)`
- **Packages:** `langchain-core==1.7.0`, `langchain-openai==1.7.2`, `langgraph==1.2.17`, `openai==3.37.0`, `langchain-nebius==0.1.3`
- **Command:** `pytest conformance -n 8 -p no:cacheprovider -k not server_usage` with `NEBIUS_CLIENT=langchain-nebius`
- **Models:** `Qwen/Qwen3-235B-A22B-Instruct-2507`, `deepseek-ai/DeepSeek-V4.1-Flash`, `zai-org/GLM-5.3`

✅ pass · ❌ fail · ⚪ skipped

| test | Qwen3-235B-A22B-Instruct-2507 | DeepSeek-V4.1-Flash | GLM-5.3 |
|---|---|---|---|
| `streaming::test_stream_text` | ✅ | ✅ | ✅ |
| `streaming::test_stream_tool_call` | ✅ | ✅ | ✅ |
| `streaming::test_stream_usage_counted_once` | ❌ | ❌ | ❌ |
| `structured_output::test_structured_output[function_calling]` | ✅ | ✅ | ✅ |
| `structured_output::test_structured_output[json_mode]` | ❌ | ❌ | ❌ |
| `structured_output::test_structured_output[json_schema]` | ❌ | ❌ | ❌ |
| `tool_calling::test_forced_tool_choice` | ✅ | ✅ | ✅ |
| `tool_calling::test_langgraph_agent_end_to_end` | ✅ | ✅ | ✅ |
| `tool_calling::test_parallel_tool_calls` | ✅ | ✅ | ✅ |
| `tool_calling::test_required_tool_choice` | ✅ | ✅ | ✅ |
| `tool_calling::test_single_tool_call` | ✅ | ✅ | ✅ |
| `tool_calling::test_tool_result_roundtrip` | ✅ | ✅ | ✅ |

## Failure details

- `streaming::test_stream_usage_counted_once` · `Qwen/Qwen3-235B-A22B-Instruct-2507`: AssertionError: usage reported on 0 chunks; expected exactly 1
- `streaming::test_stream_usage_counted_once` · `deepseek-ai/DeepSeek-V4.1-Flash`: AssertionError: usage reported on 0 chunks; expected exactly 1
- `streaming::test_stream_usage_counted_once` · `zai-org/GLM-5.3`: AssertionError: usage reported on 0 chunks; expected exactly 1
- `structured_output::test_structured_output[json_mode]` · `Qwen/Qwen3-235B-A22B-Instruct-2507`: AttributeError: 'NoneType' object has no attribute 'chat'
- `structured_output::test_structured_output[json_mode]` · `deepseek-ai/DeepSeek-V4.1-Flash`: AttributeError: 'NoneType' object has no attribute 'chat'
- `structured_output::test_structured_output[json_mode]` · `zai-org/GLM-5.3`: AttributeError: 'NoneType' object has no attribute 'chat'
- `structured_output::test_structured_output[json_schema]` · `Qwen/Qwen3-235B-A22B-Instruct-2507`: AttributeError: 'NoneType' object has no attribute 'chat'
- `structured_output::test_structured_output[json_schema]` · `deepseek-ai/DeepSeek-V4.1-Flash`: AttributeError: 'NoneType' object has no attribute 'chat'
- `structured_output::test_structured_output[json_schema]` · `zai-org/GLM-5.3`: AttributeError: 'NoneType' object has no attribute 'chat'
