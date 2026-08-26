# ================================================================================
#  NORONHA — Authoring Placement Generator
#  Offline tool: generates Terrain Builder / DayZ Editor placement files.
#  This script is NOT loaded by the DayZ runtime.
# ================================================================================

import argparse
import hashlib
import json
import logging
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
from PIL import Image

try:
    from noise import pnoise2

    NOISE_AVAILABLE = True
except ImportError:
    NOISE_AVAILABLE = False


LOG_LEVEL = logging.INFO
DEFAULT_PROFILE_FILE = Path(__file__).with_name("placement_profiles.json")
DEFAULT_PROFILE_NAME = "noronha_coast_v1"

log = logging.getLogger(__name__)


# ================================================================================
#  DATA TYPES
# ================================================================================


@dataclass
class MapObject:
    name: str
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    scale: float = 1.0
    category: str = "generic"


@dataclass
class MapHeader:
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata: float


class PlacementStats:
    def __init__(self) -> None:
        self._data: Dict[str, Counter] = {}

    def inc(self, category: str, key: str, amount: int = 1) -> None:
        self._data.setdefault(category, Counter())[key] += amount

    def placed(self, category: str, amount: int = 1) -> None:
        self.inc(category, "placed", amount)

    def as_dict(self) -> Dict[str, Dict[str, int]]:
        return {category: dict(values) for category, values in sorted(self._data.items())}

    def log_summary(self) -> None:
        log.info("Placement summary:")
        for category, values in sorted(self._data.items()):
            attempts = values.get("attempts", 0)
            placed = values.get("placed", 0)
            log.info("  %-8s attempts=%d placed=%d", category, attempts, placed)
            rejects = [
                (key.removeprefix("rejected_"), value)
                for key, value in values.items()
                if key.startswith("rejected_") and value
            ]
            if rejects:
                log.info(
                    "           rejects: %s",
                    ", ".join(f"{name}={value}" for name, value in sorted(rejects)),
                )


# ================================================================================
#  CONFIGURATION
# ================================================================================


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else LOG_LEVEL
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def load_profile(path: Path, profile_name: str) -> Mapping:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError(f"No profiles found in {path}")

    if profile_name not in profiles:
        available = ", ".join(sorted(profiles))
        raise ValueError(f"Unknown profile '{profile_name}'. Available: {available}")

    profile = profiles[profile_name]
    for required in ("global", "surfaces", "categories"):
        if required not in profile:
            raise ValueError(f"Profile '{profile_name}' is missing '{required}'")

    validate_profile(profile_name, profile)
    return profile


def validate_profile(profile_name: str, profile: Mapping) -> None:
    surfaces = profile["surfaces"]
    for name, rgb_value in surfaces.items():
        if (
            not isinstance(rgb_value, list)
            or len(rgb_value) != 3
            or any(
                not isinstance(value, int) or not 0 <= value <= 255
                for value in rgb_value
            )
        ):
            raise ValueError(
                f"Profile '{profile_name}' surface '{name}' must be [R,G,B] integers"
            )

    categories = profile["categories"]
    required_categories = {"boats", "reeds", "stones", "debris", "shrubs"}
    missing = required_categories - set(categories)
    if missing:
        raise ValueError(
            f"Profile '{profile_name}' is missing categories: {', '.join(sorted(missing))}"
        )

    for category_name, category in categories.items():
        for surface_name in category.get("surfaces", []):
            if surface_name not in surfaces:
                raise ValueError(
                    f"Profile '{profile_name}' category '{category_name}' "
                    f"references unknown surface '{surface_name}'"
                )

    biomes = profile.get("biomes", {})
    if not isinstance(biomes, Mapping):
        raise ValueError(f"Profile '{profile_name}' biomes must be an object")
    for biome_name, biome in biomes.items():
        if not isinstance(biome, Mapping):
            raise ValueError(
                f"Profile '{profile_name}' biome '{biome_name}' must be an object"
            )
        for surface_name in biome.get("surfaces", []):
            if surface_name not in surfaces:
                raise ValueError(
                    f"Profile '{profile_name}' biome '{biome_name}' "
                    f"references unknown surface '{surface_name}'"
                )


