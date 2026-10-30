
"""
MemoryMedic AI 2.0
FastAPI Backend Application

This application provides:
- API information
- Health checks
- Historical process telemetry
- Machine-learning memory-leak predictions

The backend connects MemoryMedic's monitoring data
to its trained machine-learning prediction pipeline.
"""

from datetime import datetime, timezone

from fastapi import FastAPI

# Import historical memory metrics endpoints.
from backend.app.metrics import router as metrics_router

# Import machine-learning prediction endpoints.
from backend.app.predictions import router as predictions_router


# --------------------------------------------------
# Initialize MemoryMedic AI FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="MemoryMedic AI API",
    description=(
        "MemoryMedic AI 2.0 provides system health "
        "monitoring, historical memory telemetry, "
        "and machine-learning anomaly detection."
    ),
    version="2.0.0",
)


# --------------------------------------------------
# Register API Routers
# --------------------------------------------------

# Historical memory telemetry
# GET /api/v1/metrics
app.include_router(metrics_router)

# Machine-learning memory leak prediction
# POST /api/v1/predict
app.include_router(predictions_router)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/", tags=["System"])
def root():
    """Return basic information about MemoryMedic AI."""

    return {
        "project": "MemoryMedic AI",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
    }


# --------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    """Check whether the FastAPI service is responding."""

    return {
        "status": "healthy",
        "service": "memorymedic-api",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }
