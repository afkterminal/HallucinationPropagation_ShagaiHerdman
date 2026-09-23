"""
Hallucination Taxonomy - HalluCode / CodeHalu compatible labeling system
Used for classifying hallucinations in the corpus
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

class HallucinationType(Enum):
    """Hallucination type classification"""
    API = "api"
    DEPENDENCY = "dependency"
    LOGIC = "logic"
    SECURITY = "security"
    SYNTAX = "syntax"
    TYPE = "type"
    SEMANTICS = "semantics"
    CONFIG = "config"
    LIBRARY_VERSION = "library_version"

class HallucinationState(Enum):
    """State of hallucination across iterations"""
    PERSIST = "persist"
    MUTATE = "mutate"
    RESOLVE = "resolve"
    MASKED = "masked"
    COMPOUND = "compound"

class Severity(Enum):
    """Severity level of hallucination"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class HallucinationInstance:
    """Single hallucination occurrence"""
    id: str
    task_id: str
    iteration: int
    code_snippet: str
    hallucination_type: HallucinationType
    severity: Severity
    location: str
    description: str
    detected_by: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class HallucinationTrajectory:
    """Complete lifecycle of a single hallucination across iterations"""
    hallucination_id: str
    task_id: str
    instances: List[HallucinationInstance]
    state_transitions: List[tuple]
    persistence_duration: int
    final_state: HallucinationState
    
    def add_instance(self, instance: HallucinationInstance, state: HallucinationState):
        """Track hallucination instance and its state"""
        self.instances.append(instance)
        self.state_transitions.append((instance.iteration, state))
        if state == HallucinationState.RESOLVE:
            self.final_state = state
            self.persistence_duration = instance.iteration - self.instances[0].iteration
    
    def get_trajectory_summary(self) -> dict:
        """Return summary of this hallucination's lifecycle"""
        return {
            "hallucination_id": self.hallucination_id,
            "task_id": self.task_id,
            "type": self.instances[0].hallucination_type.value if self.instances else None,
            "first_iteration": self.instances[0].iteration if self.instances else None,
            "last_iteration": self.instances[-1].iteration if self.instances else None,
            "persistence_duration": self.persistence_duration,
            "final_state": self.final_state.value,
            "state_transitions": self.state_transitions,
            "severity": self.instances[0].severity.value if self.instances else None,
        }

@dataclass
class CorpusMetadata:
    """Metadata for the entire logged-trajectory corpus"""
    corpus_id: str
    seed_benchmark: str
    num_tasks: int
    num_iterations_per_task: int
    llm_model: str
    refinement_harness: str
    date_created: datetime = None
    annotations_complete: bool = False
    
    def __post_init__(self):
        if self.date_created is None:
            self.date_created = datetime.now()

HALLUCINATION_PATTERNS = {
    HallucinationType.API: [
        "non_existent_method",
        "wrong_parameter_count",
        "wrong_module_path",
    ],
    HallucinationType.DEPENDENCY: [
        "non_existent_import",
        "non_existent_package",
        "version_incompatibility",
        "package_squatting",
    ],
    HallucinationType.SECURITY: [
        "sql_injection",
        "command_injection",
        "unsafe_deserialization",
        "hardcoded_credentials",
        "insecure_random",
        "weak_cryptography",
    ],
    HallucinationType.LOGIC: [
        "off_by_one",
        "infinite_loop",
        "unreachable_code",
        "wrong_condition",
    ],
    HallucinationType.SYNTAX: [
        "invalid_syntax",
        "indentation_error",
        "missing_colon",
    ],
}

def get_hallucination_severity(halluc_type: HallucinationType) -> Severity:
    """Infer severity from hallucination type"""
    type_to_severity = {
        HallucinationType.SECURITY: Severity.CRITICAL,
        HallucinationType.DEPENDENCY: Severity.HIGH,
        HallucinationType.API: Severity.HIGH,
        HallucinationType.LOGIC: Severity.HIGH,
        HallucinationType.SYNTAX: Severity.CRITICAL,
        HallucinationType.TYPE: Severity.MEDIUM,
        HallucinationType.SEMANTICS: Severity.MEDIUM,
        HallucinationType.CONFIG: Severity.LOW,
    }
    return type_to_severity.get(halluc_type, Severity.MEDIUM)