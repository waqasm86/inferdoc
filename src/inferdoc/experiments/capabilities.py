from .policy import BackendCapabilities

TOKEN_FACTORY_CAPABILITIES = BackendCapabilities(
    backend="nebius-token-factory",
    controllable_fields={"temperature", "max_tokens", "stream", "concurrency", "prompts"},
    observable_fields={
        "latency_s", "ttft_s", "request_throughput_rps", "output_token_throughput_tps",
        "total_token_throughput_tps", "token_usage",
    },
    domains={"concurrency": (1, 64), "max_tokens": (1, 4096), "temperature": (0.0, 2.0)},
)

DEMO_TOKEN_FACTORY_CAPABILITIES = BackendCapabilities(
    backend="nebius-token-factory",
    controllable_fields={"concurrency"},
    observable_fields=TOKEN_FACTORY_CAPABILITIES.observable_fields,
    domains={"concurrency": (1, 8)},
)