def rgb(profile: Mapping, surface_name: str) -> Tuple[int, int, int]:
    return tuple(profile["surfaces"][surface_name])


def category_surface_colors(
    profile: Mapping, category: Mapping
) -> List[Tuple[int, int, int]]:
    return [rgb(profile, name) for name in category.get("surfaces", [])]


# ================================================================================
#  INPUT DATA
# ================================================================================


def load_heightmap(path: Path, sea_level: float) -> Tuple[np.ndarray, MapHeader]:
    log.info("Loading heightmap: %s", path)
    with path.open("r", encoding="utf-8") as handle:
        lines = [handle.readline() for _ in range(6)]

    header = MapHeader(
        ncols=int(lines[0].split()[1]),
        nrows=int(lines[1].split()[1]),
        xllcorner=float(lines[2].split()[1]),
        yllcorner=float(lines[3].split()[1]),
        cellsize=float(lines[4].split()[1]),
        nodata=float(lines[5].split()[1]),
    )

    data = np.loadtxt(path, skiprows=6)
    data[data == header.nodata] = sea_level
    return data, header


def load_surfacemap(path: Path) -> np.ndarray:
    log.info("Loading surface map: %s", path)
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(path) as image:
        return np.array(image.convert("RGB"))


# ================================================================================
#  TERRAIN QUERIES
# ================================================================================


def world_to_heightmap(x: float, z: float, header: MapHeader) -> Tuple[int, int]:
    col = int(x / header.cellsize)
    row = int((header.nrows - 1) - (z / header.cellsize))
    return (
        max(0, min(header.nrows - 1, row)),
        max(0, min(header.ncols - 1, col)),
    )


def world_to_surface(
    x: float,
    z: float,
    surface_shape: Tuple[int, ...],
    max_x: float,
    max_z: float,
) -> Tuple[int, int]:
    cell_x = max_x / surface_shape[1]
    cell_z = max_z / surface_shape[0]
    col = int(x / cell_x)
    row = int((surface_shape[0] - 1) - (z / cell_z))
    return (
        max(0, min(surface_shape[0] - 1, row)),
        max(0, min(surface_shape[1] - 1, col)),
    )


def get_altitude(
    x: float, z: float, height_data: np.ndarray, header: MapHeader
) -> float:
    row, col = world_to_heightmap(x, z, header)
    return float(height_data[row, col])


def get_slope(
    x: float, z: float, height_data: np.ndarray, header: MapHeader
) -> float:
    row, col = world_to_heightmap(x, z, header)
    if (
        row <= 0
        or row >= height_data.shape[0] - 1
        or col <= 0
        or col >= height_data.shape[1] - 1
    ):
        return 0.0

    dz_dx = (
        height_data[row, col + 1] - height_data[row, col - 1]
    ) / (2 * header.cellsize)
    dz_dy = (
        height_data[row + 1, col] - height_data[row - 1, col]
    ) / (2 * header.cellsize)
    return math.degrees(math.atan(math.sqrt(dz_dx**2 + dz_dy**2)))


def get_surface_color(
    x: float,
    z: float,
    surface_data: np.ndarray,
    max_x: float,
    max_z: float,
) -> Tuple[int, int, int]:
    row, col = world_to_surface(x, z, surface_data.shape, max_x, max_z)
    return tuple(int(value) for value in surface_data[row, col][:3])


def is_color(
    pixel: Sequence[int], target: Sequence[int], tolerance: float
) -> bool:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pixel, target))) <= tolerance


def matches_any_surface(
    pixel: Sequence[int],
    allowed_colors: Iterable[Sequence[int]],
    tolerance: float,
) -> bool:
    return any(is_color(pixel, target, tolerance) for target in allowed_colors)


def slope_to_pitch_roll(slope_deg: float, rng: random.Random) -> Tuple[float, float]:
    jitter = slope_deg * 0.3
    return rng.uniform(-jitter, jitter), rng.uniform(-jitter, jitter)


