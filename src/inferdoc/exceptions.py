class InferDocError(Exception):
    """Base exception for InferDoc."""


class ConfigurationError(InferDocError):
    """Configuration is missing or invalid."""


class BackendError(InferDocError):
    """The inference backend rejected or failed a request."""


class AdmissionError(InferDocError):
    """An experiment cannot be executed under backend capabilities or policy."""


class EvidenceError(InferDocError):
    """Evidence is malformed, incomplete, or not comparable."""
