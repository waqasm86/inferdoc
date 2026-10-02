from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .benchmark.runner import benchmark
from .config import InferDocSettings
from .evidence.models import EvidenceBundle
from .experiments.capabilities import TOKEN_FACTORY_CAPABILITIES
from .experiments.models import ExperimentSpec
from .experiments.policy import validate_experiment
from .storage.artifacts import ArtifactStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inferdoc", description="Evidence-driven Nebius inference doctor"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("chat", help="send one prompt to Token Factory")
    chat.add_argument("prompt")
    chat.add_argument("--model", default=None)
    chat.add_argument("--max-tokens", type=int, default=64)

    bench = sub.add_parser("bench", help="run a bounded benchmark and persist evidence")
    bench.add_argument("prompts", nargs="+", help="one or more prompts")
    bench.add_argument("--model", default=None)
    bench.add_argument("--concurrency", type=int, default=1)
    bench.add_argument("--max-tokens", type=int, default=64)
    bench.add_argument("--no-stream", action="store_true")
    bench.add_argument("--artifact-dir", default=None)

    runs = sub.add_parser("runs", help="list locally persisted runs")
    runs.add_argument("--artifact-dir", default=None)

    validate = sub.add_parser(
        "validate", help="admit an ExperimentSpec against Token Factory capabilities"
    )
    validate.add_argument("experiment", type=Path)
    validate.add_argument("--baseline", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = InferDocSettings.from_env(artifact_dir=getattr(args, "artifact_dir", None))
    if args.command == "chat":
        from .nebius.client import chat

        result = chat(model=args.model, prompt=args.prompt, max_tokens=args.max_tokens)
        print(result.text)
        return 0
    if args.command == "bench":
        bundle = benchmark(
            model=args.model,
            prompts=args.prompts,
            concurrency=args.concurrency,
            max_tokens=args.max_tokens,
            stream=not args.no_stream,
        )
        path = ArtifactStore(settings.artifact_dir).save(bundle)
        print(
            json.dumps(
                {"run_id": bundle.run_id, "evidence": str(path), "aggregate": bundle.aggregate},
                indent=2,
            )
        )
        return 0
    if args.command == "runs":
        print("\n".join(ArtifactStore(settings.artifact_dir).list_runs()))
        return 0
    if args.command == "validate":
        experiment = ExperimentSpec.model_validate_json(args.experiment.read_text(encoding="utf-8"))
        baseline = EvidenceBundle.model_validate_json(args.baseline.read_text(encoding="utf-8"))
        decision = validate_experiment(experiment, TOKEN_FACTORY_CAPABILITIES, baseline=baseline)
        print(decision.model_dump_json(indent=2))
        return 0 if decision.approved else 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
