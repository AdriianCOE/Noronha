# ==============================================================================
#  NORONHA — Coastal Object Placement Generator (Com Radar de Terra Firme)
#  Autor: AdriianCOE
# ==============================================================================

import os
import sys
import math
import random
import json
import logging
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from PIL import Image

try:
    from noise import pnoise2
    NOISE_AVAILABLE = True
except ImportError:
    NOISE_AVAILABLE = False

# ==============================================================================
#  CONFIGURACOES DO USUARIO
# ==============================================================================

OUTPUT_PATH_BASE  = "P:/Noronha/source/scripts/generated_coastal_objects"
HEIGHTMAP_PATH    = "P:/Noronha/source/QGIS/gtt_heightmap.asc"
SURFACEMAP_PATH   = "P:/Noronha/source/QGIS/gtt_mask_osm.bmp"

RANDOM_SEED       = 42
SEA_LEVEL         = 0.0
LOG_LEVEL         = logging.INFO

COASTAL_COLOR         = (140, 137, 98)   
DIRT_BUFFER_COLOR     = (104,  85, 49)   
ROCK_COLOR            = ( 80,  80, 80)   
VEGETATION_COLOR      = ( 34, 100, 34)   

COLOR_TOLERANCE       = 50   

EXCLUSION_ALT_CENTER    = 5.0
EXCLUSION_ALT_TOLERANCE = 0.02
MAP_MARGIN              = 150.0 

# ==============================================================================
#  PARAMETROS POR CATEGORIA DE OBJETO (ATUALIZADO)
# ==============================================================================

BOAT_MODELS = ["Boat_Small1", "Boat_Small2", "Boat_Small3"]
STONE_MODELS = ["stone6_moss", "stone7_moss", "stone8_moss", "stone9_moss", "stone10_moss"]
REED_MODEL = "b_phragmitesaustralis_summer"
BOAT_GEAR_MODELS = [("misc_boxwooden",  20)]
DEBRIS_MODELS = ["garbage_groundsq_5m"]
SHRUB_MODELS = ["b_SambucusNigra_2s", "b_CorylusAvellana_1f", "b_RosaCanina_1s"]

BOAT_TOTAL_CLUSTERS         = 80
BOAT_CLUSTER_MIN_SIZE       = 1
BOAT_CLUSTER_MAX_SIZE       = 3
BOAT_CLUSTER_RADIUS         = 6.0
BOAT_MIN_HEIGHT             = -0.2     
BOAT_MAX_HEIGHT             = 12.0
BOAT_MAX_SLOPE              = 5.0
BOAT_GEAR_CHANCE            = 0.75
MIN_SPACING_BETWEEN_CLUSTERS= 120.0

REED_TOTAL_ATTEMPTS         = 600000   
REED_MIN_HEIGHT             = -0.20
REED_MAX_HEIGHT             =  1.50
REED_MIN_SPACING            =  3.0
REED_MAX_SPACING            =  5.5
REED_CLUMP_CHANCE           =  0.012
REED_CLUMP_CONTINUE         =  0.88
REED_CLUMP_MAX_SIZE         =  18

STONE_TOTAL_TARGET          = 35000
STONE_OVERSAMPLE            = 15       
STONE_MIN_HEIGHT            = -0.1     
STONE_MAX_HEIGHT            =  8.0
STONE_MAX_SLOPE             = 35.0
STONE_NOISE_SCALE           = 48.0
STONE_NOISE_OCTAVES         = 5
STONE_NOISE_PERSISTENCE     = 0.55
STONE_NOISE_LACUNARITY      = 2.1
STONE_CLUSTER_BIAS          = 0.65

DEBRIS_TOTAL_TARGET         = 300
DEBRIS_MIN_HEIGHT           = 0.0
DEBRIS_MAX_HEIGHT           = 8.0
DEBRIS_MAX_SLOPE            = 15.0
DEBRIS_MIN_SPACING          = 6.0

