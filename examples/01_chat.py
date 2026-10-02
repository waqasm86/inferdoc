import inferdoc

response = inferdoc.chat(
    model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    prompt="Explain TTFT in one sentence.",
    max_tokens=64,
    temperature=0.0,
    chat_template_kwargs={"enable_thinking": False},
)
print(response.text)
