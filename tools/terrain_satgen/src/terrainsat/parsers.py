"""Small read-only parsers for the formats used by TerrainSatGen inspect."""

from __future__ import annotations

import math
import re
from itertools import chain
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class InputFormatError(ValueError):
    """An inspected input does not match the supported format subset."""


@dataclass(frozen=True)
class Surface:
    name: str
    texture: str
    material: str
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class AscStats:
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata_value: float | None
    value_count: int
    nodata_count: int
    minimum: float
    maximum: float
    mean: float

    @property
    def extent(self) -> dict[str, list[float]]:
        return {
            "x": [self.xllcorner, self.xllcorner + self.ncols * self.cellsize],
            "y": [self.yllcorner, self.yllcorner + self.nrows * self.cellsize],
        }


_CLASS_RE = re.compile(r"\bclass\s+(?P<name>[A-Za-z_]\w*)\s*\{")
_TEXTURE_RE = re.compile(r'\btexture\s*=\s*"(?P<value>[^"]+)"\s*;')
_MATERIAL_RE = re.compile(r'\bmaterial\s*=\s*"(?P<value>[^"]+)"\s*;')
_COLOR_RE = re.compile(
    r"\b(?P<name>[A-Za-z_]\w*)\s*\[\s*\]\s*=\s*"
    r"\{\s*\{\s*(?P<r>\d+)\s*,\s*(?P<g>\d+)\s*,\s*(?P<b>\d+)\s*\}\s*\}\s*;"
)


def _without_comments(text: str) -> str:
    """Remove C/C++ comments while preserving quoted strings and line shape."""

    output: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            output.append(char)
            if char == "\\" and index + 1 < len(text):
                output.append(text[index + 1])
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {'"', "'"}:
            quote = char
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            output.extend("  ")
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                output.append(" ")
                index += 1
            continue
        if char == "/" and next_char == "*":
            output.extend("  ")
            index += 2
            while index < len(text):
                if text[index] == "*" and index + 1 < len(text) and text[index + 1] == "/":
                    output.extend("  ")
                    index += 2
                    break
                output.append(text[index] if text[index] in "\r\n" else " ")
                index += 1
            else:
                raise InputFormatError("Unterminated block comment in layers.cfg")
            continue
        output.append(char)
        index += 1
    if quote:
        raise InputFormatError("Unterminated quoted string in layers.cfg")
    return "".join(output)


def _class_body(text: str, class_name: str) -> str:
    matches = [match for match in _CLASS_RE.finditer(text) if match["name"] == class_name]
    if len(matches) != 1:
        raise InputFormatError(f"Expected exactly one class {class_name}, found {len(matches)}")
    start = matches[0].end()
    depth = 1
    quote: str | None = None
    index = start
    while index < len(text):
        char = text[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index]
        index += 1
    raise InputFormatError(f"Unterminated class {class_name}")


def _direct_child_classes(body: str) -> Iterator[tuple[str, str]]:
    index = 0
    while True:
        match = _CLASS_RE.search(body, index)
        if not match:
            return
        start = match.end()
        depth = 1
        cursor = start
        while cursor < len(body) and depth:
            if body[cursor] == "{":
                depth += 1
            elif body[cursor] == "}":
                depth -= 1
            cursor += 1
        if depth:
            raise InputFormatError(f"Unterminated surface class {match['name']}")
        yield match["name"], body[start : cursor - 1]
        index = cursor


def parse_layers(path: Path) -> list[Surface]:
    """Parse the concrete Layers/Legend subset used by Noronha."""

    text = _without_comments(path.read_text(encoding="utf-8-sig"))
    layers_body = _class_body(text, "Layers")
    definitions: dict[str, tuple[str, str]] = {}
    for name, body in _direct_child_classes(layers_body):
        if name in definitions:
            raise InputFormatError(f"Duplicate surface class: {name}")
        textures = _TEXTURE_RE.findall(body)
        materials = _MATERIAL_RE.findall(body)
        if len(textures) != 1 or len(materials) != 1:
            raise InputFormatError(
                f"Surface {name} must declare exactly one texture and one material"
            )
        definitions[name] = (textures[0], materials[0])
    if not definitions:
        raise InputFormatError("No surface classes found in class Layers")

    legend_body = _class_body(text, "Legend")
    colors_body = _class_body(legend_body, "Colors")
    colors: dict[str, tuple[int, int, int]] = {}
    rgb_owners: dict[tuple[int, int, int], str] = {}
    for match in _COLOR_RE.finditer(colors_body):
        name = match["name"]
        rgb = tuple(int(match[channel]) for channel in ("r", "g", "b"))
        if any(channel > 255 for channel in rgb):
            raise InputFormatError(f"Legend RGB outside 0..255 for {name}: {rgb}")
        if name in colors:
            raise InputFormatError(f"Duplicate Legend surface: {name}")
        if rgb in rgb_owners:
            raise InputFormatError(
                f"Duplicate Legend RGB {rgb}: {rgb_owners[rgb]} and {name}"
            )
        colors[name] = rgb
        rgb_owners[rgb] = name

    missing_layers = sorted(set(colors) - set(definitions))
    missing_colors = sorted(set(definitions) - set(colors))
    if missing_layers:
        raise InputFormatError(
            "Legend references undefined surfaces: " + ", ".join(missing_layers)
        )
    if missing_colors:
        raise InputFormatError(
            "Layers without Legend RGB: " + ", ".join(missing_colors)
        )
    return [Surface(name, *definitions[name], colors[name]) for name in definitions]