SHRUB_TOTAL_TARGET          = 800
SHRUB_MIN_HEIGHT            = 1.0    # Força nascer na terra firme
SHRUB_MAX_HEIGHT            = 15.0
SHRUB_MAX_SLOPE             = 25.0
SHRUB_MIN_SPACING           = 4.0

MIN_SPACING_SOLID_OBJECTS   = 4.0

# ==============================================================================
#  DATA CLASSES & LOGGING
# ==============================================================================

@dataclass
class MapObject:
    name:  str; x: float; y: float; z: float
    yaw: float = 0.0; pitch: float = 0.0; roll: float = 0.0; scale: float = 1.0; category: str = "generic"

@dataclass
class MapHeader:
    ncols: int; nrows: int; xllcorner: float; yllcorner: float; cellsize: float; nodata: float

def setup_logging():
    logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

# ==============================================================================
#  CORE FUNCTIONS
# ==============================================================================

def load_heightmap(path: str) -> Tuple[np.ndarray, MapHeader]:
    log.info(f"Carregando heightmap: {path}")
    with open(path) as f: lines = [f.readline() for _ in range(6)]
    hdr = MapHeader(ncols=int(lines[0].split()[1]), nrows=int(lines[1].split()[1]), xllcorner=float(lines[2].split()[1]), yllcorner=float(lines[3].split()[1]), cellsize=float(lines[4].split()[1]), nodata=float(lines[5].split()[1]))
    data = np.loadtxt(path, skiprows=6)
    data[data == hdr.nodata] = SEA_LEVEL
    return data, hdr

def load_surfacemap(path: str) -> np.ndarray:
    log.info(f"Carregando surfacemap: {path}")
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(path) as img: return np.array(img.convert('RGB'))

def world_to_heightmap(x: float, z: float, hdr: MapHeader) -> Tuple[int, int]:
    col, row = int(x / hdr.cellsize), int((hdr.nrows - 1) - (z / hdr.cellsize))
    return max(0, min(hdr.nrows - 1, row)), max(0, min(hdr.ncols - 1, col))

def world_to_surface(x: float, z: float, surf_shape: Tuple[int, int], max_x: float, max_z: float) -> Tuple[int, int]:
    cs = max_x / surf_shape[1]
    col, row = int(x / cs), int((surf_shape[0] - 1) - (z / cs))
    return max(0, min(surf_shape[0] - 1, row)), max(0, min(surf_shape[1] - 1, col))

def get_altitude(x: float, z: float, height_data: np.ndarray, hdr: MapHeader) -> float:
    r, c = world_to_heightmap(x, z, hdr)
    return float(height_data[r, c])

def get_slope(x: float, z: float, height_data: np.ndarray, hdr: MapHeader) -> float:
    r, c = world_to_heightmap(x, z, hdr)
    if r <= 0 or r >= height_data.shape[0]-1 or c <= 0 or c >= height_data.shape[1]-1: return 0.0
    dz_dx, dz_dy = (height_data[r, c+1] - height_data[r, c-1]) / (2 * hdr.cellsize), (height_data[r+1, c] - height_data[r-1, c]) / (2 * hdr.cellsize)
    return math.degrees(math.atan(math.sqrt(dz_dx**2 + dz_dy**2)))

def get_surface_color(x: float, z: float, surface_data: np.ndarray, max_x: float, max_z: float) -> Tuple[int, int, int]:
    r, c = world_to_surface(x, z, surface_data.shape, max_x, max_z)
    return tuple(surface_data[r, c][:3])

def is_color(pixel: Tuple, target: Tuple, tol: float = COLOR_TOLERANCE) -> bool:
    return math.sqrt(sum((a - b)**2 for a, b in zip(pixel, target))) <= tol

def slope_to_pitch_roll(slope_deg: float) -> Tuple[float, float]:
    j = slope_deg * 0.3
    return random.uniform(-j, j), random.uniform(-j, j)

