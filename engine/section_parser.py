import re
from dataclasses import dataclass

# ---------------- DATA STRUCT ----------------
@dataclass
class DocumentSection:
    name: str
    raw_heading: str
    text: str
    weight: float
    char_start: int
    char_end: int


# ---------------- CONSTANTS ----------------
MAX_TEXT_SIZE = 50000

SECTION_WEIGHTS = {
    "abstract": 1.5,
    "introduction": 0.8,
    "background": 0.8,
    "methods": 2.0,
    "methodology": 2.0,
    "materials": 2.0,
    "results": 1.0,
    "discussion": 1.2,
    "conclusion": 1.0,
    "supplementary": 1.0,
    "ethics": 2.5,
    "safety": 2.0,
    "data availability": 1.8,
    "limitations": 0.7,
    "references": 0.0,
    "acknowledgements": 0.3,
    "unknown": 0.9,
}

_HEADING_PATTERNS = [
    re.compile(r'^(?:\d+\.?)+\s+([A-Z][^\n]{2,60})$', re.MULTILINE),
    re.compile(r'^([A-Z][A-Z\s&/]{3,50})$', re.MULTILINE),
    re.compile(r'^([A-Z][a-z].{2,50})$', re.MULTILINE),
]

_SECTION_KEYWORDS = {
    "abstract": ["abstract"],
    "introduction": ["introduction", "background"],
    "methods": ["method", "protocol", "procedure"],
    "results": ["result", "finding"],
    "discussion": ["discussion"],
    "conclusion": ["conclusion"],
    "ethics": ["ethic", "consent", "approval", "irb"],
    "safety": ["safety", "biosafety", "biosecurity"],
}


# ---------------- HELPERS ----------------
def _normalize_section_name(heading: str):
    h = re.sub(r'^[\d.]+\s*', '', heading.lower()).strip()

    for canonical, keywords in _SECTION_KEYWORDS.items():
        if any(k in h for k in keywords):
            return canonical, SECTION_WEIGHTS.get(canonical, 0.9)

    return "unknown", SECTION_WEIGHTS["unknown"]


def _find_headings(text: str):
    results = {}

    for pattern in _HEADING_PATTERNS:
        for m in pattern.finditer(text):
            heading = m.group(1).strip() if m.lastindex else m.group(0).strip()
            if 3 <= len(heading) <= 80:
                results[m.start()] = heading

    return sorted(results.items())


# ---------------- MAIN ----------------
def parse_sections(text: str):
    # 🔒 HARD LIMIT (FIXED HERE)
    if len(text) > MAX_TEXT_SIZE:
        text = text[:MAX_TEXT_SIZE]

    if not text or len(text.strip()) < 50:
        return [DocumentSection(
            name="abstract",
            raw_heading="Full Text",
            text=text.strip(),
            weight=1.5,
            char_start=0,
            char_end=len(text),
        )]

    headings = _find_headings(text)

    if len(headings) < 2:
        return _fallback(text)

    sections = []

    for i, (pos, heading) in enumerate(headings):
        name, weight = _normalize_section_name(heading)

        next_pos = headings[i + 1][0] if i + 1 < len(headings) else len(text)

        body_start = pos + len(heading)
        while body_start < len(text) and text[body_start] in ('\n', ' '):
            body_start += 1

        body = text[body_start:next_pos].strip()

        if len(body) < 20:
            continue

        sections.append(DocumentSection(
            name=name,
            raw_heading=heading,
            text=body,
            weight=weight,
            char_start=body_start,
            char_end=next_pos,
        ))

    return sections if sections else _fallback(text)


# ---------------- FALLBACK ----------------
def _fallback(text: str):
    words = text.split()
    size = len(words)

    if size < 50:
        return [DocumentSection(
            name="abstract",
            raw_heading="Full Text",
            text=text,
            weight=1.5,
            char_start=0,
            char_end=len(text),
        )]

    split = size // 3

    parts = [
        ("abstract", words[:split], 1.5),
        ("methods", words[split:2*split], 2.0),
        ("discussion", words[2*split:], 1.2),
    ]

    sections = []
    offset = 0

    for name, wlist, weight in parts:
        t = " ".join(wlist)
        sections.append(DocumentSection(
            name=name,
            raw_heading=name,
            text=t,
            weight=weight,
            char_start=offset,
            char_end=offset + len(t),
        ))
        offset += len(t)

    return sections