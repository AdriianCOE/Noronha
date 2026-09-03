"""Bounded, read-only statistics for local reference satellite maps."""

from __future__ import annotations

from pathlib import Path
import math
import tomllib
import warnings

import numpy as np
from PIL import Image, ImageFilter

from .inspect import sha256_file


MAX_REFERENCE_PIXELS = 256_000_000
SAMPLE_EDGE_PX = 1024
MICRO_LOW_PASS_RADIUS_PX = 2
MESO_LOW_PASS_RADIUS_PX = 12
MACRO_LOW_PASS_RADIUS_PX = 48


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


def _crop_bound(value: object, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ReferenceAnalysisError(f"ROI {name} must be a non-negative integer")
    return value


def _sample_rgb(path: Path, crop: tuple[int, int, int, int] | None = None) -> tuple[np.ndarray, dict[str, object]]:
    width, height, mode, image_format = _open_unbounded_metadata(path)
    pixels = width * height
    if pixels > MAX_REFERENCE_PIXELS:
        raise ReferenceAnalysisError(
            f"{path.name} has {pixels:,} pixels; reference analysis limit is {MAX_REFERENCE_PIXELS:,}"
        )
    if crop is not None:
        left, top, right, bottom = crop
        if left < 0 or top < 0 or right > width or bottom > height or right <= left or bottom <= top:
            raise ReferenceAnalysisError(f"ROI lies outside {path.name}")
    original_limit = Image.MAX_IMAGE_PIXELS
    try:
        Image.MAX_IMAGE_PIXELS = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                image = image.convert("RGB")
                if crop is not None:
                    image = image.crop(crop)
                source_size = image.size
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
        "analysis_source_size": {"width": source_size[0], "height": source_size[1]},
        "analysis_sample_size": {"width": sample.shape[1], "height": sample.shape[0]},
    }
    if crop is not None:
        metadata["roi_bounds_pixels"] = {"x": crop[0], "y": crop[1], "width": crop[2] - crop[0], "height": crop[3] - crop[1]}
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


def _frequency_metrics(luminance: np.ndarray) -> dict[str, object]:
    """Report a simple Laplacian-style split in sample pixels, never metres by default."""
    micro_low = _blur_luminance(luminance, MICRO_LOW_PASS_RADIUS_PX)
    meso_low = _blur_luminance(luminance, MESO_LOW_PASS_RADIUS_PX)
    macro_low = _blur_luminance(luminance, MACRO_LOW_PASS_RADIUS_PX)
    micro = luminance - micro_low
    meso = micro_low - meso_low
    macro = meso_low - macro_low
    return {
        "radii_sample_pixels": {
            "micro_low_pass": MICRO_LOW_PASS_RADIUS_PX,
            "meso_low_pass": MESO_LOW_PASS_RADIUS_PX,
            "macro_low_pass": MACRO_LOW_PASS_RADIUS_PX,
        },
        "micro_mean_abs": round(float(np.mean(np.abs(micro))), 4),
        "micro_variance": round(float(np.var(micro)), 4),
        "meso_mean_abs": round(float(np.mean(np.abs(meso))), 4),
        "meso_variance": round(float(np.var(meso)), 4),
        "macro_mean_abs": round(float(np.mean(np.abs(macro))), 4),
        "macro_variance": round(float(np.var(macro)), 4),
        "macro_residual_variance": round(float(np.var(macro_low)), 4),
    }


def _edge_metrics(luminance: np.ndarray) -> dict[str, float]:
    horizontal = np.abs(np.diff(luminance, axis=1))
    vertical = np.abs(np.diff(luminance, axis=0))
    magnitude = np.concatenate((horizontal.ravel(), vertical.ravel()))
    return {
        "mean_abs_gradient": round(float(np.mean(magnitude)), 4),
        "p90_abs_gradient": round(float(np.percentile(magnitude, 90)), 4),
        "edge_fraction_gradient_ge_12": round(float(np.mean(magnitude >= 12.0)), 6),
    }