# ==============================================================================
#  O NOVO RADAR DE TERRA FIRME
# ==============================================================================
def is_real_coast(x: float, z: float, height_data: np.ndarray, hdr: MapHeader, search_radius: float = 40.0) -> bool:
    """Verifica se existe terra firme nas redondezas para ignorar linhas falsas no mar."""
    alt_n = get_altitude(x, z + search_radius, height_data, hdr)
    alt_s = get_altitude(x, z - search_radius, height_data, hdr)
    alt_e = get_altitude(x + search_radius, z, height_data, hdr)
    alt_w = get_altitude(x - search_radius, z, height_data, hdr)
    
    # Se pelo menos um dos lados atingir 1.0m de altura, significa que a ilha esta proxima
    return max(alt_n, alt_s, alt_e, alt_w) >= 1.0

class PlacementGrid:
    def __init__(self, cell_size: float, max_x: float, max_z: float):
        self.cell, self.grid = cell_size, {}
    def _k(self, x, z): return int(x / self.cell), int(z / self.cell)
    def too_close(self, x, z, md):
        cx, cz = self._k(x, z)
        r = int(math.ceil(md / self.cell)) + 1
        for dx in range(-r, r+1):
            for dz in range(-r, r+1):
                if any(math.hypot(x - ox, z - oz) < md for ox, oz in self.grid.get((cx+dx, cz+dz), [])): return True
        return False
    def add(self, x, z): self.grid.setdefault(self._k(x, z), []).append((x, z))

def noise_value(x: float, z: float, seed: int = 0) -> float:
    if NOISE_AVAILABLE: return (pnoise2(x/STONE_NOISE_SCALE + seed*100, z/STONE_NOISE_SCALE + seed*100, octaves=STONE_NOISE_OCTAVES, persistence=STONE_NOISE_PERSISTENCE, lacunarity=STONE_NOISE_LACUNARITY) + 1) / 2
    return random.random()

# ==============================================================================
#  GERADORES
# ==============================================================================

def generate_boats(height_data, hdr, surface_data, max_x, max_z, grid):
    log.info("Gerando barcos...")
    objects, cluster_centers, attempts = [], [], 0
    while len(cluster_centers) < BOAT_TOTAL_CLUSTERS and attempts < BOAT_TOTAL_CLUSTERS * 10000:
        attempts += 1
        x, z = random.uniform(MAP_MARGIN, max_x - MAP_MARGIN), random.uniform(MAP_MARGIN, max_z - MAP_MARGIN)
        y = get_altitude(x, z, height_data, hdr)
        if not (BOAT_MIN_HEIGHT <= y <= BOAT_MAX_HEIGHT) or get_slope(x, z, height_data, hdr) > BOAT_MAX_SLOPE: continue
        if not is_color(get_surface_color(x, z, surface_data, max_x, max_z), COASTAL_COLOR): continue
        
        # O Radar de Terra Firme entra em acao aqui!
        if not is_real_coast(x, z, height_data, hdr): continue
        
        if any(math.hypot(x - cx, z - cz) < MIN_SPACING_BETWEEN_CLUSTERS for cx, cz in cluster_centers): continue

                # ... dentro do loop de barcos ...
        if not is_color(get_surface_color(x, z, surface_data, max_x, max_z), COASTAL_COLOR): 
            continue

        # ADICIONE ESTA LINHA AQUI:
        if not is_real_island(x, z, height_data, hdr): 
            continue

        cluster_centers.append((x, z))
        for _ in range(random.randint(BOAT_CLUSTER_MIN_SIZE, BOAT_CLUSTER_MAX_SIZE)):
            bx, bz = x + random.uniform(-BOAT_CLUSTER_RADIUS, BOAT_CLUSTER_RADIUS), z + random.uniform(-BOAT_CLUSTER_RADIUS, BOAT_CLUSTER_RADIUS)
            if grid.too_close(bx, bz, MIN_SPACING_SOLID_OBJECTS): continue
            pitch, roll = slope_to_pitch_roll(get_slope(bx, bz, height_data, hdr))
            model = random.choice(BOAT_MODELS)
            if "Wreck" in model: roll, pitch = random.uniform(-25, 25), random.uniform(-10, 10)
            objects.append(MapObject(name=model, x=bx, y=get_altitude(bx, bz, height_data, hdr), z=bz, yaw=random.uniform(0, 360), pitch=pitch, roll=roll, scale=random.uniform(0.95, 1.05), category="boat"))
            grid.add(bx, bz)
            
            if random.random() < BOAT_GEAR_CHANCE:
                gx, gz = bx + random.uniform(-3, 3), bz + random.uniform(-3, 3)
                if not grid.too_close(gx, gz, 2.0):
                    objects.append(MapObject(name=BOAT_GEAR_MODELS[0][0], x=gx, y=get_altitude(gx, gz, height_data, hdr), z=gz, yaw=random.uniform(0, 360), scale=random.uniform(0.9, 1.1), category="boat"))
                    grid.add(gx, gz)
    return objects

