"""
NexusOps Enterprise Exception Hierarchy
Standardized error types for agent pipeline, guardrail checks, and simulated execution.
"""

from typing import Optional, Dict, Any

class NexusOpsBaseException(Exception):
    """Base class for all NexusOps domain exceptions."""
    def __init__(self, message: str, code: str = "NEXUS_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class TriageException(NexusOpsBaseException):
    """Raised when event parsing, decomposition, or entity extraction fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="TRIAGE_ERROR", details=details)

class PromptInjectionSecurityException(NexusOpsBaseException):
    """Raised when an adversarial prompt injection pattern is detected."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SECURITY_PROMPT_INJECTION", details=details)

class EnrichmentException(NexusOpsBaseException):
    """Raised when telemetry querying fails after retry exhaustion."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ENRICHMENT_ERROR", details=details)

class GuardrailViolationException(NexusOpsBaseException):
    """Raised when an operation attempts to bypass a hard business limit."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="GUARDRAIL_VIOLATION", details=details)

class SimulatedExecutionException(NexusOpsBaseException):
    """Raised when stateful execution against the simulator fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SIMULATOR_EXECUTION_ERROR", details=details)

class AuditChainTamperException(NexusOpsBaseException):
    """Raised when cryptographic audit log hash chain validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUDIT_TAMPER_DETECTED", details=details)