def is_real_coast(
    x: float,
    z: float,
    height_data: np.ndarray,
    header: MapHeader,
    search_radius: float,
    min_land_height: float,
) -> bool:
    """Reject false surface-mask coast lines that have no nearby dry land."""
    diagonal = search_radius / math.sqrt(2)
    offsets = (
        (0.0, search_radius),
        (0.0, -search_radius),
        (search_radius, 0.0),
        (-search_radius, 0.0),
        (diagonal, diagonal),
        (diagonal, -diagonal),
        (-diagonal, diagonal),
        (-diagonal, -diagonal),
    )
    return any(
        get_altitude(x + dx, z + dz, height_data, header) >= min_land_height
        for dx, dz in offsets
    )


class PlacementGrid:
    def __init__(self, cell_size: float) -> None:
        self.cell = cell_size
        self.grid: Dict[Tuple[int, int], List[Tuple[float, float]]] = {}

    def _key(self, x: float, z: float) -> Tuple[int, int]:
        return int(x / self.cell), int(z / self.cell)

    def too_close(self, x: float, z: float, min_distance: float) -> bool:
        cell_x, cell_z = self._key(x, z)
        radius = int(math.ceil(min_distance / self.cell)) + 1
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                for other_x, other_z in self.grid.get(
                    (cell_x + dx, cell_z + dz), []
                ):
                    if math.hypot(x - other_x, z - other_z) < min_distance:
                        return True
        return False

    def add(self, x: float, z: float) -> None:
        self.grid.setdefault(self._key(x, z), []).append((x, z))


def noise_value(
    x: float, z: float, category: Mapping, seed: int, rng: random.Random
) -> float:
    if not NOISE_AVAILABLE:
        return rng.random()

    noise_cfg = category["noise"]
    return (
        pnoise2(
            x / noise_cfg["scale"] + seed * 100,
            z / noise_cfg["scale"] + seed * 100,
            octaves=noise_cfg["octaves"],
            persistence=noise_cfg["persistence"],
            lacunarity=noise_cfg["lacunarity"],
        )
        + 1
    ) / 2


# ================================================================================
#  GENERATORS
# ================================================================================


def random_world_point(
    margin: float, max_x: float, max_z: float, rng: random.Random
) -> Tuple[float, float]:
    return (
        rng.uniform(margin, max_x - margin),
        rng.uniform(margin, max_z - margin),
    )


def category_rng(seed: int, category_name: str) -> random.Random:
    """Give each generator a stable stream without touching module-global RNG."""
    digest = hashlib.sha256(f"{seed}:{category_name}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_candidate(
    *,
    category_name: str,
    x: float,
    z: float,
    height_data: np.ndarray,
    header: MapHeader,
    surface_data: np.ndarray,
    max_x: float,
    max_z: float,
    allowed_colors: Sequence[Sequence[int]],
    tolerance: float,
    min_height: float,
    max_height: float,
    max_slope: float,
    coast_required: bool,
    coast_radius: float,
    coast_min_land_height: float,
    stats: PlacementStats,
) -> Tuple[bool, float, float]:
    y = get_altitude(x, z, height_data, header)
    if not min_height <= y <= max_height:
        stats.inc(category_name, "rejected_altitude")
        return False, y, 0.0

    slope = get_slope(x, z, height_data, header)
    if slope > max_slope:
        stats.inc(category_name, "rejected_slope")
        return False, y, slope

    surface = get_surface_color(x, z, surface_data, max_x, max_z)
    if not matches_any_surface(surface, allowed_colors, tolerance):
        stats.inc(category_name, "rejected_surface")
        return False, y, slope

    if coast_required and not is_real_coast(
        x,
        z,
        height_data,
        header,
        coast_radius,
        coast_min_land_height,
    ):
        stats.inc(category_name, "rejected_inland")
        return False, y, slope

    return True, y, slope


