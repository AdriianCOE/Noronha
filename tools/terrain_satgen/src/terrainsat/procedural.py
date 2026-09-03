"""Deterministic, world-coordinate procedural fields for synthetic previews."""

from __future__ import annotations

import hashlib

import numpy as np


def stable_seed(*parts: object) -> int:
    """Return a reproducible 64-bit seed without relying on Python's salted hash."""
    encoded = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(encoded, digest_size=8).digest(), "little")


def _hash_grid(x: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """Vectorized hash-grid values in [0, 1), stable across processes."""
    value = (
        np.asarray(x, dtype=np.uint64) * np.uint64(0x9E3779B185EBCA87)
        ^ np.asarray(y, dtype=np.uint64) * np.uint64(0xC2B2AE3D27D4EB4F)
        ^ np.uint64(seed)
    )
    value ^= value >> np.uint64(30)
    value *= np.uint64(0xBF58476D1CE4E5B9)
    value ^= value >> np.uint64(27)
    value *= np.uint64(0x94D049BB133111EB)
    value ^= value >> np.uint64(31)
    return ((value >> np.uint64(40)).astype(np.float32) / np.float32(1 << 24)).astype(np.float32)


def value_noise(
    x_m: np.ndarray,
    y_m: np.ndarray,
    *,
    cell_size_m: float,
    seed: int,
) -> np.ndarray:
    """Smooth value noise sampled at absolute world coordinates in metres."""
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    gx = np.asarray(x_m, dtype=np.float32) / np.float32(cell_size_m)
    gy = np.asarray(y_m, dtype=np.float32) / np.float32(cell_size_m)
    x0 = np.floor(gx).astype(np.int64)
    y0 = np.floor(gy).astype(np.int64)
    tx = (gx - x0).astype(np.float32)
    ty = (gy - y0).astype(np.float32)
    sx = tx * tx * (np.float32(3.0) - np.float32(2.0) * tx)
    sy = ty * ty * (np.float32(3.0) - np.float32(2.0) * ty)
    v00 = _hash_grid(x0[None, :], y0[:, None], seed)
    v10 = _hash_grid((x0 + 1)[None, :], y0[:, None], seed)
    v01 = _hash_grid(x0[None, :], (y0 + 1)[:, None], seed)
    v11 = _hash_grid((x0 + 1)[None, :], (y0 + 1)[:, None], seed)
    lower = v00 + (v10 - v00) * sx[None, :]
    upper = v01 + (v11 - v01) * sx[None, :]
    return (lower + (upper - lower) * sy[:, None]).astype(np.float32)
