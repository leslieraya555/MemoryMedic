
"""MemoryMedic AI 2.0 — FastAPI backend."""

from datetime import datetime, timezone

from fastapi import FastAPI

from backend.app.metrics import router as metrics_router


app = FastAPI(
    title="MemoryMedic AI API",
    description=(
        "System health, memory monitoring, "
        "and AI anomaly detection."
    ),
    version="2.0.0",
)

# Connect the MemoryMedic metrics endpoints.
app.include_router(metrics_router)


@app.get("/")
def root():
    return {
        "project": "MemoryMedic AI",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "memorymedic-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
