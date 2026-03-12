"""Embedding utilities — standalone, no external config dependency."""

from __future__ import annotations

from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CACHE_DIR = str(Path.home() / ".knowledge-graph" / ".model_cache")

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
        _model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=CACHE_DIR)
    return _model


def get_embedding(text: str) -> list[float]:
    return get_model().encode(text, normalize_embeddings=True).tolist()


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, normalize_embeddings=True, batch_size=32).tolist()


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    a, b = np.array(vec1), np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
