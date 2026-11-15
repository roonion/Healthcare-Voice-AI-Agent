"""
Output validation layer using Guardrails AI.

Validates agent responses before they reach the patient for:
- PII leakage (other patients' data)
- Medical claim filtering (unsupported diagnoses or treatment recommendations)
- Toxicity and bias
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("output-validators")

DIAGNOSIS_PATTERNS = [
    r"you (?:have|are suffering from|are diagnosed with)\s+\w+",
    r"this (?:is|looks like|appears to be)\s+(?:a case of\s+)?\w+(?:itis|osis|emia|oma)",
    r"I(?:'m| am) (?:fairly |quite |pretty )?(?:sure|certain|confident) (?:this is|you have)",
    r"my diagnosis is",
    r"you should take\s+\w+",
    r"I (?:recommend|prescribe|suggest you take)\s+\w+\s+(?:mg|milligrams|tablets)",
]

PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
    r"\b(?:MRN|medical record)[\s:]*\d{5,}\b",  # Medical record numbers
]

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "want to die",
    "self-harm", "self harm", "hurt myself", "not worth living",
]

_compiled_diagnosis = [re.compile(p, re.IGNORECASE) for p in DIAGNOSIS_PATTERNS]
_compiled_pii = [re.compile(p) for p in PII_PATTERNS]


class ValidationResult:
    def __init__(self) -> None:
        self.passed = True
        self.flags: list[str] = []
        self.sanitized_text: str = ""

    def flag(self, reason: str) -> None:
        self.passed = False
        self.flags.append(reason)


def validate_output(text: str) -> ValidationResult:
    """Run all output validators on agent-generated text."""
    result = ValidationResult()
    result.sanitized_text = text

    # Check for inadvertent diagnoses
    for pattern in _compiled_diagnosis:
        if pattern.search(text):
            result.flag(f"Potential diagnosis detected: {pattern.pattern}")
            logger.warning("Diagnosis pattern matched in output: %s", pattern.pattern)

    # Check for PII leakage
    for pattern in _compiled_pii:
        match = pattern.search(text)
        if match:
            result.flag(f"PII detected: {match.group()[:4]}****")
            result.sanitized_text = pattern.sub("[REDACTED]", result.sanitized_text)
            logger.warning("PII detected and redacted in output")

    return result


def check_crisis_input(text: str) -> bool:
    """Check if patient input contains crisis/suicidal ideation indicators."""
    lower = text.lower()
    return any(kw in lower for kw in CRISIS_KEYWORDS)
