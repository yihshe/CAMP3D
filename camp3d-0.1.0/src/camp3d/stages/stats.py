from __future__ import annotations
import os
import tempfile
from typing import Optional
from ..config import Config
from ..blender_exec import run_blender

def run(conf: Config, blend: Optional[str] = None):
    """Generate statistics for a Blender scene."""
    blend = blend or conf.scene.blend
    if not blend:
        print("[ERROR] No blend file specified")
        return
    
    # Resolve the blend file path to absolute path
    if not os.path.isabs(blend):
        blend = os.path.abspath(blend)
    
    if not os.path.exists(blend):
        print(f"[ERROR] Blend file not found: {blend}")
        return
    
    # Create a simple stats script
    stats_script = """
import bpy
import os

def print_scene_stats():
    print("=== SCENE STATISTICS ===")
    print(f"Scene: {bpy.context.scene.name}")
    print(f"File: {bpy.data.filepath}")
    
    # Object counts
    total_objects = len(bpy.data.objects)
    mesh_objects = len([o for o in bpy.data.objects if o.type == 'MESH'])
    print(f"Total objects: {total_objects}")
    print(f"Mesh objects: {mesh_objects}")
    
    # Collection info
    print("\\nCollections:")
    for coll in bpy.data.collections:
        if coll.name != "Master Collection":
            mesh_count = len([o for o in coll.objects if o.type == 'MESH'])
            print(f"  {coll.name}: {len(coll.objects)} objects ({mesh_count} meshes)")
    
    # Material info
    print(f"\\nMaterials: {len(bpy.data.materials)}")
    for mat in bpy.data.materials:
        if mat.use_nodes:
            print(f"  {mat.name}: uses nodes")
        else:
            print(f"  {mat.name}: basic material")
    
    # Helios part IDs
    helios_objects = [o for o in bpy.data.objects if "helios_part_id" in o]
    print(f"\\nHelios tagged objects: {len(helios_objects)}")
    for obj in helios_objects:
        print(f"  {obj.name}: part_id={obj.get('helios_part_id', 'N/A')}")

print_scene_stats()
"""
    
    # Write temporary script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(stats_script)
        temp_script = f.name
    
    try:
        rc = run_blender(conf.blender.bin, temp_script, blend, [])
        if rc != 0:
            print(f"[ERROR] Stats generation failed with code {rc}")
    finally:
        os.unlink(temp_script)