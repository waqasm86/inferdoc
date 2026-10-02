import inferdoc

run = inferdoc.benchmark(
    model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    prompts=["What is TTFT?", "Why measure p95 latency?"],
    concurrency=2,
    max_tokens=32,
    stream=False,
)
print(run.model_dump_json(indent=2))
