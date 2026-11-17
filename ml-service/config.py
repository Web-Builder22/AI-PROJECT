"""
Central configuration for the ML service.

Every dataset-specific setting lives here so a new dataset can be adopted
without touching any core code. Override any value with environment
variables (all optional) — see .env.example.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", BASE_DIR / "artifacts"))
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", BASE_DIR / "reports"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

for _dir in (MODELS_DIR, ARTIFACTS_DIR, REPORTS_DIR, DATA_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


@dataclass
class DatasetConfig:
    """Configuration for locating and interpreting the training CSV.

    Column names are intentionally NOT assumed: set them once here (or via
    env vars) when the dataset is supplied. `review_text_column` and
    `label_column` may be set to None until then.
    """

    # Path to the CSV. Accepts an absolute path or one relative to ml-service/.
    csv_path: str = os.getenv("DATASET_CSV_PATH", str(DATA_DIR / "reviews.csv"))

    # Column containing the review text. None = not configured yet.
    review_text_column: str | None = os.getenv("DATASET_TEXT_COLUMN") or None

    # Column containing the sentiment label. None = not configured yet.
    label_column: str | None = os.getenv("DATASET_LABEL_COLUMN") or None

    # Product column is optional (used for per-product insights later).
    product_column: str | None = os.getenv("DATASET_PRODUCT_COLUMN") or None

    # Expected label values after any mapping. Classes not listed here are
    # reported during inspection as unexpected.
    expected_classes: tuple[str, ...] = ("negative", "neutral", "positive")

    # Only used when the dataset carries ratings instead of sentiment labels.
    # Kept as explicit configuration — ratings are NEVER silently mapped.
    rating_column: str | None = os.getenv("DATASET_RATING_COLUMN") or None
    # Example for a 1–5 scale (set RATINGS_ARE_LABELS=true to activate):
    #   1-2 -> negative, 3 -> neutral, 4-5 -> positive
    rating_to_sentiment: dict[int, str] = field(
        default_factory=lambda: {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}
    )
    ratings_are_labels: bool = os.getenv("DATASET_RATINGS_ARE_LABELS", "false").lower() == "true"

    def resolve_csv_path(self) -> Path:
        p = Path(self.csv_path)
        return p if p.is_absolute() else BASE_DIR / p

    def has_required_columns(self) -> bool:
        return bool(self.review_text_column) and (bool(self.label_column) or bool(self.rating_column))


def get_dataset_config() -> DatasetConfig:
    """Build the active dataset configuration (env vars already applied)."""
    return DatasetConfig()


# --- Service settings ---

API_HOST = os.getenv("ML_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("ML_API_PORT", "8000"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_REVIEW_CHARS", "5000"))
