#!/usr/bin/env python3
"""
Post-processing stage for converting HELIOS simulation output to ML-ready format.
Converts point cloud data and splits it into tiles for machine learning applications.
"""

from __future__ import annotations
from typing import Optional
import os
from pathlib import Path
import numpy as np
from plyfile import PlyElement, PlyData
from typing import List
from ..config import Config


def load_and_merge_xyz(scene_ts_dir: Path) -> np.ndarray:
    """Load all leg*_points.xyz under scene_ts_dir, return merged numpy array of shape (N, >=10)."""
    all_files = sorted(scene_ts_dir.glob("leg*_points.xyz"))
    pcs = []
    for fp in all_files:
        if fp.stat().st_size == 0:
            continue
        data = np.loadtxt(fp)
        if data.ndim == 1:
            data = data[None, :]
        pcs.append(data)
    if not pcs:
        # Fallback to an empty array with at least 10 columns so indexing works
        return np.empty((0, 10), dtype=float)
    merged = np.vstack(pcs)
    # Ensure we have at least 10 columns (x,y,z,intensity, ..., hit_id=col8, class=col9)
    if merged.shape[1] < 10:
        raise ValueError(f"Expected at least 10 columns in XYZ files, got {merged.shape[1]}")
    return merged


def compute_stats(merged: np.ndarray, vegetation_labels: set[int]):
    x, y = merged[:, 0], merged[:, 1]
    classes = merged[:, 9].astype(int)
    hit_ids = merged[:, 8].astype(int)

    veg_mask = np.isin(classes, list(vegetation_labels))

    # number of unique trees (by hit_id) among vegetation points
    tree_ids = np.unique(hit_ids[veg_mask])
    n_trees = len(tree_ids)

    # extents & area
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()
    area_m2 = max((xmax - xmin) * (ymax - ymin), 1e-9)  # avoid div by zero
    area_ha = area_m2 / 10000.0

    stem_density = n_trees / area_ha
    point_density = merged.shape[0] / area_m2

    print(f"Scene stats for area {area_m2:.1f} m² ({area_ha:.4f} ha):")
    print(f"  #Trees: {n_trees}  →  Stem density: {stem_density:.2f} trees/ha")
    print(f"  Total points: {merged.shape[0]} → Point density: {point_density:.3f} pts/m²\n")

    return xmin, ymin, xmax, ymax


