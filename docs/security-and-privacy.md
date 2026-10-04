# Security and privacy

Keep `NEBIUS_API_KEY` in your process environment or an ignored local `.env`; never put a real key in examples, issues, notebooks, or commits. `.env.example` contains placeholders. The project [security policy](../SECURITY.md) asks for private vulnerability reports. Live requests send prompts and parameters to Nebius Token Factory and spend credits.

`ArtifactStore` saves local JSON. Its default `store_prompts=False` removes raw prompt fields from **saved evidence** and records count plus hashes; `store_prompts=True` explicitly persists them. This is field-level redaction, not an encryption or comprehensive sensitive-data scrub. Error strings, diagnosis prose, experiment rationale, or other free-text fields may still contain sensitive information. Doctor read-only tools can send prompts held in the in-memory evidence bundle to the reasoning model. Review artifacts before sharing or committing them.

Manifest SHA-256 values detect changes to listed JSON payloads. They are not signatures, access controls, encryption, or proof of provider origin. Local files inherit your filesystem permissions; InferDoc does not provide remote storage or retention management. `.inferdoc/`, `.env`, build output, and caches are ignored by Git, but inspect `git status` before committing.

For a public demonstration, prefer the sanitized [offline example artifacts](../examples/demo_artifacts/README.md). See [artifacts](artifacts.md) and [limitations](limitations.md).