def generate_boats(
    profile: Mapping,
    height_data: np.ndarray,
    header: MapHeader,
    surface_data: np.ndarray,
    max_x: float,
    max_z: float,
    grid: PlacementGrid,
    stats: PlacementStats,
    rng: random.Random,
) -> List[MapObject]:
    category_name = "boats"
    cfg = profile["categories"][category_name]
    global_cfg = profile["global"]
    colors = category_surface_colors(profile, cfg)
    objects: List[MapObject] = []
    cluster_centers: List[Tuple[float, float]] = []

    log.info("Generating boats...")
    max_attempts = cfg["total_clusters"] * cfg["max_attempts_per_cluster"]
    for _ in range(max_attempts):
        if len(cluster_centers) >= cfg["total_clusters"]:
            break

        stats.inc(category_name, "attempts")
        x, z = random_world_point(global_cfg["map_margin"], max_x, max_z, rng)
        valid, _, _ = validate_candidate(
            category_name=category_name,
            x=x,
            z=z,
            height_data=height_data,
            header=header,
            surface_data=surface_data,
            max_x=max_x,
            max_z=max_z,
            allowed_colors=colors,
            tolerance=global_cfg["color_tolerance"],
            min_height=cfg["min_height"],
            max_height=cfg["max_height"],
            max_slope=cfg["max_slope"],
            coast_required=cfg.get("require_real_coast", True),
            coast_radius=global_cfg["coast_search_radius"],
            coast_min_land_height=global_cfg["coast_min_land_height"],
            stats=stats,
        )
        if not valid:
            continue

        if any(
            math.hypot(x - center_x, z - center_z) < cfg["min_cluster_spacing"]
            for center_x, center_z in cluster_centers
        ):
            stats.inc(category_name, "rejected_spacing")
            continue

        cluster_centers.append((x, z))
        stats.inc(category_name, "accepted_clusters")

        for _ in range(
            rng.randint(cfg["cluster_min_size"], cfg["cluster_max_size"])
        ):
            boat_x = x + rng.uniform(-cfg["cluster_radius"], cfg["cluster_radius"])
            boat_z = z + rng.uniform(-cfg["cluster_radius"], cfg["cluster_radius"])
            if grid.too_close(boat_x, boat_z, global_cfg["solid_spacing"]):
                stats.inc(category_name, "rejected_object_spacing")
                continue

            boat_y = get_altitude(boat_x, boat_z, height_data, header)
            boat_slope = get_slope(boat_x, boat_z, height_data, header)
            pitch, roll = slope_to_pitch_roll(boat_slope, rng)
            model = rng.choice(cfg["models"])
            if "Wreck" in model:
                roll = rng.uniform(-25, 25)
                pitch = rng.uniform(-10, 10)

            objects.append(
                MapObject(
                    name=model,
                    x=boat_x,
                    y=boat_y,
                    z=boat_z,
                    yaw=rng.uniform(0, 360),
                    pitch=pitch,
                    roll=roll,
                    scale=rng.uniform(*cfg["scale"]),
                    category="boat",
                )
            )
            grid.add(boat_x, boat_z)
            stats.placed(category_name)

            if cfg.get("gear_models") and rng.random() < cfg["gear_chance"]:
                gear_x = boat_x + rng.uniform(-3, 3)
                gear_z = boat_z + rng.uniform(-3, 3)
                if grid.too_close(gear_x, gear_z, cfg["gear_min_spacing"]):
                    stats.inc(category_name, "rejected_gear_spacing")
                    continue

                objects.append(
                    MapObject(
                        name=rng.choice(cfg["gear_models"]),
                        x=gear_x,
                        y=get_altitude(gear_x, gear_z, height_data, header),
                        z=gear_z,
                        yaw=rng.uniform(0, 360),
                        scale=rng.uniform(*cfg["gear_scale"]),
                        category="boat",
                    )
                )
                grid.add(gear_x, gear_z)
                stats.placed(category_name)

    return objects


