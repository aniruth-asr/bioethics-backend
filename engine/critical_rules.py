"""
critical_rules.py — deterministic hard overrides (no hallucination).

Requirements implemented:
- Explicit weaponization intent forces FAIL (overall score -> 0).
- Unsafe gain-of-function (GOF) caps score (does not auto-zero).
- Avoid false positives: discussion/mitigation/anti-weaponization language should not trigger.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class OverrideResult:
    forced_fail: bool
    score_cap: int | None  # cap overall score to <= this value
    findings: List[dict]


_WS_RE = re.compile(r"\s+")

# Broad detectors (high recall)
_GOF_TERMS = re.compile(
    r"\b(gain[- ]of[- ]function|go[- ]?f|enhanced\s+transmissibility|increased\s+virulence|host\s+range\s+expansion)\b",
    re.IGNORECASE,
)
_WEAPON_TERMS = re.compile(
    r"\b(weaponiz(?:e|ed|ing|ation)?|biological\s+weapon|bioweapon|offensive\s+biological\s+(?:program|capability))\b",
    re.IGNORECASE,
)

# Contextual intent (precision): verbs that indicate building/optimizing offensive capability
_INTENT_VERBS = re.compile(
    r"\b(develop|design|engineer|optimi[sz]e|produce|increase|maximi[sz]e|enhance|improve|weaponiz(?:e|ed|ing|ation))\b",
    re.IGNORECASE,
)

# Negation / prevention language (to avoid false positives when discussing governance)
_ANTI_WEAPON_CONTEXT = re.compile(
    r"\b(prevent|prohibit|ban|against|mitigat(?:e|ion)|reduce|avoid|guard(?:rail)?s?|deterr(?:ence|ent))\b",
    re.IGNORECASE,
)

# Safety/oversight indicators used as GOF mitigators
_GOF_SAFETY = re.compile(
    r"\b(BSL[- ]?[34]|biosafety\s+level\s+[34]|IBC\s+approval|institutional\s+biosafety\s+committee|DURC\s+review|NSABB|select\s+agent|HHS\s+P3CO)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", (text or "")).strip()


def _window(text: str, m: re.Match, radius: int = 160) -> str:
    start = max(0, m.start() - radius)
    end = min(len(text), m.end() + radius)
    return text[start:end]


def _weaponization_intent(text: str) -> bool:
    """
    Force FAIL only when the document indicates offensive intent,
    not when it discusses prohibitions, governance, or risk mitigation.
    """
    for m in _WEAPON_TERMS.finditer(text):
        w = _window(text, m, radius=220)
        # If the local window is clearly about prevention, do not trigger
        if _ANTI_WEAPON_CONTEXT.search(w) and not _INTENT_VERBS.search(w):
            continue
        # Require some "intent" verb near weapon terms
        if _INTENT_VERBS.search(w):
            return True
    return False


def _unsafe_gof(text: str) -> bool:
    """
    Unsafe GOF = GOF mentioned without explicit containment/oversight cues.
    If safety cues exist anywhere, treat as mitigated (cap is looser / none).
    """
    if not _GOF_TERMS.search(text):
        return False
    return not bool(_GOF_SAFETY.search(text))


def evaluate_overrides(overall_score: int, text: str) -> OverrideResult:
    text_n = _normalize(text)
    findings: List[dict] = []

    if _weaponization_intent(text_n):
        findings.append(
            {"type": "risk", "text": "Critical override: explicit weaponization intent detected. Forced FAIL."}
        )
        return OverrideResult(forced_fail=True, score_cap=0, findings=findings)

    if _unsafe_gof(text_n):
        # Cap (but do not zero). Keep cap consistent with requested bands:
        # unsafe GOF should not reach "PERFECT" or "RULEBOOK LEVEL".
        cap = 40  # max overall score (still "FAIL/OKAY" region)
        if overall_score > cap:
            findings.append(
                {
                    "type": "risk",
                    "text": "Critical override: gain-of-function content without explicit biosafety/oversight. Score capped.",
                }
            )
        return OverrideResult(forced_fail=False, score_cap=cap, findings=findings)

    return OverrideResult(forced_fail=False, score_cap=None, findings=findings)


def apply_global_overrides(total_score: int, text: str) -> Tuple[int, List[dict], bool]:
    """
    Backwards-compatible wrapper used by the pipeline.
    Returns: (score_after_overrides, findings, force_fail)
    """
    res = evaluate_overrides(total_score, text)
    if res.score_cap is not None:
        total_score = min(total_score, int(res.score_cap))
    force_fail = bool(res.forced_fail)
    if force_fail:
        total_score = 0
    return int(total_score), list(res.findings), force_fail
