from __future__ import annotations
from typing import Optional
from ..config import Config
from ..blender_exec import run_blender

def run(conf: Config, input_blend: Optional[str] = None, output_dir: Optional[str] = None,
        nx: Optional[int] = None, ny: Optional[int] = None):
    """Split a Blender scene into tiles."""
    input_blend = input_blend or conf.scene.blend
    if not input_blend:
        print("[ERROR] No input blend file specified")
        return
    
    nx = nx or conf.scene.tiling.nx
    ny = ny or conf.scene.tiling.ny
    
    # Create tiling script
    tiling_script = """
import bpy
import os
import sys

def tile_scene(input_path, output_dir, nx, ny):
    print(f"[TILING] Input: {input_path}")
    print(f"[TILING] Output: {output_dir}")
    print(f"[TILING] Tiles: {nx}x{ny}")
    
    # Load the scene
    bpy.ops.wm.open_mainfile(filepath=input_path)
    
    # Get scene bounds
    scene = bpy.context.scene
    if not scene.objects:
        print("[ERROR] No objects in scene")
        return
    
    # Calculate bounding box
    min_coords = [float('inf')] * 3
    max_coords = [float('-inf')] * 3
    
    for obj in scene.objects:
        if obj.type == 'MESH':
            for vertex in obj.bound_box:
                world_vertex = obj.matrix_world @ vertex
                for i in range(3):
                    min_coords[i] = min(min_coords[i], world_vertex[i])
                    max_coords[i] = max(max_coords[i], world_vertex[i])
    
    width = max_coords[0] - min_coords[0]
    height = max_coords[1] - min_coords[1]
    tile_width = width / nx
    tile_height = height / ny
    
    print(f"[TILING] Scene bounds: {min_coords} to {max_coords}")
    print(f"[TILING] Tile size: {tile_width:.2f} x {tile_height:.2f}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create tiles
    for i in range(nx):
        for j in range(ny):
            tile_name = f"tile_{i:02d}_{j:02d}"
            print(f"[TILING] Creating {tile_name}...")
            
            # Calculate tile bounds
            x_min = min_coords[0] + i * tile_width
            x_max = min_coords[0] + (i + 1) * tile_width
            y_min = min_coords[1] + j * tile_height
            y_max = min_coords[1] + (j + 1) * tile_height
            
            # Select objects in this tile
            bpy.ops.object.select_all(action='DESELECT')
            objects_in_tile = []
            
            for obj in scene.objects:
                if obj.type == 'MESH':
                    # Check if object center is in tile
                    center = obj.matrix_world.translation
                    if (x_min <= center[0] < x_max and 
                        y_min <= center[1] < y_max):
                        obj.select_set(True)
                        objects_in_tile.append(obj)
            
            if objects_in_tile:
                # Create new scene for this tile
                bpy.ops.scene.new(type='EMPTY')
                tile_scene = bpy.context.scene
                tile_scene.name = tile_name
                
                # Copy selected objects to new scene
                bpy.ops.object.make_links_scene(scene=tile_name)
                
                # Save tile
                tile_path = os.path.join(output_dir, f"{tile_name}.blend")
                bpy.ops.wm.save_as_mainfile(filepath=tile_path)
                print(f"[TILING] Saved {tile_path} ({len(objects_in_tile)} objects)")
            else:
                print(f"[TILING] No objects in {tile_name}, skipping")
    
    print("[TILING] Tiling complete!")

# Get arguments
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

def get_arg_value(arg_name, default_value=None):
    try:
        idx = argv.index(arg_name)
        return argv[idx + 1]
    except (ValueError, IndexError):
        return default_value

input_blend = get_arg_value("--input_blend", "")
output_dir = get_arg_value("--output_dir", "")
nx = int(get_arg_value("--nx", "2"))
ny = int(get_arg_value("--ny", "2"))

if input_blend and output_dir:
    tile_scene(input_blend, output_dir, nx, ny)
else:
    print("[ERROR] Missing required arguments: --input_blend, --output_dir")
"""
    
    # Write temporary script
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(tiling_script)
        temp_script = f.name
    
    try:
        args = [
            "--input_blend", input_blend,
            "--output_dir", output_dir or f"{input_blend}_tiles",
            "--nx", str(nx),
            "--ny", str(ny)
        ]
        rc = run_blender(conf.blender.bin, temp_script, None, args)
        if rc != 0:
            print(f"[ERROR] Tiling failed with code {rc}")
    finally:
        os.unlink(temp_script)