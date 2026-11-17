"""
FastAPI service exposing dataset inspection and (in later phases) training,
evaluation and prediction. This file intentionally contains no ML logic yet.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import API_HOST, API_PORT, MAX_TEXT_LENGTH, get_dataset_config
from dataset import DatasetError, inspect_dataset
from preprocess import preprocess_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ml-service")

app = FastAPI(
    title="E-Commerce Review Intelligence — ML Service",
    version="0.2.0-phase-b",
    description="Dataset inspection and text preprocessing. Training and prediction arrive in later phases.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # internal service; the Express backend is the public entry point
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DatasetError)
def dataset_error_handler(_req, exc: DatasetError):
    return JSONResponse(status_code=503, content={"error": str(exc), "detail": "dataset_unavailable"})


@app.get("/health")
def health():
    return {"status": "ok", "service": "ml-service", "phase": "B", "ml_trained": False}


@app.get("/models/status")
def models_status():
    """Honest status: no models exist yet in Phase B."""
    return {
        "models_trained": False,
        "trained_models": [],
        "selected_model": None,
        "note": "No models have been trained. Training is implemented in a later phase.",
    }


@app.get("/dataset/inspect")
def dataset_inspect():
    """Factual inspection of the configured CSV. Returns 503 when unavailable."""
    config = get_dataset_config()
    report = inspect_dataset(config)
    status = 200 if report.exists else 503
    return JSONResponse(status_code=status, content={"data": report.to_dict()})


@app.get("/dataset/config")
def dataset_config():
    """Show the active dataset configuration (paths/columns, no data)."""
    config = get_dataset_config()
    return {
        "csv_path": str(config.resolve_csv_path()),
        "review_text_column": config.review_text_column,
        "label_column": config.label_column,
        "product_column": config.product_column,
        "rating_column": config.rating_column,
        "ratings_are_labels": config.ratings_are_labels,
        "expected_classes": list(config.expected_classes),
        "configured_correctly": config.has_required_columns(),
    }


@app.post("/preprocess")
def preprocess_endpoint(payload: dict):
    """Utility endpoint applying the shared preprocessing pipeline to text.
    Useful for debugging the pipeline; not used for predictions yet."""
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Field 'text' (non-empty string) is required.")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail=f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters.")
    return {"data": {"original_length": len(text), "processed": preprocess_text(text)}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
