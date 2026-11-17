"""
Text preprocessing for the Review Intelligence System.

Shared by training and prediction so both paths apply identical transforms.
Goal: normalize noise while preserving sentiment signal — crucially,
negation words (not, no, never…) are never removed because "not good" and
"good" are opposite sentiments.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Negations and sentiment-critical words excluded from stopword removal.
NEGATION_WORDS = {
    "not", "no", "never", "nor", "n't", "cannot", "without",
    "but", "however", "although", "though", "yet", "against",
}

SENTIMENT_CRITICAL = {"very", "too", "so", "really", "extremely", "barely", "hardly", "barely"}

_LEMMATIZER = WordNetLemmatizer()
_STOPWORDS: set[str] | None = None


def _ensure_nltk_data() -> None:
    for pkg in ("stopwords", "wordnet", "omw-1.4"):
        try:
            nltk.data.find(f"corpora/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)


_ensure_nltk_data()


def get_stopwords() -> set[str]:
    """English stopwords minus negation and sentiment-critical words."""
    global _STOPWORDS
    if _STOPWORDS is None:
        base = set(stopwords.words("english"))
        _STOPWORDS = base - NEGATION_WORDS - SENTIMENT_CRITICAL
    return _STOPWORDS


_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_HTML_RE = re.compile(r"<[^>]+>")
_NON_ALPHANUM_RE = re.compile(r"[^a-z\s']")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Lowercase, strip noise, collapse whitespace. Keeps apostrophes so
    contractions like "don't" survive tokenization."""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = _HTML_RE.sub(" ", text)
    text = _URL_RE.sub(" ", text)
    text = _NON_ALPHANUM_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def tokenize(text: str) -> list[str]:
    """Split normalized text on whitespace and drop pure apostrophe tokens."""
    return [t for t in normalize_text(text).split() if t.strip("'")]


def remove_stopwords(tokens: Iterable[str]) -> list[str]:
    stop = get_stopwords()
    return [t for t in tokens if t not in stop and len(t) > 1]


def lemmatize(tokens: Iterable[str]) -> list[str]:
    return [_LEMMATIZER.lemmatize(t) for t in tokens]


def preprocess_text(text: str, *, remove_stops: bool = True, lemmatize_tokens: bool = True) -> str:
    """Full pipeline for one review. Used identically by train.py and predict.py."""
    if not isinstance(text, str) or not text.strip():
        return ""
    tokens = tokenize(text)
    if remove_stops:
        tokens = remove_stopwords(tokens)
    if lemmatize_tokens:
        tokens = lemmatize(tokens)
    return " ".join(tokens)


def clean_dataframe(df, text_column: str, label_column: str | None = None, *,
                    apply_text_pipeline: bool = True, config=None):
    """Clean a raw dataframe for training: drop unusable rows and duplicates.

    Returns (clean_df, stats). Missing text/labels are dropped (not imputed) —
    inventing review text or labels would corrupt the model.
    """
    import pandas as pd

    stats: dict[str, int] = {}
    original = len(df)
    df = df.copy()

    df[text_column] = df[text_column].astype("string").str.strip()
    df = df[df[text_column].str.len() > 0]
    stats["dropped_missing_or_empty_text"] = original - len(df)

    if label_column and label_column in df.columns:
        before = len(df)
        df = df[df[label_column].notna()]
        stats["dropped_missing_labels"] = before - len(df)

    before = len(df)
    df = df.drop_duplicates(subset=[text_column])
    stats["dropped_duplicate_reviews"] = before - len(df)

    stats["remaining_rows"] = len(df)

    if apply_text_pipeline:
        df = df.assign(**{
            f"{text_column}_clean": df[text_column].apply(preprocess_text)
        })
        before = len(df)
        df = df[df[f"{text_column}_clean"].str.len() > 0]
        stats["dropped_empty_after_preprocessing"] = before - len(df)
        stats["remaining_rows"] = len(df)

    return df, stats
