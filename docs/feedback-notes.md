# Implementation-derived feedback

These observations come from building and testing InferDoc. They are product
feedback, not claims about undocumented platform behavior.

| Area | Observation | Constructive suggestion |
| --- | --- | --- |
| OpenAI-compatible API | Standard chat request shapes made the Token Factory client small and let InferDoc focus on evidence. | Keep compatibility examples for model-specific options alongside the generic API. |
| Nemotron Nano tool calling | Read-only function calls work well for bounded evidence analysis and a single proposed experiment. | Publish a compact worked example of tool calls plus a validated structured final report. |
| Structured output | A reasoning response can be syntactically or schema invalid, so InferDoc validates and uses bounded repair turns. | Document reliable schema and repair patterns for agent builders. |
| Reasoning controls | Normal workload inference and Doctor reasoning need different `enable_thinking` settings. | Put the control and token-budget implications prominently near model examples. |
| Serverless telemetry | Client-side latency, usage, and throughput are observable; GPU utilization and KV-cache internals are not exposed in this integration. | Make serverless versus dedicated-endpoint telemetry boundaries easy to find. |
| Streaming | A first streamed chunk can expose TTFT, while current streaming usage may be unavailable for token throughput. | Clarify usage availability by response mode and document how to request usage with streaming where supported. |
| Capability discovery | InferDoc must maintain explicit backend control and observable lists for safe experiment admission. | A machine-readable capability discovery API would help inference-engineering SDKs avoid invalid experiments. |

Do not paste API keys, private prompts, or unredacted provider responses here.
