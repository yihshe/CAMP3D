
from __future__ import annotations
from typing import Optional
from ..config import Config
from ..blender_exec import run_blender

def run(conf: Config, blend: Optional[str] = None, materials_dir: Optional[str] = None,
        output_dir: Optional[str] = None, scene_name: Optional[str] = None,
        use_own_materials: bool = True, materials_name: Optional[str] = None,
        save_scene_bbox: bool = True, save_survey_file: bool = False):
    # Use leafwood blend file if it exists, otherwise fall back to regular blend
    if blend is None:
        base_blend = conf.scene.blend
        if base_blend:
            # Try leafwood version first
            import os
            base, ext = os.path.splitext(base_blend)
            leafwood_blend = base + "_leafwood" + ext
            if os.path.exists(leafwood_blend):
                blend = leafwood_blend
            else:
                blend = base_blend
        else:
            blend = None
    materials_dir = materials_dir or conf.u2h.materials_dir
    output_dir = output_dir or conf.helios.get_output_dir()
    scene_name = scene_name or (conf.scene.name or "")
    args = [
        "--materials_dir", materials_dir,
        "--output_dir", output_dir,
        "--scene_name", scene_name,
        "--use_own_materials", str(use_own_materials),
        "--materials_name", materials_name or "",
        "--save_scene_bbox", str(save_scene_bbox),
        "--write_survey_file", str(save_survey_file),
    ]
    rc = run_blender(conf.blender.bin, "scene_export.py", blend, args)
    if rc != 0:
        raise SystemExit(rc)
