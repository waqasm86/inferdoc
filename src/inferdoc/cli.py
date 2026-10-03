from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .benchmark.runner import benchmark
from .benchmark.workload import WorkloadSpec
from .config import InferDocSettings
from .evidence.models import EvidenceBundle
from .experiments.capabilities import TOKEN_FACTORY_CAPABILITIES
from .experiments.models import ExperimentSpec
from .experiments.policy import validate_experiment
from .storage.artifacts import ArtifactStore


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


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
    bench.add_argument("--concurrency", type=_positive_int, default=1)
    bench.add_argument("--max-tokens", type=_positive_int, default=64)
    bench.add_argument("--stream", action="store_true", help="opt in to TTFT measurement; token usage may be unavailable")
    bench.add_argument("--artifact-dir", default=None)

    closed = sub.add_parser("closed-loop", help="measure, diagnose, rerun, and verify one experiment")
    closed.add_argument("--prompt", action="append", default=[], help="repeat for multiple prompts")
    closed.add_argument("--prompts-file", type=Path, help="one prompt per nonempty line")
    closed.add_argument("--model", default=None)
    closed.add_argument("--concurrency", type=_positive_int, default=1)
    closed.add_argument("--max-tokens", type=_positive_int, default=64)
    closed.add_argument("--temperature", type=float, default=0.0)
    closed.add_argument("--stream", action="store_true")
    closed.add_argument("--enable-thinking", action="store_true")
    closed.add_argument("--artifact-dir", default=None)

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
            stream=args.stream,
        )
        path = ArtifactStore(settings.artifact_dir).save(bundle)
        print(
            json.dumps(
                {"run_id": bundle.run_id, "evidence": str(path), "aggregate": bundle.aggregate},
                indent=2,
            )
        )
        return 0
    if args.command == "closed-loop":
        prompts = list(args.prompt)
        if args.prompts_file is not None:
            try:
                prompts.extend(line.strip() for line in args.prompts_file.read_text(encoding="utf-8").splitlines() if line.strip())
            except OSError as exc:
                print(f"cannot read prompts file: {type(exc).__name__}", file=sys.stderr)
                return 1
        if not prompts:
            parser = _parser()
            parser.error("closed-loop requires --prompt or --prompts-file")
        try:
            workload = WorkloadSpec(
                prompts=prompts,
                concurrency=args.concurrency,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                stream=args.stream,
                enable_thinking=args.enable_thinking,
            )
            settings.require_api_key()
            from .nebius.client import NebiusClient
            from .workflows import run_closed_loop

            async def execute():
                client = NebiusClient(settings=settings)
                try:
                    return await run_closed_loop(
                        client=client,
                        workload=workload,
                        model=args.model or settings.default_model,
                        artifact_store=ArtifactStore(settings.artifact_dir),
                    )
                finally:
                    await client.aclose()

            result = asyncio.run(execute())
        except Exception as exc:
            print(f"closed-loop failed: {type(exc).__name__}", file=sys.stderr)
            return 1
        experiment = result.diagnosis.experiment
        print(json.dumps({
            "baseline_run_id": result.baseline.run_id,
            "candidate_run_id": result.candidate.run_id if result.candidate else None,
            "experiment_id": experiment.id if experiment else None,
            "admission_approved": result.admission.approved if result.admission else None,
            "verification_status": result.verification.status if result.verification else None,
            "metric_results": [metric.model_dump(mode="json") for metric in result.verification.metric_results] if result.verification else [],
            "artifact_dir": str(settings.artifact_dir),
        }, indent=2))
        return 2 if result.admission is not None and not result.admission.approved else 0
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