def generate_reeds(
    profile: Mapping,
    height_data: np.ndarray,
    header: MapHeader,
    surface_data: np.ndarray,
    max_x: float,
    max_z: float,
    grid: PlacementGrid,
    stats: PlacementStats,
    rng: random.Random,
) -> List[MapObject]:
    category_name = "reeds"
    cfg = profile["categories"][category_name]
    global_cfg = profile["global"]
    colors = category_surface_colors(profile, cfg)
    objects: List[MapObject] = []

    log.info("Generating reeds...")
    for _ in range(cfg["attempts"]):
        stats.inc(category_name, "attempts")
        x, z = random_world_point(global_cfg["map_margin"], max_x, max_z, rng)
        valid, _, _ = validate_candidate(
            category_name=category_name,
            x=x,
            z=z,
            height_data=height_data,
            header=header,
            surface_data=surface_data,
            max_x=max_x,
            max_z=max_z,
            allowed_colors=colors,
            tolerance=global_cfg["color_tolerance"],
            min_height=cfg["min_height"],
            max_height=cfg["max_height"],
            max_slope=cfg["max_slope"],
            coast_required=cfg.get("require_real_coast", True),
            coast_radius=global_cfg["coast_search_radius"],
            coast_min_land_height=global_cfg["coast_min_land_height"],
            stats=stats,
        )
        if not valid:
            continue

        if rng.random() > cfg["clump_chance"]:
            stats.inc(category_name, "rejected_probability")
            continue
        if grid.too_close(x, z, cfg["min_spacing"]):
            stats.inc(category_name, "rejected_spacing")
            continue

        clump_size = 0
        current_x, current_z = x, z
        continue_chance = 1.0
        while (
            clump_size < cfg["clump_max_size"]
            and rng.random() < continue_chance
        ):
            current_y = get_altitude(current_x, current_z, height_data, header)
            current_surface = get_surface_color(
                current_x, current_z, surface_data, max_x, max_z
            )
            if (
                cfg["min_height"] <= current_y <= cfg["max_height"]
                and matches_any_surface(
                    current_surface, colors, global_cfg["color_tolerance"]
                )
                and not grid.too_close(current_x, current_z, cfg["min_spacing"])
            ):
                objects.append(
                    MapObject(
                        name=rng.choice(cfg["models"]),
                        x=current_x,
                        y=current_y,
                        z=current_z,
                        yaw=rng.uniform(0, 360),
                        scale=rng.uniform(*cfg["scale"]),
                        category="reed",
                    )
                )
                grid.add(current_x, current_z)
                stats.placed(category_name)
                clump_size += 1

            angle = rng.uniform(0, 2 * math.pi)
            step = rng.uniform(cfg["min_spacing"], cfg["max_spacing"])
            current_x = max(
                0, min(max_x, current_x + step * math.cos(angle))
            )
            current_z = max(
                0, min(max_z, current_z + step * math.sin(angle))
            )
            continue_chance *= cfg["clump_continue"]

    return objects