def generate_reeds(height_data, hdr, surface_data, max_x, max_z, grid):
    log.info("Gerando juncos...")
    objects = []
    for _ in range(REED_TOTAL_ATTEMPTS):
        x, z = random.uniform(MAP_MARGIN, max_x - MAP_MARGIN), random.uniform(MAP_MARGIN, max_z - MAP_MARGIN)
        y = get_altitude(x, z, height_data, hdr)
        if not (REED_MIN_HEIGHT <= y <= REED_MAX_HEIGHT): continue
        c = get_surface_color(x, z, surface_data, max_x, max_z)
        if not (is_color(c, COASTAL_COLOR) or is_color(c, DIRT_BUFFER_COLOR)): continue
        
        # O Radar de Terra Firme bloqueia juncos no meio do oceano
        if not is_real_coast(x, z, height_data, hdr): continue
        
        if random.random() > REED_CLUMP_CHANCE or grid.too_close(x, z, REED_MIN_SPACING): continue

                # ... dentro do loop de barcos ...
        if not is_color(get_surface_color(x, z, surface_data, max_x, max_z), COASTAL_COLOR): 
            continue

        # ADICIONE ESTA LINHA AQUI:
        if not is_real_island(x, z, height_data, hdr): 
            continue

        clump_size, cx, cz, cc = 0, x, z, 1.0
        while clump_size < REED_CLUMP_MAX_SIZE and random.random() < cc:
            cy = get_altitude(cx, cz, height_data, hdr)
            if REED_MIN_HEIGHT <= cy <= REED_MAX_HEIGHT and not grid.too_close(cx, cz, REED_MIN_SPACING):
                objects.append(MapObject(name=REED_MODEL, x=cx, y=cy, z=cz, yaw=random.uniform(0, 360), scale=random.uniform(0.7, 1.3), category="reed"))
                grid.add(cx, cz)
                clump_size += 1
            a, s = random.uniform(0, 2 * math.pi), random.uniform(REED_MIN_SPACING, REED_MAX_SPACING)
            cx, cz = max(0, min(max_x, cx + s * math.cos(a))), max(0, min(max_z, cz + s * math.sin(a)))
            cc *= REED_CLUMP_CONTINUE
    return objects

