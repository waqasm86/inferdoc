"""Reusable measured, diagnosed, admitted, and verified workflow."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ..benchmark.runner import AsyncBenchmarkRunner
from ..benchmark.workload import WorkloadSpec
from ..doctor.agent import DoctorAgent
from ..doctor.models import DiagnosisReport
from ..evidence.models import EvidenceBundle
from ..experiments.capabilities import DEMO_TOKEN_FACTORY_CAPABILITIES
from ..experiments.policy import AdmissionDecision, BackendCapabilities, validate_experiment
from ..experiments.runner import run_experiment
from ..storage.artifacts import ArtifactStore
from ..verification.verifier import VerificationReport, verify


class ClosedLoopResult(BaseModel):
    baseline: EvidenceBundle
    diagnosis: DiagnosisReport
    admission: AdmissionDecision | None = None
    candidate: EvidenceBundle | None = None
    verification: VerificationReport | None = None


async def run_closed_loop(
    *,
    client: Any,
    workload: WorkloadSpec,
    model: str | None = None,
    capabilities: BackendCapabilities = DEMO_TOKEN_FACTORY_CAPABILITIES,
    artifact_store: ArtifactStore | None = None,
) -> ClosedLoopResult:
    """Run one bounded experiment; absence or rejection of a proposal is valid."""
    store = artifact_store or ArtifactStore()
    baseline = await AsyncBenchmarkRunner(client).run(workload, model=model)
    store.save(baseline)
    if not baseline.aggregate["successful_requests"]:
        raise RuntimeError("baseline produced no successful requests")

    diagnosis = await DoctorAgent(client, capabilities=capabilities).adiagnose(baseline)
    store.save_diagnosis(diagnosis, baseline.run_id)
    if diagnosis.experiment is None:
        return ClosedLoopResult(baseline=baseline, diagnosis=diagnosis,
                                admission=diagnosis.admission)

    admission = validate_experiment(
        diagnosis.experiment, capabilities, baseline=baseline, max_changed_variables=1
    )
    if not admission.approved:
        return ClosedLoopResult(baseline=baseline, diagnosis=diagnosis, admission=admission)

    store.save_experiment(diagnosis.experiment, baseline.run_id)
    candidate = await run_experiment(
        diagnosis.experiment, client=client, baseline=baseline, capabilities=capabilities
    )
    store.save(candidate)
    verification = verify(
        baseline=baseline, candidate=candidate, experiment=diagnosis.experiment
    )
    store.save_verification(verification, candidate.run_id)
    store.link_closed_loop(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        experiment_id=diagnosis.experiment.id,
    )
    return ClosedLoopResult(
        baseline=baseline,
        diagnosis=diagnosis,
        admission=admission,
        candidate=candidate,
        verification=verification,
    )
