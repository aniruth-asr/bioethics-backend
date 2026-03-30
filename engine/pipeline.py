from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
import pdfplumber

from .critical_rules import apply_global_overrides
from .guideline_engine import GuidelineClause, PILLARS, load_guideline_clauses
from .section_parser import parse_sections
from .llm_extractor import extract_with_llm

logger = logging.getLogger(__name__)

_sentence_transformer = None
_model_name = "sentence-transformers/all-MiniLM-L6-v2"
_guideline_cache: Dict[str, List[GuidelineClause]] = {pid: [] for pid in PILLARS.keys()}


# ---------------- MODEL ----------------
def get_encoder():
    global _sentence_transformer
    if _sentence_transformer is None:
        from sentence_transformers import SentenceTransformer
        _sentence_transformer = SentenceTransformer(_model_name)
    return _sentence_transformer


# ---------------- SAFETY ----------------
def safe_text(t: str) -> str:
    return t.replace("<", "").replace(">", "")


# ---------------- TEXT EXTRACTION ----------------
def extract_text(file_bytes: bytes, filename: str) -> str:
    try:
        if filename.lower().endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        else:
            text = file_bytes.decode("utf-8", errors="ignore")

        return text[:50000]  # HARD LIMIT

    except Exception:
        raise Exception("Invalid or corrupted file")


# ---------------- SEMANTIC MATCHING ----------------
def _clause_coverage(chunk_embs: np.ndarray, clauses: Sequence[GuidelineClause]):
    if chunk_embs.size == 0 or not clauses:
        return 0.0, 0.0, []

    clause_embs = np.vstack([c.embedding for c in clauses])

    sims = (chunk_embs @ clause_embs.T)
    sims /= (np.linalg.norm(chunk_embs, axis=1, keepdims=True) + 1e-12)
    sims /= (np.linalg.norm(clause_embs, axis=1) + 1e-12)

    best = np.max(sims, axis=0)

    clause_sims = list(zip(clauses, best.tolist()))
    clause_sims.sort(key=lambda x: -x[1])

    satisfied = [s for _, s in clause_sims if s > 0.38]
    partial = [s for _, s in clause_sims if 0.30 <= s <= 0.38]

    addressed = satisfied + partial

    coverage = min(1.0, (len(addressed) / max(1, len(clause_sims))) ** 0.5 * 6.5)

    quality = 0.0
    if addressed:
        quality = (sum(addressed) / len(addressed) - 0.30) / 0.20
        quality = max(0.0, min(1.0, quality))

    return coverage, quality, clause_sims


# ---------------- SCORING ----------------
def _pillar_score(coverage, quality):
    score = 60 * (0.45 * coverage + 0.55 * quality)

    if quality > 0.40:
        score = max(score, 45)
    elif quality > 0.30:
        score = max(score, 30)

    return int(max(0, min(60, score)))


def _status(score):
    if score >= 52: return "RULEBOOK LEVEL"
    if score >= 42: return "PERFECT"
    if score >= 32: return "GOOD"
    if score >= 22: return "OKAY"
    return "FAIL"


# ---------------- MAIN PIPELINE ----------------
def run_full_pipeline(text: str, llm_data: dict = None):
    encoder = get_encoder()
    sections = parse_sections(text)

    embeddings = np.vstack([
        encoder.encode([s.text], convert_to_numpy=True)[0]
        for s in sections
    ]) if sections else np.array([])

    results = []

    for pid, name in PILLARS.items():
        clauses = _guideline_cache.get(pid, [])
        if not clauses:
            print(f"No clauses loaded for {pid}")

        coverage, quality, sims = _clause_coverage(embeddings, clauses) if clauses else (0, 0, [])

        score = _pillar_score(coverage, quality)

        # ---------------- LLM BOOST ----------------
        if llm_data:
            if llm_data.get("safety_measures"):
                score += 2
            if llm_data.get("oversight_mentions"):
                score += 2

        score = min(60, score)
        
        if score == 0:
            score = 18

        # ---------------- FINDINGS ----------------
        findings = []

        if quality > 0:
            findings.append(f"Semantic alignment: {round(quality, 2)}")

        if coverage > 0:
            findings.append(f"Coverage level: {round(coverage, 2)}")

        if llm_data and llm_data.get("key_points"):
            findings.extend(llm_data["key_points"][:2])

        if not findings:
            findings = ["Ethical signals detected but weak alignment"]

        # ---------------- EVIDENCE ----------------
        evidence = [
            {
                "text": safe_text(c.text),
                "source": c.source_pdf,
                "sim": round(s, 2)
            }
            for c, s in sims[:3] if s > 0.30
        ]

        if not evidence:
            evidence = [{
                "text": "No strong evidence match found",
                "source": "N/A",
                "sim": 0
            }]

        # ---------------- IMPROVEMENTS ----------------
        improvements = []

        if quality < 0.4:
            improvements.append("Improve alignment with ethical guidelines")

        if coverage < 0.3:
            improvements.append("Expand discussion of safety or ethics considerations")

        if not improvements:
            improvements = ["Improve alignment with ethical guidelines"]

        results.append({
            "pillar": pid,
            "name": name,
            "score": score,
            "status": _status(score),
            "findings": findings or ["Basic ethical signals detected"],
            "evidence": [e["text"] for e in evidence] or ["No strong evidence"],
            "improvements": improvements or ["Improve ethical coverage"]
        })

    total = int(sum(r["score"] for r in results) / len(results)) if results else 0
    final_score = total

    print("FINAL OUTPUT:", final_score, len(results))

    return {
        "total_score": final_score,
        "status": _status(final_score),
        "results": results
    }


# ---------------- ENTRY ----------------
def run_pipeline_on_file(file_bytes: bytes, filename: str):
    text = extract_text(file_bytes, filename)

    try:
        llm_data = extract_with_llm(text)
    except Exception as e:
        print("LLM failed:", e)
        llm_data = {}

    return run_full_pipeline(text, llm_data)


# ---------------- INIT ----------------
def warmup_model():
    try:
        encoder = get_encoder()
        
        # Robust path resolution for Render deployment
        base = Path(__file__).resolve().parent.parent
        path = base / "guidelines"
        
        # Fallback to CWD if not found (Render/Docker sometimes alters execution root)
        if not path.exists():
            alt_path = Path.cwd() / "guidelines"
            if alt_path.exists():
                path = alt_path
            elif (Path.cwd() / "backend" / "guidelines").exists():
                path = Path.cwd() / "backend" / "guidelines"

        print("ABS PATH:", path)
        if path.exists():
            print("FILES:", list(path.glob("*")))
        else:
            print("FILES: []")

        _guideline_cache.update(
            load_guideline_clauses(encoder, path)
        )

        sizes = {k: len(v) for k, v in _guideline_cache.items()}
        print("CACHE:", sizes)

        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Warmup failed:", str(e))
        return False