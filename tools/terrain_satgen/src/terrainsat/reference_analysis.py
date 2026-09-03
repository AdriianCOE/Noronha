"""Bounded, read-only style statistics for local reference satellite maps."""

from __future__ import annotations

from pathlib import Path
import warnings

import numpy as np
from PIL import Image, ImageFilter

from .inspect import sha256_file


MAX_REFERENCE_PIXELS = 256_000_000
SAMPLE_EDGE_PX = 1024


class ReferenceAnalysisError(ValueError):
    """A style reference cannot be sampled safely."""


def _open_unbounded_metadata(path: Path) -> tuple[int, int, str, str]:
    original_limit = Image.MAX_IMAGE_PIXELS
    try:
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(path) as image:
            return image.width, image.height, image.mode, image.format or "unknown"
    finally:
        Image.MAX_IMAGE_PIXELS = original_limit


def _sample_rgb(path: Path) -> tuple[np.ndarray, dict[str, object]]:
    width, height, mode, image_format = _open_unbounded_metadata(path)
    pixels = width * height
    if pixels > MAX_REFERENCE_PIXELS:
        raise ReferenceAnalysisError(
            f"{path.name} has {pixels:,} pixels; reference analysis limit is {MAX_REFERENCE_PIXELS:,}"
        )
    original_limit = Image.MAX_IMAGE_PIXELS
    try:
        Image.MAX_IMAGE_PIXELS = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((SAMPLE_EDGE_PX, SAMPLE_EDGE_PX), Image.Resampling.BOX)
                sample = np.asarray(image, dtype=np.uint8).copy()
    finally:
        Image.MAX_IMAGE_PIXELS = original_limit
    metadata: dict[str, object] = {
        "path": str(path),
        "width": width,
        "height": height,
        "mode": mode,
        "format": image_format,
        "file_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "analysis_sample_size": {"width": sample.shape[1], "height": sample.shape[0]},
        "frequency_units": "normalized sample pixels; physical metres are not inferred",
    }
    return sample, metadata


def _luminance(rgb: np.ndarray) -> np.ndarray:
    return (rgb[:, :, 0] * 0.2126 + rgb[:, :, 1] * 0.7152 + rgb[:, :, 2] * 0.0722).astype(np.float32)


def _saturation(rgb: np.ndarray) -> np.ndarray:
    values = rgb / np.float32(255)
    maximum = np.max(values, axis=2)
    minimum = np.min(values, axis=2)
    return np.divide(maximum - minimum, maximum, out=np.zeros_like(maximum), where=maximum > 0)


def _blur_luminance(luminance: np.ndarray, radius: int) -> np.ndarray:
    image = Image.fromarray(np.rint(luminance).clip(0, 255).astype(np.uint8), mode="L")
    return np.asarray(image.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)


def image_statistics(path: Path) -> dict[str, object]:
    """Return comparable image statistics; no reference pixels leave this process."""
    sample, metadata = _sample_rgb(path)
    values = sample.astype(np.float32)
    luminance = _luminance(values)
    saturation = _saturation(values)
    blur_small = _blur_luminance(luminance, 1)
    blur_medium = _blur_luminance(luminance, 8)
    blur_macro = _blur_luminance(luminance, 32)
    metadata["statistics"] = {
        "rgb_mean": [round(float(value), 3) for value in values.mean(axis=(0, 1))],
        "rgb_median": [round(float(value), 3) for value in np.median(values, axis=(0, 1))],
        "luminance_percentiles": {str(p): round(float(value), 3) for p, value in zip((5, 25, 50, 75, 95), np.percentile(luminance, (5, 25, 50, 75, 95)))},
        "saturation_percentiles": {str(p): round(float(value), 5) for p, value in zip((5, 25, 50, 75, 95), np.percentile(saturation, (5, 25, 50, 75, 95)))},
        "local_contrast_mean_abs": round(float(np.mean(np.abs(luminance - blur_small))), 4),
        "high_frequency_mean_abs": round(float(np.mean(np.abs(luminance - blur_medium))), 4),
        "medium_variance": round(float(np.var(blur_medium - blur_macro)), 4),
        "macro_variance": round(float(np.var(blur_macro)), 4),
    }
    return metadata
