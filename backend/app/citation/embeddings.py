"""Deterministic, dependency-free text embedder.

For a production deployment swap this for ``sentence-transformers`` (or a hosted
embedding API). We use a hashing embedder here so the whole stack runs with no
model download and tests are deterministic. The output is L2-normalized so dot
product equals cosine similarity, matching pgvector's ``<=>`` distance.
"""
from __future__ import annotations

import hashlib
import math
import re

from app.core.config import settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def embed(text: str, dim: int | None = None) -> list[float]:
    """Return an L2-normalized hashing embedding for ``text``.

    Uses the hashing trick: each token is hashed to a bucket with a signed
    weight. Stable across processes (uses blake2b, not Python's salted hash).
    """
    dim = dim or settings.embedding_dim
    vec = [0.0] * dim
    tokens = _tokens(text)
    if not tokens:
        return vec
    for tok in tokens:
        h = hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "big") % dim
        sign = 1.0 if h[4] & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
