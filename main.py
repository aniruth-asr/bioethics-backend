from dotenv import load_dotenv
load_dotenv()

import logging
import time
import os
import threading
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
from threading import Thread

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model_ready, _startup_time
    _startup_time = time.time()

    logger.info("🚀 Starting BioEthics Radar (non-blocking)...")

    def background_warmup():
        global _model_ready
        try:
            from engine.pipeline import warmup_model
            success = warmup_model()
            _model_ready = success
            logger.info(f"Warmup complete: {success}")
        except Exception as e:
            logger.error(f"Warmup failed: {e}")
            _model_ready = False

    Thread(target=background_warmup).start()

    yield


# ---------------- APP ----------------
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- VALIDATION ----------------
def validate_file(file_bytes, filename):
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF allowed")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")


# ---------------- REQUEST MODEL ----------------
class TextAuditRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=MAX_TEXT_SIZE)


# ---------------- ROUTES ----------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_ready": _model_ready,
        "uptime": round(time.time() - _startup_time, 1)
    }


@app.post("/api/audit")
async def audit_text(body: TextAuditRequest):
    try:
        print("🚀 API HIT")
        from engine.pipeline import run_full_pipeline

        print("⚙️ Running pipeline...")
        result = run_full_pipeline(body.text)

        print("✅ PIPELINE RESULT:", result)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()   # 🔥 THIS IS KEY

        return {
            "error": str(e),
            "total_score": 0,
            "status": "ERROR",
            "results": []
        }


@app.post("/api/audit/file")
async def audit_file(file: UploadFile = File(...)):
    try:
        from engine.pipeline import run_pipeline_on_file

        file_bytes = await file.read()
        validate_file(file_bytes, file.filename)

        result = run_pipeline_on_file(file_bytes, file.filename)
        print("API RESPONSE:", result)
        return result

    except Exception as e:
        print("FILE ERROR:", e)
        return {
            "total_score": 0,
            "status": "ERROR",
            "results": []
        }


# ---------------- ENTRYPOINT ----------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))  
    uvicorn.run("main:app", host="0.0.0.0", port=port)