def generate_stones(
    profile: Mapping,
    height_data: np.ndarray,
    header: MapHeader,
    surface_data: np.ndarray,
    max_x: float,
    max_z: float,
    grid: PlacementGrid,
    stats: PlacementStats,
    seed: int,
    rng: random.Random,
) -> List[MapObject]:
    category_name = "stones"
    cfg = profile["categories"][category_name]
    global_cfg = profile["global"]
    colors = category_surface_colors(profile, cfg)
    objects: List[MapObject] = []

    log.info("Generating stones...")
    for _ in range(cfg["target"] * cfg["oversample"]):
        if len(objects) >= cfg["target"]:
            break

        stats.inc(category_name, "attempts")
        x, z = random_world_point(global_cfg["map_margin"], max_x, max_z, rng)
        valid, y, slope = validate_candidate(
            category_name=category_name,
            x=x,
            z=z,
            height_data=height_data,
            header=header,
            surface_data=surface_data,
            max_x=max_x,
            max_z=max_z,
            allowed_colors=colors,
            tolerance=global_cfg["color_tolerance"],
            min_height=cfg["min_height"],
            max_height=cfg["max_height"],
            max_slope=cfg["max_slope"],
            coast_required=cfg.get("require_real_coast", True),
            coast_radius=global_cfg["coast_search_radius"],
            coast_min_land_height=global_cfg["coast_min_land_height"],
            stats=stats,
        )
        if not valid:
            continue

        exclusion = cfg.get("exclude_altitude")
        if exclusion and abs(y - exclusion["center"]) <= exclusion["tolerance"]:
            stats.inc(category_name, "rejected_altitude_band")
            continue

        noise = noise_value(x, z, cfg, seed, rng)
        cluster_bias = cfg["cluster_bias"]
        if noise < cluster_bias and rng.random() > (noise / cluster_bias):
            stats.inc(category_name, "rejected_noise")
            continue

        if grid.too_close(x, z, global_cfg["solid_spacing"]):
            stats.inc(category_name, "rejected_spacing")
            continue

        pitch, roll = slope_to_pitch_roll(slope, rng)
        objects.append(
            MapObject(
                name=rng.choice(cfg["models"]),
                x=x,
                y=y,
                z=z,
                yaw=rng.uniform(0, 360),
                pitch=pitch,
                roll=roll,
                scale=rng.uniform(*cfg["scale"]),
                category="stone",
            )
        )
        grid.add(x, z)
        stats.placed(category_name)

    return objects


def generate_debris(
    profile: Mapping,
    height_data: np.ndarray,
    header: MapHeader,
    surface_data: np.ndarray,
    max_x: float,
    max_z: float,
    grid: PlacementGrid,
    stats: PlacementStats,
    rng: random.Random,
) -> List[MapObject]:
    category_name = "debris"
    cfg = profile["categories"][category_name]
    global_cfg = profile["global"]
    colors = category_surface_colors(profile, cfg)
    objects: List[MapObject] = []

    log.info("Generating debris...")
    for _ in range(cfg["target"] * cfg["max_attempts_per_object"]):
        if len(objects) >= cfg["target"]:
            break

        stats.inc(category_name, "attempts")
        x, z = random_world_point(global_cfg["map_margin"], max_x, max_z, rng)
        valid, y, _ = validate_candidate(
            category_name=category_name,
            x=x,
            z=z,
            height_data=height_data,
            header=header,
            surface_data=surface_data,
            max_x=max_x,
            max_z=max_z,
            allowed_colors=colors,
            tolerance=global_cfg["color_tolerance"],
            min_height=cfg["min_height"],
            max_height=cfg["max_height"],
            max_slope=cfg["max_slope"],
            coast_required=cfg.get("require_real_coast", True),
            coast_radius=global_cfg["coast_search_radius"],
            coast_min_land_height=global_cfg["coast_min_land_height"],
            stats=stats,
        )
        if not valid:
            continue

        if grid.too_close(x, z, cfg["min_spacing"]):
            stats.inc(category_name, "rejected_spacing")
            continue

        objects.append(
            MapObject(
                name=rng.choice(cfg["models"]),
                x=x,
                y=y,
                z=z,
                yaw=rng.uniform(0, 360),
                pitch=rng.uniform(*cfg["pitch"]),
                roll=rng.uniform(*cfg["roll"]),
                scale=rng.uniform(*cfg["scale"]),
                category="debris",
            )
        )
        grid.add(x, z)
        stats.placed(category_name)

    return objects