def image_statistics(
    path: Path,
    *,
    crop: tuple[int, int, int, int] | None = None,
    meters_per_pixel: float | None = None,
) -> dict[str, object]:
    """Return derived metrics; reference pixels never leave this process."""
    if meters_per_pixel is not None and (not math.isfinite(meters_per_pixel) or meters_per_pixel <= 0):
        raise ReferenceAnalysisError("meters_per_pixel must be a positive finite number")
    sample, metadata = _sample_rgb(path, crop)
    values = sample.astype(np.float32)
    luminance = _luminance(values)
    saturation = _saturation(values)
    local_low = _blur_luminance(luminance, 1)
    frequency = _frequency_metrics(luminance)
    metadata["frequency_units"] = "normalized sample pixels; physical metres are not inferred"
    if meters_per_pixel is not None:
        metadata["known_meters_per_pixel"] = meters_per_pixel
        metadata["frequency_radii_metres"] = {
            name: round(radius * meters_per_pixel, 4)
            for name, radius in frequency["radii_sample_pixels"].items()  # type: ignore[union-attr]
        }
    metadata["statistics"] = {
        "rgb_mean": [round(float(value), 3) for value in values.mean(axis=(0, 1))],
        "rgb_median": [round(float(value), 3) for value in np.median(values, axis=(0, 1))],
        "luminance_mean": round(float(luminance.mean()), 4),
        "luminance_percentiles": {str(p): round(float(value), 3) for p, value in zip((5, 25, 50, 75, 95), np.percentile(luminance, (5, 25, 50, 75, 95)))},
        "saturation_mean": round(float(saturation.mean()), 5),
        "saturation_percentiles": {str(p): round(float(value), 5) for p, value in zip((5, 25, 50, 75, 95), np.percentile(saturation, (5, 25, 50, 75, 95)))},
        "local_contrast_mean_abs": round(float(np.mean(np.abs(luminance - local_low))), 4),
        "edge_preservation_proxy": _edge_metrics(luminance),
        "clipping": {
            "channel_zero_fraction": round(float(np.mean(sample == 0)), 8),
            "channel_255_fraction": round(float(np.mean(sample == 255)), 8),
        },
        "frequency": frequency,
        # Stable compatibility keys for existing reports. Their definitions now
        # point at the explicit three-band decomposition above.
        "high_frequency_mean_abs": frequency["micro_mean_abs"],
        "medium_variance": frequency["meso_variance"],
        "macro_variance": frequency["macro_variance"],
    }
    return metadata


def local_roi_statistics(config_path: Path) -> list[dict[str, object]]:
    """Read local-only ROI coordinates and return statistics without creating crops.

    The caller restricts ``config_path`` below ``out/``. Sources remain local
    absolute paths; this function writes nothing and makes no semantic claim
    about a ROI beyond the author-supplied label.
    """
    if not config_path.is_file():
        raise ReferenceAnalysisError(f"Local ROI config does not exist: {config_path}")
    try:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ReferenceAnalysisError(f"Cannot read local ROI config: {error}") from error
    if not isinstance(raw, dict) or not raw:
        raise ReferenceAnalysisError("Local ROI config must contain named reference tables")
    results: list[dict[str, object]] = []
    for collection, entries in raw.items():
        if not isinstance(entries, dict):
            raise ReferenceAnalysisError(f"ROI collection {collection} must be a table")
        for name, item in entries.items():
            if not isinstance(item, dict) or set(item) != {"source", "x", "y", "width", "height"}:
                raise ReferenceAnalysisError(f"ROI {collection}.{name} must contain source, x, y, width and height")
            source = item["source"]
            if not isinstance(source, str):
                raise ReferenceAnalysisError(f"ROI {collection}.{name} source must be a path string")
            x = _crop_bound(item["x"], name=f"{collection}.{name}.x")
            y = _crop_bound(item["y"], name=f"{collection}.{name}.y")
            width = _crop_bound(item["width"], name=f"{collection}.{name}.width")
            height = _crop_bound(item["height"], name=f"{collection}.{name}.height")
            if width == 0 or height == 0:
                raise ReferenceAnalysisError(f"ROI {collection}.{name} width and height must be positive")
            result = image_statistics(Path(source).resolve(strict=True), crop=(x, y, x + width, y + height))
            result["roi_name"] = f"{collection}.{name}"
            result["semantic_status"] = "AUTHOR_NAMED_LOCAL_ROI; no automatic terrain classification"
            results.append(result)
    return results
