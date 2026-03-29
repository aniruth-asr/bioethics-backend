from dotenv import load_dotenv
load_dotenv()

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------- CONFIG ----------------
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_TEXT_SIZE = 50000

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bioethics_radar")

# ---------------- STARTUP STATE ----------------
_model_ready = False
_startup_time = None

# ---------------- LIFESPAN ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model_ready, _startup_time
    _startup_time = time.time()

    logger.info(" Starting BioEthics Radar...")

    try:
        from engine.pipeline import warmup_model

        # SAFE MODEL LOAD
        _model_ready = warmup_model()

        logger.info(" Model READY")

    except Exception as e:
        logger.error(f" Warmup failed: {e}")

        # DO NOT CRASH SERVER
        _model_ready = False

    yield

    logger.info(" Shutting down...")

# ---------------- APP ----------------
app = FastAPI(lifespan=lifespan)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #  tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- VALIDATION ----------------
def validate_file(file_bytes, filename):
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

# ---------------- MODELS ----------------
class TextAuditRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=MAX_TEXT_SIZE)

# ---------------- ROUTES ----------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_ready": _model_ready,
        "uptime": round(time.time() - _startup_time, 1) if _startup_time else 0
    }

@app.post("/api/audit")
async def audit_text(body: TextAuditRequest):
    try:
        from engine.pipeline import run_full_pipeline

        result = run_full_pipeline(body.text)

        logger.info(f"API RESPONSE: {result}")
        return result

    except Exception as e:
        logger.error(f"TEXT ERROR: {e}")

        return {
            "total_score": 0,
            "status": "ERROR",
            "results": []
        }

@app.post("/api/audit/file")
async def audit_file(file: UploadFile = File(...)):
    try:
        from engine.pipeline import run_pipeline_on_file

        file_bytes = await file.read()

        # VALIDATION ADDED (you missed calling it)
        validate_file(file_bytes, file.filename)

        result = run_pipeline_on_file(file_bytes, file.filename)

        logger.info(f"API RESPONSE: {result}")
        return result

    except Exception as e:
        logger.error(f"FILE ERROR: {e}")

        return {
            "total_score": 0,
            "status": "ERROR",
            "results": []
        }

# ---------------- LOCAL RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)