def generate_shrubs(
    profile: Mapping,
    height_data: np.ndarray,
    header: MapHeader,
    surface_data: np.ndarray,
    max_x: float,
    max_z: float,
    grid: PlacementGrid,
    stats: PlacementStats,
    rng: random.Random,
) -> List[MapObject]:
    category_name = "shrubs"
    cfg = profile["categories"][category_name]
    global_cfg = profile["global"]
    colors = category_surface_colors(profile, cfg)
    objects: List[MapObject] = []

    log.info("Generating shrubs...")
    for _ in range(cfg["target"] * cfg["max_attempts_per_object"]):
        if len(objects) >= cfg["target"]:
            break

        stats.inc(category_name, "attempts")
        x, z = random_world_point(global_cfg["map_margin"], max_x, max_z, rng)
        valid, y, _ = validate_candidate(
            category_name=category_name,
            x=x,
            z=z,
            height_data=height_data,
            header=header,
            surface_data=surface_data,
            max_x=max_x,
            max_z=max_z,
            allowed_colors=colors,
            tolerance=global_cfg["color_tolerance"],
            min_height=cfg["min_height"],
            max_height=cfg["max_height"],
            max_slope=cfg["max_slope"],
            coast_required=cfg.get("require_real_coast", False),
            coast_radius=global_cfg["coast_search_radius"],
            coast_min_land_height=global_cfg["coast_min_land_height"],
            stats=stats,
        )
        if not valid:
            continue

        if grid.too_close(x, z, cfg["min_spacing"]):
            stats.inc(category_name, "rejected_spacing")
            continue

        objects.append(
            MapObject(
                name=rng.choice(cfg["models"]),
                x=x,
                y=y,
                z=z,
                yaw=rng.uniform(0, 360),
                scale=rng.uniform(*cfg["scale"]),
                category="shrub",
            )
        )
        grid.add(x, z)
        stats.placed(category_name)

    return objects


GENERATORS = {
    "boats": generate_boats,
    "reeds": generate_reeds,
    "stones": generate_stones,
    "debris": generate_debris,
    "shrubs": generate_shrubs,
}


# ================================================================================
#  EXPORT
# ================================================================================


def export_terrain_builder(
    objects: Sequence[MapObject], path: Path, header: MapHeader
) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for obj in objects:
            handle.write(
                f'"{obj.name}";'
                f"{obj.x + header.xllcorner:.3f};"
                f"{obj.z + header.yllcorner:.3f};"
                f"{obj.y:.3f};{obj.yaw:.3f};{obj.pitch:.3f};{obj.roll:.3f};{obj.scale:.3f}\n"
            )


def export_dayz_editor(objects: Sequence[MapObject], path: Path) -> None:
    payload = {
        "MapName": "Noronha",
        "Objects": [
            {
                "type": obj.name,
                "position": [round(obj.x, 3), round(obj.y, 3), round(obj.z, 3)],
                "ypr": [
                    round(obj.yaw, 3),
                    round(obj.pitch, 3),
                    round(obj.roll, 3),
                ],
                "scale": round(obj.scale, 3),
            }
            for obj in objects
        ],
    }
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def export_by_category(
    objects: Sequence[MapObject], base_path: Path, header: MapHeader
) -> None:
    categories: Dict[str, List[MapObject]] = {}
    for obj in objects:
        categories.setdefault(obj.category, []).append(obj)

    for category, category_objects in sorted(categories.items()):
        export_terrain_builder(
            category_objects,
            Path(f"{base_path}_{category}_tb.txt"),
            header,
        )


def export_stats(
    *,
    stats: PlacementStats,
    path: Path,
    profile_name: str,
    seed: int,
    object_count: int,
    categories: Sequence[str],
    input_hashes: Mapping[str, str],
    output_hashes: Mapping[str, str] | None = None,
) -> None:
    payload = {
        "generator_version": 2,
        "profile": profile_name,
        "seed": seed,
        "categories": list(categories),
        "object_count": object_count,
        "input_sha256": dict(input_hashes),
        "output_sha256": dict(output_hashes or {}),
        "stats": stats.as_dict(),
    }
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


# ================================================================================
#  CLI / MAIN
# ================================================================================


