"""Conservative, best-effort PHI scrubbing for text leaving the server.

Targets patient identifiers (ages, record/ID numbers, contacts, explicit
'patient <Name>') WITHOUT touching legitimate domain text (KOL names, drug
names, indications). This is defense-in-depth, NOT a HIPAA-grade guarantee.
"""
import re
from typing import Optional

_PATTERNS = [
    (re.compile(r"\b\d{1,3}\s*[- ]?\s*(?:year|yr|y/o|yo|years?[- ]old)\b", re.I), "[AGE]"),
    (re.compile(r"\bMRN[:#\s]*\d+\b", re.I), "[MRN]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"\b\+?\d[\d\-\s().]{7,}\d\b"), "[PHONE]"),
    (re.compile(r"\bpatient\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?"), "patient [NAME]"),
]


def deidentify(text: Optional[str]) -> str:
    if not text:
        return ""
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out
