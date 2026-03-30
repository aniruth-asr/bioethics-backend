"""
guideline_engine.py — Guideline ingestion for semantic compliance evaluation.

Design goals:
- Clause-level semantic units extracted from guideline PDFs (pdfplumber).
- Deterministic pillar mapping using semantic prototypes (no keyword buckets).
- Metadata retained for explainability (source PDF, page number, clause index).
- No persistence: everything is loaded from local guideline PDFs at startup.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pdfplumber

# Canonical pillars (frontend depends on these names)
PILLARS: Dict[str, str] = {
    "biosafety": "Biosafety & Biosecurity",
    "consent": "Informed Consent & Welfare",
    "environmental": "Environmental Stewardship",
    "data": "Data Privacy & Ethics",
    "justice": "Justice & Research Equity",
}

# Pillar prototypes used to map guideline clauses to pillars semantically.
# Keep short, high-signal, and stable for deterministic behavior.
PILLAR_PROTOTYPES: Dict[str, List[str]] = {
    "biosafety": [
        "laboratory biosafety containment levels and facility controls for pathogens",
        "biosecurity, dual-use research of concern, and institutional biosafety oversight",
        "prohibited weaponization of biological agents and toxins; peaceful purpose requirement",
    ],
    "consent": [
        "informed consent, ethics committee approval, and participant welfare protections",
        "animal welfare, 3Rs principles, and institutional animal care oversight",
    ],
    "environmental": [
        "environmental risk assessment and containment for living modified organisms",
        "biodiversity protection, monitoring, and transboundary movement risk management",
    ],
    "data": [
        "health data privacy, confidentiality, de-identification, and secure access controls",
        "ethical governance for personal and genomic data processing, retention, and sharing",
    ],
    "justice": [
        "justice, equity, benefit sharing, and fair distribution of research benefits and burdens",
        "community engagement, inclusion, and avoiding exploitation of vulnerable populations",
    ],
}


@dataclass(frozen=True)
class GuidelineClause:
    pillar: str
    text: str
    source_pdf: str
    page: int
    clause_id: str
    embedding: np.ndarray


_WS_RE = re.compile(r"\s+")
_BULLET_RE = re.compile(r"^\s*(?:[-–•·*]|\(\d+\)|\d+\)|\d+\.|[A-Za-z]\))\s+")
_HARD_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _clean_line(s: str) -> str:
    s = _WS_RE.sub(" ", (s or "").strip())
    # Normalize common PDF artifacts without changing meaning
    s = s.replace("\u00ad", "")  # soft hyphen
    return s.strip()


def _iter_pdf_pages(path: Path) -> Iterable[Tuple[int, str]]:
    with pdfplumber.open(io.BytesIO(path.read_bytes())) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            t = page.extract_text() or ""
            t = t.replace("\r", "\n")
            t = _clean_line(t) if "\n" not in t else "\n".join(_clean_line(x) for x in t.split("\n"))
            if t.strip():
                yield i, t


def _split_into_clauses(page_text: str) -> List[str]:
    """
    Split a page into clause-like units suitable for embedding.

    Strategy (deterministic):
    - Prefer bullet/number lines as separate units.
    - Otherwise split by sentence boundaries.
    - Keep only medium-length units (avoid headers and giant paragraphs).
    """
    if not page_text or not page_text.strip():
        return []

    lines = [ln.strip() for ln in page_text.split("\n") if ln.strip()]
    units: List[str] = []

    buf: List[str] = []
    buf_is_bullet = False

    def flush_buf():
        nonlocal buf, buf_is_bullet
        if not buf:
            return
        text = _clean_line(" ".join(buf))
        if text:
            units.append(text)
        buf = []
        buf_is_bullet = False

    for ln in lines:
        is_bullet = bool(_BULLET_RE.match(ln))
        ln_clean = _clean_line(_BULLET_RE.sub("", ln) if is_bullet else ln)
        if not ln_clean:
            continue

        # New bullet starts a new unit
        if is_bullet:
            flush_buf()
            buf.append(ln_clean)
            buf_is_bullet = True
            continue

        # Non-bullet line: append to current buffer if it looks like continuation
        if buf and buf_is_bullet:
            # Continuation lines for bullet items (often wrapped in PDFs)
            buf.append(ln_clean)
            continue

        # Non-bullet, non-bullet buffer: accumulate paragraphs but avoid huge blobs
        if not buf:
            buf.append(ln_clean)
        else:
            # If line looks like a new heading, flush and start new buffer
            if len(ln_clean) <= 60 and ln_clean.isupper():
                flush_buf()
                buf.append(ln_clean)
            else:
                buf.append(ln_clean)

        # Flush if buffer becomes very long
        if sum(len(x) for x in buf) > 1500:
            flush_buf()

    flush_buf()

    # Sentence-split each unit if it's still long
    clauses: List[str] = []
    for u in units:
        u = _clean_line(u)
        if len(u) <= 220:
            clauses.append(u)
            continue
        parts = [p.strip() for p in _HARD_SPLIT_RE.split(u) if p.strip()]
        if len(parts) <= 1:
            clauses.append(u)
        else:
            clauses.extend(parts)

    # Length filter: retain semantically meaningful clauses
    out = []
    for c in clauses:
        c = _clean_line(c)
        if 60 <= len(c) <= 700:
            out.append(c)
    return out


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def load_guideline_clauses(encoder, guidelines_dir: Path) -> Dict[str, List[GuidelineClause]]:
    """
    Load all guideline PDFs from `guidelines_dir` and return clauses mapped to pillars.

    Returns dict[pillar_id] -> List[GuidelineClause]. Empty lists when PDFs missing.
    """
    print("ENCODER:", type(encoder))
    print("PATH:", type(guidelines_dir))
    
    clauses_by_pillar: Dict[str, List[GuidelineClause]] = {k: [] for k in PILLARS}
    if not guidelines_dir.exists():
        return clauses_by_pillar

    pdfs = sorted(guidelines_dir.glob("*.pdf"), key=lambda p: p.name.lower())
    if not pdfs:
        return clauses_by_pillar

    # Pre-embed prototypes once (deterministic, same model used throughout)
    proto_embeddings = {
        pid: encoder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        for pid, texts in PILLAR_PROTOTYPES.items()
    }

    for pdf_path in pdfs:
        print("LOADING PDF:", pdf_path)
        page_units: List[Tuple[int, str]] = []
        text_length = 0
        for page_num, page_text in _iter_pdf_pages(pdf_path):
            text_length += len(page_text)
            for clause in _split_into_clauses(page_text):
                page_units.append((page_num, clause))

        print("TEXT LENGTH:", text_length)

        if not page_units:
            continue

        texts = [t for _, t in page_units]
        embs = encoder.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        for idx, ((page_num, clause_text), emb) in enumerate(zip(page_units, embs)):
            best_pillar = "biosafety"
            best_score = -1.0

            for pid, proto_embs in proto_embeddings.items():
                # clause-to-prototype: max similarity across that pillar's prototypes
                score = max(_cosine(emb, p) for p in proto_embs)
                if score > best_score:
                    best_score = score
                    best_pillar = pid

            clause_id = f"{pdf_path.stem}:{page_num}:{idx+1}"
            clauses_by_pillar[best_pillar].append(
                GuidelineClause(
                    pillar=best_pillar,
                    text=clause_text,
                    source_pdf=pdf_path.name,
                    page=page_num,
                    clause_id=clause_id,
                    embedding=emb,
                )
            )

    # Stable sort for reproducibility
    for pid in clauses_by_pillar:
        clauses_by_pillar[pid].sort(key=lambda c: (c.source_pdf.lower(), c.page, c.clause_id))
    return clauses_by_pillar