_ASC_REQUIRED = {"ncols", "nrows", "cellsize"}
_ASC_X_KEYS = {"xllcorner", "xllcenter"}
_ASC_Y_KEYS = {"yllcorner", "yllcenter"}


def parse_asc(path: Path) -> AscStats:
    """Stream an ESRI ASCII grid and calculate shape and value statistics."""

    header: dict[str, float] = {}
    value_count = 0
    nodata_count = 0
    valid_count = 0
    minimum = math.inf
    maximum = -math.inf
    total = 0.0

    with path.open("r", encoding="ascii") as stream:
        known_header_keys = _ASC_REQUIRED | _ASC_X_KEYS | _ASC_Y_KEYS | {"nodata_value"}
        first_data_line: str | None = None
        while line := stream.readline():
            parts = line.split()
            if not parts:
                continue
            key = parts[0].lower()
            if key not in known_header_keys:
                try:
                    float(parts[0])
                except ValueError as error:
                    raise InputFormatError(f"Unknown ASC header key: {parts[0]}") from error
                first_data_line = line
                break
            if len(parts) != 2:
                raise InputFormatError(f"Invalid ASC header line: {line.rstrip()}")
            if key in header:
                raise InputFormatError(f"Duplicate ASC header key: {key}")
            try:
                header[key] = float(parts[1])
            except ValueError as error:
                raise InputFormatError(f"Invalid ASC header value for {key}") from error

        if not _ASC_REQUIRED <= header.keys():
            missing = sorted(_ASC_REQUIRED - header.keys())
            raise InputFormatError("Missing ASC header keys: " + ", ".join(missing))
        x_keys = _ASC_X_KEYS & header.keys()
        y_keys = _ASC_Y_KEYS & header.keys()
        if len(x_keys) != 1 or len(y_keys) != 1:
            raise InputFormatError("ASC requires exactly one X and one Y origin key")
        ncols = int(header["ncols"])
        nrows = int(header["nrows"])
        if header["ncols"] != ncols or header["nrows"] != nrows or ncols <= 0 or nrows <= 0:
            raise InputFormatError("ASC ncols and nrows must be positive integers")
        if header["cellsize"] <= 0:
            raise InputFormatError("ASC cellsize must be positive")
        nodata_value = header.get("nodata_value")

        rows_seen = 0
        data_lines = chain([first_data_line] if first_data_line is not None else [], stream)
        for rows_seen, line in enumerate(data_lines, start=1):
            parts = line.split()
            if len(parts) != ncols:
                raise InputFormatError(
                    f"ASC row {rows_seen} has {len(parts)} values; expected {ncols}"
                )
            try:
                values = [float(part) for part in parts]
            except ValueError as error:
                raise InputFormatError(f"ASC row {rows_seen} contains a non-number") from error
            value_count += len(values)
            for value in values:
                if nodata_value is not None and value == nodata_value:
                    nodata_count += 1
                    continue
                valid_count += 1
                minimum = min(minimum, value)
                maximum = max(maximum, value)
                total += value
        if rows_seen != nrows:
            raise InputFormatError(f"ASC has {rows_seen} rows; expected {nrows}")
        if not valid_count:
            raise InputFormatError("ASC contains no valid elevation values")

    x_key = next(iter(x_keys))
    y_key = next(iter(y_keys))
    x_origin = header[x_key]
    y_origin = header[y_key]
    if x_key == "xllcenter":
        x_origin -= header["cellsize"] / 2
    if y_key == "yllcenter":
        y_origin -= header["cellsize"] / 2
    return AscStats(
        ncols=ncols,
        nrows=nrows,
        xllcorner=x_origin,
        yllcorner=y_origin,
        cellsize=header["cellsize"],
        nodata_value=nodata_value,
        value_count=value_count,
        nodata_count=nodata_count,
        minimum=minimum,
        maximum=maximum,
        mean=total / valid_count,
    )
