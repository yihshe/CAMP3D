
from __future__ import annotations
import os
from typing import Optional, List
from ..config import Config
from ..blender_exec import run_blender

def run(conf: Config,
        batch_dir: Optional[str] = None,
        batch_overwrite: bool = False,
        create_new_scene: bool = False,
        landscape_fbx: Optional[str] = None,
        trees_fbx: Optional[str] = None,
        objects_fbx: Optional[str] = None,
        blend_path: Optional[str] = None,
        tree_keywords: Optional[List[str]] = None):
    args = []
    if batch_dir:
        args += ["--batch_dir", batch_dir]
        args += ["--batch_overwrite", str(bool(batch_overwrite))]
    else:
        # Auto-detect if we need to create a new scene
        blend_file = blend_path or conf.scene.blend
        if not blend_file or not os.path.exists(blend_file):
            create_new_scene = True
        
        if create_new_scene:
            args += ["--create_new_scene", "True"]
        if landscape_fbx:
            args += ["--landscape_fbx", landscape_fbx]
        elif conf.unreal.get("landscape_fbx"):
            args += ["--landscape_fbx", conf.unreal["landscape_fbx"]]
        if trees_fbx:
            args += ["--trees_fbx", trees_fbx]
        elif conf.unreal.get("trees_fbx"):
            args += ["--trees_fbx", conf.unreal["trees_fbx"]]
        if objects_fbx:
            args += ["--objects_fbx", objects_fbx]
        if blend_path:
            args += ["--blend_path", blend_path]
        elif blend_file:
            args += ["--blend_path", blend_file]
        if tree_keywords:
            args += ["--tree_keywords", ",".join(tree_keywords)]
    rc = run_blender(conf.blender.bin, "scene_create.py", None, args)
    if rc != 0:
        raise SystemExit(rc)
