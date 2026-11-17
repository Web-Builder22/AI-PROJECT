"""
Dataset loading and inspection.

`inspect_dataset` never fabricates statistics: it reads the configured CSV
and reports exactly what is on disk, or raises a clear error explaining
what is missing or misconfigured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from config import DatasetConfig


class DatasetError(Exception):
    """Raised when the dataset is missing, unreadable, or misconfigured."""


@dataclass
class ColumnReport:
    name: str
    dtype: str
    non_null: int
    missing: int
    unique: int


@dataclass
class InspectionReport:
    file_path: str
    exists: bool
    total_rows: int = 0
    total_columns: int = 0
    columns: list[ColumnReport] = field(default_factory=list)
    label_classes: dict[str, int] = field(default_factory=dict)
    label_percentages: dict[str, float] = field(default_factory=dict)
    duplicate_rows: int = 0
    duplicate_reviews: int = 0
    missing_text: int = 0
    missing_labels: int = 0
    text_column_found: bool = False
    label_column_found: bool = False
    configured_correctly: bool = False
    issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "exists": self.exists,
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "columns": [c.__dict__ for c in self.columns],
            "label_classes": self.label_classes,
            "label_percentages": self.label_percentages,
            "duplicate_rows": self.duplicate_rows,
            "duplicate_reviews": self.duplicate_reviews,
            "missing_text": self.missing_text,
            "missing_labels": self.missing_labels,
            "text_column_found": self.text_column_found,
            "label_column_found": self.label_column_found,
            "configured_correctly": self.configured_correctly,
            "issues": self.issues,
            "notes": self.notes,
        }


def load_raw_dataframe(config: DatasetConfig) -> pd.DataFrame:
    """Load the configured CSV verbatim (no cleaning). Raises DatasetError on failure."""
    path = config.resolve_csv_path()
    if not path.exists():
        raise DatasetError(
            f"Dataset file not found at '{path}'. "
            "Place the CSV in ml-service/data/ or set DATASET_CSV_PATH in .env."
        )
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError as e:
        raise DatasetError(f"Dataset file at '{path}' is empty.") from e
    except Exception as e:  # unreadable encoding / malformed CSV
        raise DatasetError(f"Could not parse '{path}' as CSV: {e}") from e


def map_labels(df: pd.DataFrame, config: DatasetConfig) -> pd.Series:
    """Return normalized string labels, applying the rating mapping only when
    explicitly configured (`ratings_are_labels=True`)."""
    if config.label_column and config.label_column in df.columns:
        return df[config.label_column].astype("string").str.strip().str.lower()
    if config.ratings_are_labels and config.rating_column and config.rating_column in df.columns:
        mapping = config.rating_to_sentiment
        return df[config.rating_column].map(mapping)
    raise DatasetError("No label column available: check label_column / rating settings.")


def inspect_dataset(config: DatasetConfig) -> InspectionReport:
    """Inspect the configured CSV and return a factual report. Never fabricates data."""
    path = config.resolve_csv_path()
    if not path.exists():
        report = InspectionReport(file_path=str(path), exists=False)
        report.issues.append("File does not exist.")
        return report

    df = load_raw_dataframe(config)
    report = InspectionReport(file_path=str(path), exists=True)
    report.total_rows = len(df)
    report.total_columns = len(df.columns)
    report.columns = [
        ColumnReport(name=str(c), dtype=str(df[c].dtype), non_null=int(df[c].notna().sum()),
                     missing=int(df[c].isna().sum()), unique=int(df[c].nunique(dropna=True)))
        for c in df.columns
    ]

    # --- configured column checks ---
    text_col = config.review_text_column
    if not text_col:
        report.issues.append("Review text column is not configured (DATASET_TEXT_COLUMN unset).")
    elif text_col not in df.columns:
        report.issues.append(
            f"Configured text column '{text_col}' not found. Available columns: {', '.join(map(str, df.columns))}."
        )
    else:
        report.text_column_found = True
        report.missing_text = int(df[text_col].isna().sum())
        report.duplicate_reviews = int(df[text_col].dropna().str.strip().str.lower().duplicated().sum())

    if config.ratings_are_labels and config.rating_column:
        if config.rating_column not in df.columns:
            report.issues.append(f"Configured rating column '{config.rating_column}' not found in CSV.")
        else:
            report.label_column_found = True
            mapped = map_labels(df, config)
            report.missing_labels = int(mapped.isna().sum())
            counts = mapped.value_counts(dropna=False)
            total = int(counts.sum())
            report.label_classes = {str(k): int(v) for k, v in counts.items() if pd.notna(k)}
            report.label_percentages = {
                str(k): round(v / total * 100, 2) for k, v in counts.items() if pd.notna(k)
            } if total else {}
            unmapped = int(mapped.isna().sum())
            unmapped_values = int(df.loc[mapped.isna(), config.rating_column].nunique()) if unmapped else 0
            if unmapped:
                report.issues.append(
                    f"{unmapped} row(s) have rating values with no mapping in rating_to_sentiment "
                    f"({unmapped_values} distinct unmapped value(s)) — review the mapping config."
                )
    elif config.label_column:
        if config.label_column not in df.columns:
            report.issues.append(
                f"Configured label column '{config.label_column}' not found. Available columns: "
                f"{', '.join(map(str, df.columns))}."
            )
        else:
            report.label_column_found = True
            labels = map_labels(df, config)
            report.missing_labels = int(labels.isna().sum())
            counts = labels.value_counts(dropna=False)
            total = int(counts.sum())
            report.label_classes = {str(k): int(v) for k, v in counts.items() if pd.notna(k)}
            report.label_percentages = {
                str(k): round(v / total * 100, 2) for k, v in counts.items() if pd.notna(k)
            } if total else {}
            unexpected = set(report.label_classes) - set(config.expected_classes)
            if unexpected:
                report.issues.append(
                    f"Unexpected label values {sorted(unexpected)} not in expected classes "
                    f"{list(config.expected_classes)} — update expected_classes or the rating mapping."
                )
    else:
        report.issues.append("No label column configured (DATASET_LABEL_COLUMN unset).")

    report.duplicate_rows = int(df.duplicated().sum())
    report.configured_correctly = report.text_column_found and report.label_column_found and not report.issues

    if report.configured_correctly:
        report.notes.append("Dataset present and both required columns resolved; ready for preprocessing/training.")
    return report
