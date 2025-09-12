# blender2helios_extended.py
"""
End‑to‑end script for preparing Blender scenes from Unreal exports.

Revision history
----------------
* **2025‑04‑28** – initial public version with scene‑creation support.
* **2025‑04‑28 b** – keep existing cameras/lights instead of wiping whole scene.
* **2025‑04‑28 c** – **batch mode**: iterate over sub‑directories inside a user‑
  supplied folder, auto‑detect *_landscape.fbx* and *_trees.fbx*, and generate
  a *.blend* for each scene if one does not already exist.

Batch usage
-----------
Generate missing .blend files only (no Helios export):
```bash
blender --background --python blender2helios_extended.py -- \
    --batch_dir "D:/datasets/forest_scenes"        # contains scene sub‑folders
```
Single‑scene mode remains unchanged and is still controlled with the original
flags (`--create_new_scene`, `--landscape_fbx`, `--trees_fbx`, …).
"""
print("[SCRIPT] scene_create.py loaded", flush=True)
import sys
import os
import glob
import shutil
import bpy
import addon_utils
from mathutils import Vector
# import pdb;pdb.set_trace()  # noqa: E402

# Default tree keywords - can be overridden by command line args
TREE_KEYWORDS = []

###############################################################################
# -----------------------------  Arg parsing  --------------------------------#
###############################################################################

# ---------------------------------------------------------------------------
# Ensure FBX importer is enabled (needed when running head‑less)
# ---------------------------------------------------------------------------
if not addon_utils.check("import_scene_fbx")[1]:  # (is_enabled Boolean)
    addon_utils.enable("import_scene_fbx", default_set=False, persistent=True)
    print("[INIT] Enabled 'import_scene_fbx' add‑on")

argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

def get_arg_value(arg_name: str, default_value=None):
    try:
        idx = argv.index(arg_name)
        return argv[idx + 1]
    except (ValueError, IndexError):
        return default_value

###############################################################################
# -----------------------  Scene‑creation helpers  ---------------------------#
###############################################################################
def import_fbx(fbx_path: str):
    pre = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    return [o for o in bpy.data.objects if o not in pre]

def modify_scene_for_helios():
    # Collections containing cameras/lights → "Ignore" (except master root)
    for coll in bpy.data.collections:
        if coll is bpy.context.scene.collection:
            continue
        if any(o.type in {"CAMERA", "LIGHT"} for o in coll.objects):
            # Unlink all objects from this collection before renaming
            for obj in list(coll.objects):
                coll.objects.unlink(obj)
            coll.name = "Ignore"

    # Tag parts for Helios
    if (landscape := bpy.data.collections.get("Landscape")):
        for obj in landscape.objects:
            obj.name = "Landscape"
            obj["helios_part_id"] = 0
    if (trees := bpy.data.collections.get("Trees")):
        for idx, obj in enumerate(trees.objects, start=1):
            # obj.name = f"Tree{idx-1}"
            obj.name = "Tree"
            obj["helios_part_id"] = idx

    bpy.ops.wm.save_mainfile()
    print("[EXPORT] Scene modified for Helios export")