def generate_stones(height_data, hdr, surface_data, max_x, max_z, grid):
    log.info(f"Gerando pedras...")
    objects = []
    for _ in range(STONE_TOTAL_TARGET * STONE_OVERSAMPLE):
        if len(objects) >= STONE_TOTAL_TARGET: break
        x, z = random.uniform(MAP_MARGIN, max_x - MAP_MARGIN), random.uniform(MAP_MARGIN, max_z - MAP_MARGIN)
        y = get_altitude(x, z, height_data, hdr)
        if not (STONE_MIN_HEIGHT <= y <= STONE_MAX_HEIGHT) or abs(y - EXCLUSION_ALT_CENTER) <= EXCLUSION_ALT_TOLERANCE or get_slope(x, z, height_data, hdr) > STONE_MAX_SLOPE: continue
        c = get_surface_color(x, z, surface_data, max_x, max_z)
        if not (is_color(c, COASTAL_COLOR) or is_color(c, ROCK_COLOR) or is_color(c, DIRT_BUFFER_COLOR)): continue
        
        # O Radar de Terra Firme bloqueia pedras no meio do oceano
        if not is_real_coast(x, z, height_data, hdr): continue

                # ... dentro do loop de barcos ...
        if not is_color(get_surface_color(x, z, surface_data, max_x, max_z), COASTAL_COLOR): 
            continue

        # ADICIONE ESTA LINHA AQUI:
        if not is_real_island(x, z, height_data, hdr): 
            continue
        
        nv = noise_value(x, z, seed=RANDOM_SEED)
        if nv < STONE_CLUSTER_BIAS and random.random() > (nv / STONE_CLUSTER_BIAS): continue
        if grid.too_close(x, z, MIN_SPACING_SOLID_OBJECTS): continue
        p, r = slope_to_pitch_roll(get_slope(x, z, height_data, hdr))
        objects.append(MapObject(name=random.choice(STONE_MODELS), x=x, y=y, z=z, yaw=random.uniform(0, 360), pitch=p, roll=r, scale=random.uniform(0.7, 1.6), category="stone"))
        grid.add(x, z)
    return objects

def generate_debris(height_data, hdr, surface_data, max_x, max_z, grid):
    log.info("Gerando destrocos...")
    objects, attempts = [], 0
    while len(objects) < DEBRIS_TOTAL_TARGET and attempts < DEBRIS_TOTAL_TARGET * 5000:
        attempts += 1
        x, z = random.uniform(MAP_MARGIN, max_x - MAP_MARGIN), random.uniform(MAP_MARGIN, max_z - MAP_MARGIN)
        y = get_altitude(x, z, height_data, hdr)
        if not (DEBRIS_MIN_HEIGHT <= y <= DEBRIS_MAX_HEIGHT) or get_slope(x, z, height_data, hdr) > DEBRIS_MAX_SLOPE: continue
        if not is_color(get_surface_color(x, z, surface_data, max_x, max_z), COASTAL_COLOR) or grid.too_close(x, z, DEBRIS_MIN_SPACING): continue
        
        # O Radar de Terra Firme bloqueia lixo no meio do oceano
        if not is_real_coast(x, z, height_data, hdr): continue

                # ... dentro do loop de barcos ...
        if not is_color(get_surface_color(x, z, surface_data, max_x, max_z), COASTAL_COLOR): 
            continue

        # ADICIONE ESTA LINHA AQUI:
        if not is_real_island(x, z, height_data, hdr): 
            continue
        
        objects.append(MapObject(name=random.choice(DEBRIS_MODELS), x=x, y=y, z=z, yaw=random.uniform(0, 360), pitch=random.uniform(-20, 20), roll=random.uniform(-25, 25), scale=random.uniform(0.8, 1.3), category="debris"))
        grid.add(x, z)
    return objects

