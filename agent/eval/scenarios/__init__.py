from .normal_intake import SCENARIOS as NORMAL_INTAKE
from .emergency_escalation import SCENARIOS as EMERGENCY_ESCALATION
from .edge_cases import SCENARIOS as EDGE_CASES
from .memory_continuity import SCENARIOS as MEMORY_CONTINUITY
from .guardrail_testing import SCENARIOS as GUARDRAIL_TESTING

ALL_SCENARIOS = (
    NORMAL_INTAKE
    + EMERGENCY_ESCALATION
    + EDGE_CASES
    + MEMORY_CONTINUITY
    + GUARDRAIL_TESTING
)
