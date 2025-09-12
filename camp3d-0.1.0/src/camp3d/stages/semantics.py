
from __future__ import annotations
from typing import Optional, List
from ..config import Config
from ..blender_exec import run_blender

def run(conf: Config, blend: Optional[str] = None, trees_collection: Optional[str] = None,
        leaf_keywords: Optional[List[str]] = None, write_csv: bool = False):
    blend = blend or conf.scene.blend
    trees_collection = trees_collection or conf.scene.semantics.trees_collection
    leaf_keywords = leaf_keywords if leaf_keywords is not None else conf.scene.semantics.leaf_keywords
    args = []
    if blend:
        args += ["--blend_file", blend]
    if trees_collection:
        args += ["--trees_collection", trees_collection]
    if leaf_keywords:
        args += ["--leaf_keywords", ",".join(leaf_keywords)]
    args += ["--write_csv", str(write_csv or conf.scene.semantics.write_csv)]
    rc = run_blender(conf.blender.bin, "scene_customise_semantics.py", blend, args)
    if rc != 0:
        raise SystemExit(rc)
