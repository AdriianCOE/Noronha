"""Output path validation and atomic JSON writing."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable


class UnsafeOutputError(ValueError):
    """The requested output could escape the tool-owned output directory."""


def safe_output_path(
    relative_path: Path,
    output_root: Path,
    input_paths: Iterable[Path] = (),
) -> Path:
    if relative_path.is_absolute():
        raise UnsafeOutputError("--json-out must be relative to the tool out directory")
    if output_root.is_symlink():
        raise UnsafeOutputError("The tool out directory must not be a symlink")
    root = output_root.resolve(strict=False)
    candidate = (root / relative_path).resolve(strict=False)
    try:
        common = os.path.commonpath((root, candidate))
    except ValueError as error:
        raise UnsafeOutputError("--json-out is on a different drive") from error
    if common != str(root):
        raise UnsafeOutputError("--json-out escapes the tool out directory")
    resolved_inputs = {path.resolve(strict=False) for path in input_paths}
    if candidate in resolved_inputs:
        raise UnsafeOutputError("--json-out resolves to an input file")
    if candidate == root:
        raise UnsafeOutputError("--json-out must name a file below the out directory")
    return candidate


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