def generate_shrubs(height_data, hdr, surface_data, max_x, max_z, grid):
    log.info("Gerando arbustos...")
    objects, attempts = [], 0
    while len(objects) < SHRUB_TOTAL_TARGET and attempts < SHRUB_TOTAL_TARGET * 5000:
        attempts += 1
        x, z = random.uniform(MAP_MARGIN, max_x - MAP_MARGIN), random.uniform(MAP_MARGIN, max_z - MAP_MARGIN)
        y = get_altitude(x, z, height_data, hdr)
        if not (SHRUB_MIN_HEIGHT <= y <= SHRUB_MAX_HEIGHT) or get_slope(x, z, height_data, hdr) > SHRUB_MAX_SLOPE: continue
        c = get_surface_color(x, z, surface_data, max_x, max_z)

                # ... dentro do loop de barcos ...
        if not is_color(get_surface_color(x, z, surface_data, max_x, max_z), COASTAL_COLOR): 
            continue

        # ADICIONE ESTA LINHA AQUI:
        if not is_real_island(x, z, height_data, hdr): 
            continue
        if not (is_color(c, COASTAL_COLOR) or is_color(c, VEGETATION_COLOR) or is_color(c, DIRT_BUFFER_COLOR)) or grid.too_close(x, z, SHRUB_MIN_SPACING): continue
        objects.append(MapObject(name=random.choice(SHRUB_MODELS), x=x, y=y, z=z, yaw=random.uniform(0, 360), scale=random.uniform(0.7, 1.2), category="shrub"))
        grid.add(x, z)
    return objects

# ==============================================================================
#  EXPORTADORES COM OFFSET GPS
# ==============================================================================

def export_terrain_builder(objects: List[MapObject], path: str, hdr: MapHeader):
    with open(path, 'w', encoding='utf-8') as f:
        for o in objects:
            f.write(f'"{o.name}";{o.x + hdr.xllcorner:.3f};{o.z + hdr.yllcorner:.3f};{o.y:.3f};{o.yaw:.3f};{o.pitch:.3f};{o.roll:.3f};{o.scale:.3f}\n')

def export_dayz_editor(objects: List[MapObject], path: str):
    payload = {"MapName": "Noronha", "Objects": [{"type": o.name, "position": [round(o.x, 3), round(o.y, 3), round(o.z, 3)], "ypr": [round(o.yaw, 3), round(o.pitch, 3), round(o.roll, 3)], "scale": round(o.scale, 3)} for o in objects]}
    with open(path, 'w', encoding='utf-8') as f: json.dump(payload, f, indent=2, ensure_ascii=False)

def export_by_category(objects: List[MapObject], base_path: str, hdr: MapHeader):
    categories = {}
    for o in objects: categories.setdefault(o.category, []).append(o)
    for cat, objs in categories.items():
        with open(f"{base_path}_{cat}_tb.txt", 'w', encoding='utf-8') as f:
            for o in objs:
                f.write(f'"{o.name}";{o.x + hdr.xllcorner:.3f};{o.z + hdr.yllcorner:.3f};{o.y:.3f};{o.yaw:.3f};{o.pitch:.3f};{o.roll:.3f};{o.scale:.3f}\n')

# ==============================================================================
#  MAIN
# ==============================================================================

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH_BASE), exist_ok=True)
    setup_logging()
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    height_data, hdr = load_heightmap(HEIGHTMAP_PATH)
    surface_data = load_surfacemap(SURFACEMAP_PATH)
    max_x, max_z = hdr.ncols * hdr.cellsize, hdr.nrows * hdr.cellsize
    grid = PlacementGrid(cell_size=MIN_SPACING_SOLID_OBJECTS * 2, max_x=max_x, max_z=max_z)

    all_objects = (
        generate_boats(height_data, hdr, surface_data, max_x, max_z, grid) + 
        generate_reeds(height_data, hdr, surface_data, max_x, max_z, grid) + 
        generate_stones(height_data, hdr, surface_data, max_x, max_z, grid) + 
        generate_debris(height_data, hdr, surface_data, max_x, max_z, grid) + 
        generate_shrubs(height_data, hdr, surface_data, max_x, max_z, grid)
    )
    
    export_terrain_builder(all_objects, f"{OUTPUT_PATH_BASE}_all_tb.txt", hdr)
    export_dayz_editor(all_objects,     f"{OUTPUT_PATH_BASE}_editor.json")
    export_by_category(all_objects,      OUTPUT_PATH_BASE, hdr)
    log.info("\nConcluido e alinhado ao GPS!")

if __name__ == "__main__":
    main()