def parse_categories(raw: str) -> List[str]:
    requested = [item.strip() for item in raw.split(",") if item.strip()]
    invalid = [name for name in requested if name not in GENERATORS]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Unknown categories: {', '.join(invalid)}. "
            f"Allowed: {', '.join(GENERATORS)}"
        )
    if not requested:
        raise argparse.ArgumentTypeError("At least one category is required")
    return requested


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic Noronha authoring placements."
    )
    parser.add_argument(
        "--heightmap",
        type=Path,
        required=True,
        help="ASCII grid heightmap (.asc).",
    )
    parser.add_argument(
        "--surfacemap", type=Path, required=True, help="Surface mask image."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path prefix, without category suffix.",
    )
    parser.add_argument(
        "--profiles",
        type=Path,
        default=DEFAULT_PROFILE_FILE,
        help=f"Placement profile JSON (default: {DEFAULT_PROFILE_FILE.name}).",
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE_NAME,
        help=f"Profile name inside placement profile JSON (default: {DEFAULT_PROFILE_NAME}).",
    )
    parser.add_argument(
        "--categories",
        type=parse_categories,
        default=list(GENERATORS),
        help="Comma-separated generators: boats,reeds,stones,debris,shrubs.",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Override profile random seed."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and report statistics without writing placement exports.",
    )
    parser.add_argument(
        "--stats",
        type=Path,
        default=None,
        help="Optional statistics JSON. Defaults to <output>_stats.json when not a dry run.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable debug logging."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    for label, path in (
        ("heightmap", args.heightmap),
        ("surfacemap", args.surfacemap),
        ("profiles", args.profiles),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"{label} not found: {path}")

    profile = load_profile(args.profiles, args.profile)
    global_cfg = profile["global"]
    seed = args.seed if args.seed is not None else int(global_cfg["random_seed"])

    height_data, header = load_heightmap(
        args.heightmap, float(global_cfg["sea_level"])
    )
    surface_data = load_surfacemap(args.surfacemap)
    max_x = header.ncols * header.cellsize
    max_z = header.nrows * header.cellsize

    grid = PlacementGrid(cell_size=float(global_cfg["solid_spacing"]) * 2)
    stats = PlacementStats()
    all_objects: List[MapObject] = []

    selected_categories = [name for name in GENERATORS if name in args.categories]
    for category_name in selected_categories:
        generator = GENERATORS[category_name]
        rng = category_rng(seed, category_name)
        if category_name == "stones":
            generated = generator(
                profile,
                height_data,
                header,
                surface_data,
                max_x,
                max_z,
                grid,
                stats,
                seed,
                rng,
            )
        else:
            generated = generator(
                profile,
                height_data,
                header,
                surface_data,
                max_x,
                max_z,
                grid,
                stats,
                rng,
            )
        all_objects.extend(generated)

    stats.log_summary()
    log.info(
        "Generated %d objects with profile '%s' and seed %d.",
        len(all_objects),
        args.profile,
        seed,
    )

    if args.dry_run:
        if args.stats:
            args.stats.parent.mkdir(parents=True, exist_ok=True)
            export_stats(
                stats=stats,
                path=args.stats,
                profile_name=args.profile,
                seed=seed,
                object_count=len(all_objects),
                categories=selected_categories,
                input_hashes={
                    "heightmap": file_sha256(args.heightmap),
                    "surfacemap": file_sha256(args.surfacemap),
                    "profiles": file_sha256(args.profiles),
                },
            )
        log.info("Dry run complete; placement exports were not written.")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_base = args.output
    export_terrain_builder(all_objects, Path(f"{output_base}_all_tb.txt"), header)
    export_dayz_editor(all_objects, Path(f"{output_base}_editor.json"))
    export_by_category(all_objects, output_base, header)

    stats_path = args.stats or Path(f"{output_base}_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    output_files = sorted(args.output.parent.glob(f"{args.output.name}_*"))
    export_stats(
        stats=stats,
        path=stats_path,
        profile_name=args.profile,
        seed=seed,
        object_count=len(all_objects),
        categories=selected_categories,
        input_hashes={
            "heightmap": file_sha256(args.heightmap),
            "surfacemap": file_sha256(args.surfacemap),
            "profiles": file_sha256(args.profiles),
        },
        output_hashes={path.name: file_sha256(path) for path in output_files if path.is_file()},
    )
    log.info("Completed exports aligned to the map origin.")


if __name__ == "__main__":
    main()