def assign_trees_to_tiles(
    merged: np.ndarray,
    xmin: float, ymin: float,
    tile_size: float, nx: int, ny: int,
    vegetation_labels: set[int]
) -> np.ndarray:
    """
    Assign each vegetation point's tree (id col 8) to a tile based on the centroid of that tree's points.
    Vegetation is defined by vegetation_labels (e.g., {3} or {3,4}).
    """
    xs, ys = merged[:, 0], merged[:, 1]
    classes = merged[:, 9].astype(int)
    ids = merged[:, 8].astype(int)

    veg_mask = np.isin(classes, list(vegetation_labels))
    xs_t, ys_t, ids_t = xs[veg_mask], ys[veg_mask], ids[veg_mask]

    # Accumulate sums per tree id
    sums = {}  # tid -> [sum_x, sum_y, count]
    for x, y, tid in zip(xs_t, ys_t, ids_t):
        if tid not in sums:
            sums[tid] = [0.0, 0.0, 0]
        sums[tid][0] += x
        sums[tid][1] += y
        sums[tid][2] += 1

    # Compute centroid tile per tree
    tree_to_tile = {}
    for tid, (sx, sy, c) in sums.items():
        if c == 0:
            continue
        cx, cy = sx / c, sy / c
        ix = min(nx - 1, max(0, int((cx - xmin) // tile_size)))
        iy = min(ny - 1, max(0, int((cy - ymin) // tile_size)))
        tree_to_tile[tid] = ix * ny + iy

    # Assign all vegetation points according to their tree's tile; non-veg stays -1
    tile_assignment = -1 * np.ones(len(merged), dtype=int)
    if tree_to_tile:
        veg_indices = np.where(veg_mask)[0]
        for idx in veg_indices:
            tid = int(ids[idx])
            tile_assignment[idx] = tree_to_tile.get(tid, -1)

    return tile_assignment


def make_ply(vertices: np.ndarray, out_path: Path, text: bool = False):
    el = PlyElement.describe(vertices, 'vertex')
    PlyData([el], text=text).write(str(out_path))


def process_scene(
    scene_dir: Path, out_root: Path, tile_size: float, merge_all_ts: bool,
    ground_label: int, wood_label: int, leaf_label: int, leafwood: bool
):
    ts_dirs = sorted(d for d in scene_dir.iterdir() if d.is_dir())
    if not ts_dirs:
        return

    if merge_all_ts:
        print(f"\nScene: {scene_dir.name} (merging all timestamps)")
        merged_list = [load_and_merge_xyz(ts) for ts in ts_dirs]
        merged = np.vstack([m for m in merged_list if m.size]) if merged_list else np.empty((0, 10))
    else:
        latest = ts_dirs[-1]
        print(f"\nScene: {scene_dir.name} (using data from {latest.name})")
        merged = load_and_merge_xyz(latest)

    if merged.size == 0:
        print("  No points found; skipping.")
        return

    # Decide vegetation labels based on mode
    vegetation_labels = {wood_label, leaf_label} if leafwood else {wood_label}

    xmin, ymin, xmax, ymax = compute_stats(merged, vegetation_labels)

    dx = max(xmax - xmin, 1e-9)
    dy = max(ymax - ymin, 1e-9)
    nx = max(1, int(dx // tile_size))
    ny = max(1, int(dy // tile_size))
    print(f"Tiling into {nx}×{ny} cells (~{tile_size} m each)")

    pt_tile = assign_trees_to_tiles(merged, xmin, ymin, tile_size, nx, ny, vegetation_labels)

    # output per-scene folder
    scene_out = out_root / scene_dir.name
    scene_out.mkdir(parents=True, exist_ok=True)

    plot_idx = 0
    xs_all, ys_all = merged[:, 0], merged[:, 1]
    classes_all = merged[:, 9].astype(int)

    in_veg_all = np.isin(classes_all, list(vegetation_labels))
    is_ground_all = (classes_all == ground_label)

    for ix in range(nx):
        x0 = xmin + ix * tile_size
        x1 = xmin + (ix + 1) * tile_size if ix < nx - 1 else xmax
        for iy in range(ny):
            y0 = ymin + iy * tile_size
            y1 = ymin + (iy + 1) * tile_size if iy < ny - 1 else ymax

            in_tile = (xs_all >= x0) & (xs_all < x1) & (ys_all >= y0) & (ys_all < y1)
            if ix == nx - 1:
                in_tile &= (xs_all <= x1)
            if iy == ny - 1:
                in_tile &= (ys_all <= y1)

            # ground points in the geometric tile
            mask_ground = is_ground_all & in_tile
            # vegetation points whose tree centroid mapped to this tile
            mask_veg = in_veg_all & (pt_tile == (ix * ny + iy))
            sel = mask_ground | mask_veg
            if not sel.any():
                continue

            pts = merged[sel]
            n = pts.shape[0]
            arr = np.zeros(n, dtype=[
                ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                ('intensity', 'f4'),
                ('semantic_seg', 'f4'),
                ('treeID', 'f4')
            ])
            arr['x'], arr['y'], arr['z'] = pts[:, 0], pts[:, 1], pts[:, 2]
            arr['intensity'] = pts[:, 3]

            cls = pts[:, 9].astype(int)
            hit_ids = pts[:, 8].astype(int)

            if leafwood:
                # Keep original labels (e.g., 2/3/4) in output
                arr['semantic_seg'] = cls.astype('f4')
                # Keep treeID for any vegetation (wood or leaf), -1 for ground
                arr['treeID'] = np.where(np.isin(cls, list(vegetation_labels)), hit_ids, -1).astype('f4')
            else:
                # Original behavior: collapse to 1 (ground) / 2 (vegetation)
                arr['semantic_seg'] = np.where(cls == ground_label, 1.0, 2.0).astype('f4')
                # Keep treeID for vegetation (wood only), -1 for ground
                arr['treeID'] = np.where(cls == wood_label, hit_ids, -1).astype('f4')

            out_path = scene_out / f"{scene_dir.name}_plot_{plot_idx}_annotated.ply"
            make_ply(arr, out_path)
            plot_idx += 1

    print(f" → Saved {plot_idx} tiles under {scene_out}\n")


def process_timestamp_directory(
    timestamp_dir: Path, out_root: Path, tile_size: float, merge_all_ts: bool,
    ground_label: int, wood_label: int, leaf_label: int, leafwood: bool
):
    """Process a timestamp directory containing XYZ files directly."""
    print(f"\nProcessing timestamp directory: {timestamp_dir.name}")
    
    # Load and merge XYZ files from this timestamp directory
    merged = load_and_merge_xyz(timestamp_dir)
    
    if merged.size == 0:
        print("  No points found; skipping.")
        return

    # Decide vegetation labels based on mode
    vegetation_labels = {wood_label, leaf_label} if leafwood else {wood_label}

    xmin, ymin, xmax, ymax = compute_stats(merged, vegetation_labels)

    dx = max(xmax - xmin, 1e-9)
    dy = max(ymax - ymin, 1e-9)
    nx = max(1, int(dx // tile_size))
    ny = max(1, int(dy // tile_size))
    print(f"Tiling into {nx}×{ny} cells (~{tile_size} m each)")

    pt_tile = assign_trees_to_tiles(merged, xmin, ymin, tile_size, nx, ny, vegetation_labels)

    # output per-scene folder (use timestamp directory name as scene name)
    scene_out = out_root / timestamp_dir.name
    scene_out.mkdir(parents=True, exist_ok=True)

    plot_idx = 0
    xs_all, ys_all = merged[:, 0], merged[:, 1]
    classes_all = merged[:, 9].astype(int)

    in_veg_all = np.isin(classes_all, list(vegetation_labels))
    is_ground_all = (classes_all == ground_label)

    for ix in range(nx):
        x0 = xmin + ix * tile_size
        x1 = xmin + (ix + 1) * tile_size if ix < nx - 1 else xmax
        for iy in range(ny):
            y0 = ymin + iy * tile_size
            y1 = ymin + (iy + 1) * tile_size if iy < ny - 1 else ymax

            in_tile = (xs_all >= x0) & (xs_all < x1) & (ys_all >= y0) & (ys_all < y1)
            if ix == nx - 1:
                in_tile &= (xs_all <= x1)
            if iy == ny - 1:
                in_tile &= (ys_all <= y1)

            # ground points in the geometric tile
            mask_ground = is_ground_all & in_tile
            # vegetation points whose tree centroid mapped to this tile
            mask_veg = in_veg_all & (pt_tile == (ix * ny + iy))
            sel = mask_ground | mask_veg
            if not sel.any():
                continue

            pts = merged[sel]
            n = pts.shape[0]
            arr = np.zeros(n, dtype=[
                ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                ('intensity', 'f4'),
                ('semantic_seg', 'f4'),
                ('treeID', 'f4')
            ])
            arr['x'], arr['y'], arr['z'] = pts[:, 0], pts[:, 1], pts[:, 2]
            arr['intensity'] = pts[:, 3]

            cls = pts[:, 9].astype(int)
            hit_ids = pts[:, 8].astype(int)

            if leafwood:
                # Keep original labels (e.g., 2/3/4) in output
                arr['semantic_seg'] = cls.astype('f4')
                # Keep treeID for any vegetation (wood or leaf), -1 for ground
                arr['treeID'] = np.where(np.isin(cls, list(vegetation_labels)), hit_ids, -1).astype('f4')
            else:
                # Original behavior: collapse to 1 (ground) / 2 (vegetation)
                arr['semantic_seg'] = np.where(cls == ground_label, 1.0, 2.0).astype('f4')
                # Keep treeID for vegetation (wood only), -1 for ground
                arr['treeID'] = np.where(cls == wood_label, hit_ids, -1).astype('f4')

            out_path = scene_out / f"{timestamp_dir.name}_plot_{plot_idx}_annotated.ply"
            make_ply(arr, out_path)
            plot_idx += 1

    print(f" → Saved {plot_idx} tiles under {scene_out}\n")


def process_merged_timestamps(
    timestamp_dirs: List[Path], out_root: Path, tile_size: float,
    ground_label: int, wood_label: int, leaf_label: int, leafwood: bool
):
    """Process multiple timestamp directories by merging all XYZ files."""
    print(f"\nProcessing {len(timestamp_dirs)} timestamp directories (merged)")
    
    # Load and merge XYZ files from all timestamp directories
    merged_list = []
    for ts_dir in sorted(timestamp_dirs):
        print(f"  Loading from {ts_dir.name}...")
        merged_ts = load_and_merge_xyz(ts_dir)
        if merged_ts.size > 0:
            merged_list.append(merged_ts)
    
    if not merged_list:
        print("  No points found in any timestamp; skipping.")
        return
    
    # Merge all timestamps
    merged = np.vstack(merged_list)
    print(f"  Merged {len(merged_list)} timestamps into {merged.shape[0]} points")
    
    # Decide vegetation labels based on mode
    vegetation_labels = {wood_label, leaf_label} if leafwood else {wood_label}

    xmin, ymin, xmax, ymax = compute_stats(merged, vegetation_labels)

    dx = max(xmax - xmin, 1e-9)
    dy = max(ymax - ymin, 1e-9)
    nx = max(1, int(dx // tile_size))
    ny = max(1, int(dy // tile_size))
    print(f"Tiling into {nx}×{ny} cells (~{tile_size} m each)")

    pt_tile = assign_trees_to_tiles(merged, xmin, ymin, tile_size, nx, ny, vegetation_labels)

    # output per-scene folder (use parent directory name as scene name)
    scene_out = out_root / "merged_timestamps"
    scene_out.mkdir(parents=True, exist_ok=True)

    plot_idx = 0
    xs_all, ys_all = merged[:, 0], merged[:, 1]
    classes_all = merged[:, 9].astype(int)

    in_veg_all = np.isin(classes_all, list(vegetation_labels))
    is_ground_all = (classes_all == ground_label)

    for ix in range(nx):
        x0 = xmin + ix * tile_size
        x1 = xmin + (ix + 1) * tile_size if ix < nx - 1 else xmax
        for iy in range(ny):
            y0 = ymin + iy * tile_size
            y1 = ymin + (iy + 1) * tile_size if iy < ny - 1 else ymax

            in_tile = (xs_all >= x0) & (xs_all < x1) & (ys_all >= y0) & (ys_all < y1)
            if ix == nx - 1:
                in_tile &= (xs_all <= x1)
            if iy == ny - 1:
                in_tile &= (ys_all <= y1)

            # ground points in the geometric tile
            mask_ground = is_ground_all & in_tile
            # vegetation points whose tree centroid mapped to this tile
            mask_veg = in_veg_all & (pt_tile == (ix * ny + iy))
            sel = mask_ground | mask_veg
            if not sel.any():
                continue

            pts = merged[sel]
            n = pts.shape[0]
            arr = np.zeros(n, dtype=[
                ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                ('intensity', 'f4'),
                ('semantic_seg', 'f4'),
                ('treeID', 'f4')
            ])
            arr['x'], arr['y'], arr['z'] = pts[:, 0], pts[:, 1], pts[:, 2]
            arr['intensity'] = pts[:, 3]

            cls = pts[:, 9].astype(int)
            hit_ids = pts[:, 8].astype(int)

            if leafwood:
                # Keep original labels (e.g., 2/3/4) in output
                arr['semantic_seg'] = cls.astype('f4')
                # Keep treeID for any vegetation (wood or leaf), -1 for ground
                arr['treeID'] = np.where(np.isin(cls, list(vegetation_labels)), hit_ids, -1).astype('f4')
            else:
                # Original behavior: collapse to 1 (ground) / 2 (vegetation)
                arr['semantic_seg'] = np.where(cls == ground_label, 1.0, 2.0).astype('f4')
                # Keep treeID for vegetation (wood only), -1 for ground
                arr['treeID'] = np.where(cls == wood_label, hit_ids, -1).astype('f4')

            out_path = scene_out / f"merged_plot_{plot_idx}_annotated.ply"
            make_ply(arr, out_path)
            plot_idx += 1

    print(f" → Saved {plot_idx} tiles under {scene_out}\n")


def run(conf: Config, input_root: Optional[str] = None, output_root: Optional[str] = None,
        tile_size: Optional[float] = None, merge_all_ts: Optional[bool] = None,
        ground_label: Optional[int] = None, wood_label: Optional[int] = None,
        leaf_label: Optional[int] = None, leafwood: Optional[bool] = None):
    """
    Post-process HELIOS simulation output to ML-ready format.
    
    Args:
        conf: Configuration object
        input_root: Root directory of HELIOS output (e.g., helios/output/SceneName)
        output_root: Root directory where processed .ply files will be saved
        tile_size: Tile edge length in meters (default: 50.0)
        merge_all_ts: Merge all timestamps for each scene instead of only the latest
        ground_label: Semantic ID for ground points (default: 2)
        wood_label: Semantic ID for wood/tree points (default: 3)
        leaf_label: Semantic ID for leaf points (default: 4)
        leafwood: If True, treat vegetation as {wood_label, leaf_label} and keep original labels
    """
    # Set defaults from config or function defaults
    input_root = input_root or conf.postprocess.input_root
    output_root = output_root or conf.postprocess.output_root
    tile_size = tile_size or conf.postprocess.tile_size
    merge_all_ts = merge_all_ts if merge_all_ts is not None else conf.postprocess.merge_all_ts
    ground_label = ground_label or conf.postprocess.ground_label
    wood_label = wood_label or conf.postprocess.wood_label
    leaf_label = leaf_label or conf.postprocess.leaf_label
    leafwood = leafwood if leafwood is not None else conf.postprocess.leafwood

    if not input_root:
        print("[ERROR] No input root specified")
        return

    input_path = Path(input_root)
    out_path = Path(output_root)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Processing scenes from: {input_path}")
    print(f"[INFO] Output directory: {out_path}")
    print(f"[INFO] Tile size: {tile_size}m")
    print(f"[INFO] Merge all timestamps: {merge_all_ts}")
    print(f"[INFO] Labels - Ground: {ground_label}, Wood: {wood_label}, Leaf: {leaf_label}")
    print(f"[INFO] Leafwood mode: {leafwood}\n")

    # Check if input directory contains XYZ files directly (single timestamp case)
    xyz_files = list(input_path.glob("leg*_points.xyz"))
    if xyz_files:
        print(f"[INFO] Found XYZ files directly in input directory - treating as single timestamp")
        process_timestamp_directory(
            input_path, out_path, tile_size, merge_all_ts,
            ground_label, wood_label, leaf_label, leafwood
        )
    else:
        # Look for timestamp subdirectories (multiple timestamps case)
        timestamp_dirs = [d for d in input_path.iterdir() if d.is_dir()]
        if timestamp_dirs:
            print(f"[INFO] Found {len(timestamp_dirs)} timestamp directories")
            if merge_all_ts:
                print(f"[INFO] Merging all timestamps into single scene")
                process_merged_timestamps(
                    timestamp_dirs, out_path, tile_size,
                    ground_label, wood_label, leaf_label, leafwood
                )
            else:
                print(f"[INFO] Using latest timestamp only")
                latest_timestamp = sorted(timestamp_dirs)[-1]
                process_timestamp_directory(
                    latest_timestamp, out_path, tile_size, merge_all_ts,
                    ground_label, wood_label, leaf_label, leafwood
                )
        else:
            # Look for scene subdirectories (original multi-scene case)
            for scene in sorted(input_path.iterdir()):
                if scene.is_dir():
                    process_scene(
                        scene, out_path, tile_size, merge_all_ts,
                        ground_label, wood_label, leaf_label, leafwood
                    )