def create_scene_with_assets(landscape_fbx: str,
                             trees_fbx: str,
                             objects_fbx: str,
                             blend_path: str):
    print(f"[CREATE] Building scene → {blend_path}")

    # Remove default cube
    if (cube := bpy.data.objects.get("Cube")):
        bpy.data.objects.remove(cube, do_unlink=True)

    root = bpy.context.scene.collection
    # ensure collections
    landscape_coll = bpy.data.collections.get("Landscape") or bpy.data.collections.new("Landscape")
    trees_coll     = bpy.data.collections.get("Trees")     or bpy.data.collections.new("Trees")
    for coll in (landscape_coll, trees_coll):
        if coll.name not in root.children:
            root.children.link(coll)

    # Import landscape
    if landscape_fbx and os.path.exists(landscape_fbx):
        new_objs = import_fbx(landscape_fbx)
        for o in new_objs:
            if o.type == 'MESH' and o.name == "Landscape":
                landscape_coll.objects.link(o)
                if o.name in root.objects:
                    root.objects.unlink(o)
                print(f"  • Imported {os.path.basename(landscape_fbx)} → Basic Landscape")
            else:
                # Remove non‑landscape objects, filters can be added here
                bpy.data.objects.remove(o, do_unlink=True)
    else:
        print(f"  • [WARN] Missing landscape FBX: {landscape_fbx}")

    # Import trees or filter objects
    if trees_fbx and os.path.exists(trees_fbx):
        new_objs = import_fbx(trees_fbx)
        for o in new_objs:
            trees_coll.objects.link(o)
            if o.name in root.objects:
                root.objects.unlink(o)
        print(f"  • Imported {os.path.basename(trees_fbx)} → Trees ({len(new_objs)} objs)")
    elif objects_fbx and os.path.exists(objects_fbx):
        new_objs = import_fbx(objects_fbx)
        count_tree = count_land = 0
        for o in new_objs:
            name = o.data.name if hasattr(o, 'data') else o.name
            if any(kw in name for kw in TREE_KEYWORDS):
                trees_coll.objects.link(o)
                count_tree += 1
            else:
                landscape_coll.objects.link(o)
                count_land += 1
            if o.name in root.objects:
                root.objects.unlink(o)
        print(f"  • Imported {os.path.basename(objects_fbx)} → Trees({count_tree}), Landscape({count_land})")
    else:
        print(f"  • [WARN] Missing trees/objects FBX: {trees_fbx or objects_fbx}")

    # save blend and tag for Helios
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_mainfile(filepath=blend_path)
    # modify scene properties for Helios LiDAR simulation
    modify_scene_for_helios()
    print("  • .blend saved and tagged for Helios\n")


###############################################################################
# -------------------------  Batch‑mode logic  --------------------------# 
###############################################################################
def batch_create_scenes(batch_dir: str, overwrite=False):
    """Iterate through each immediate subfolder in *batch_dir* and build scenes.

    Each subfolder is expected to contain exactly two FBX files:
    * *_landscape.fbx
    * *_trees.fbx
    A .blend is created (or skipped if it already exists unless *overwrite* is
    True) with the same name as the folder (e.g. *scene123/scene123.blend*).
    """
    if not os.path.isdir(batch_dir):
        print(f"[ERROR] {batch_dir} is not a directory")
        return

    subs = [d for d in os.scandir(batch_dir) if d.is_dir()]
    print(f"[BATCH] {len(subs)} scenes in {batch_dir}")
    for entry in subs:
        scene = entry.name
        scene_dir = entry.path
        landsc = glob.glob(os.path.join(scene_dir, "*_landscape.fbx"))
        trees  = glob.glob(os.path.join(scene_dir, "*_trees.fbx"))
        objs   = glob.glob(os.path.join(scene_dir, "*_objects.fbx"))
        blendf = os.path.join(scene_dir, f"{scene}.blend")
        if os.path.exists(blendf) and not overwrite: 
            print(f"  ‑ Skipping '{scene}': .blend already exists")
            continue

        lf = landsc[0] if landsc else ''
        tf = trees[0] if trees else ''
        of = objs[0] if objs else ''

        bpy.ops.wm.read_factory_settings(use_empty=True)
        create_scene_with_assets(lf, tf, of, blendf)
    print("[BATCH] Done")

###############################################################################
# ------------------------------  Main entry  --------------------------------#
###############################################################################

# Batch flags
batch_dir        = get_arg_value("--batch_dir", "")
batch_overwrite  = get_arg_value("--batch_overwrite", "False").lower() == "true"

# Single‑scene flags (unchanged)
create_new_scene = get_arg_value("--create_new_scene", "False").lower() == "true"
landscape_fbx    = get_arg_value("--landscape_fbx", "")
trees_fbx        = get_arg_value("--trees_fbx",     "")
objects_fbx     = get_arg_value("--objects_fbx",   "")
blend_path      = get_arg_value("--blend_path",    os.path.abspath("autogen_scene.blend"))
tree_keywords   = get_arg_value("--tree_keywords", "")

# parse comma-separated tree keywords
if tree_keywords:
    TREE_KEYWORDS = [k.strip() for k in tree_keywords.split(",") if k.strip()]
else:
    TREE_KEYWORDS = []

# ---------------- Pipeline dispatcher ----------------
if batch_dir:
    batch_create_scenes(batch_dir,
                        overwrite=batch_overwrite)
    print("[BATCH] Processing complete – exiting")
    sys.exit(0)

# --- single‑scene path (original behaviour) ---
elif create_new_scene:
    create_scene_with_assets(landscape_fbx, trees_fbx, objects_fbx, blend_path)
else:
    print("[INFO] Using current .blend – skipping scene creation")