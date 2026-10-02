"""InferDoc: evidence-driven inference engineering for Nebius Token Factory."""

from .benchmark.runner import AsyncBenchmarkRunner, BenchmarkLimits, benchmark
from .config import InferDocSettings
from .doctor.agent import DoctorAgent, diagnose
from .evidence.models import EvidenceBundle
from .experiments.models import ExperimentSpec
from .experiments.policy import AdmissionDecision, BackendCapabilities, validate_experiment
from .nebius.client import NebiusClient, chat
from .nebius.observability import ObservabilitySnapshot, UnsupportedObservabilityAdapter
from .verification.verifier import VerificationReport, VerificationStatus, verify

__all__ = [
    "AdmissionDecision",
    "AsyncBenchmarkRunner",
    "BackendCapabilities",
    "BenchmarkLimits",
    "DoctorAgent",
    "EvidenceBundle",
    "ExperimentSpec",
    "InferDocSettings",
    "NebiusClient",
    "ObservabilitySnapshot",
    "UnsupportedObservabilityAdapter",
    "VerificationReport",
    "VerificationStatus",
    "benchmark",
    "chat",
    "diagnose",
    "validate_experiment",
    "verify",
]

__version__ = "0.1.0"
