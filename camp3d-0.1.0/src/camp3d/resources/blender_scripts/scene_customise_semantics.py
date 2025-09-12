# label_customization_extended.py
"""
Companion to blender2helios_extended.py.
Purpose:
- Load an existing .blend file.
- Split each tree into wood/leaves by material keywords.
- Move to Trees_Wood / Trees_Leaves collections (semantic classes).
- Assign SAME helios_part_id to both parts of a tree (instance id).
- Preserve existing helios_part_id if present; otherwise allocate new ids.
- Remove original Trees collection after splitting.
- Save as new .blend with '_labeled' suffix.
- Optionally write labels.csv next to the new .blend.

Run BEFORE Blender2Helios export.
"""

import sys
import os
import csv
import bpy
import bmesh

print("[SCRIPT] label_customization_extended.py loaded", flush=True)

###############################################################################
# ----------------------------- Arg parsing ----------------------------------#
###############################################################################

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

blend_file = get_arg_value("--blend_file", "")
trees_collection = get_arg_value("--trees_collection", "Trees")
leaf_keywords_arg = get_arg_value("--leaf_keywords", "Leaves,MTL_RW_Needles,MI_birch_branch,MI_pine_branch,MI_Leaves,leaf,MI_Pine_Tree_Needles,MI_Scots_Pine_Sheet_Sick,MI_Scots_Pine_Sheet,MI_Pine_Mountain_Ash_Sheet,TwoSided,Decoration,decoration")
write_csv = (get_arg_value("--write_csv", "True") or "True").lower() == "true"

LEAF_KEYWORDS = [k.strip() for k in (leaf_keywords_arg or "").split(",") if k.strip()]

###############################################################################
# ------------------------------- Helpers ------------------------------------#
###############################################################################

def ensure_collection(name: str):
    root = bpy.context.scene.collection
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if coll.name not in root.children:
        root.children.link(coll)
    return coll

def link_exclusive(obj, target_coll):
    for c in list(obj.users_collection):
        try:
            c.objects.unlink(obj)
        except RuntimeError:
            pass
    target_coll.objects.link(obj)

def max_existing_part_id():
    m = -1
    for o in bpy.data.objects:
        if "helios_part_id" in o:
            try:
                m = max(m, int(o["helios_part_id"]))
            except Exception:
                pass
    return m

def separate_faces_by_material_slots(obj, target_slots):
    """Split selected faces into a new object; return new object or None."""
    if not target_slots:
        return None
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = (f.material_index in target_slots)
    bm.to_mesh(me)
    bm.free()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    new_objs = [o for o in bpy.context.selected_objects if o.type == 'MESH' and o != obj]
    return new_objs[0] if new_objs else None

def is_leaf_material_name(name: str) -> bool:
    n = (name or "").lower()
    return any(k.lower() in n for k in LEAF_KEYWORDS)

###############################################################################
# ----------------------- Core label customization ---------------------------#
###############################################################################

def split_trees_into_wood_and_leaves(trees_coll_name="Trees"):
    """
    Fast, modifier-aware split:
    - Uses evaluated mesh (modifiers applied)
    - Creates per-object meshes ("Wood"/"Leaves" names for dedup)
    - Copies full world transform (works even with parents)
    - helios_part_id is the same for wood & leaves of a tree
    """
    trees = bpy.data.collections.get(trees_coll_name)
    if not trees:
        print(f"[WARN] No '{trees_coll_name}' collection found. Nothing to do.")
        return []

    coll_leaves = ensure_collection("Trees_Leaves")
    coll_wood   = ensure_collection("Trees_Wood")

    next_id = max_existing_part_id() + 1
    rows = []

    # Snapshot the list; removing objects won't affect our iteration
    candidates = [o for o in list(trees.objects) if o.type == 'MESH']
    total = len(candidates)
    print(f"[SPLIT-FAST] Found {total} tree mesh object(s) in '{trees_coll_name}'")
    print(f"[SPLIT-FAST] Leaf keywords: {LEAF_KEYWORDS}")

    depsgraph = bpy.context.evaluated_depsgraph_get()

    for idx, base in enumerate(candidates):
        base_name = base.name  # cache name BEFORE we remove it

        # evaluated mesh (modifiers applied)
        eval_obj = base.evaluated_get(depsgraph)
        me = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

        # instance id (helios_part_id)
        inst_id = int(base.get("helios_part_id", 0))
        if inst_id == 0:
            inst_id = next_id
            next_id += 1
            base["helios_part_id"] = inst_id

        # which material slots are leaves?
        leaf_slots = {i for i, slot in enumerate(base.material_slots)
                      if slot.material and is_leaf_material_name(slot.material.name)}
        
        # Debug: print material information
        print(f"[DEBUG] Tree '{base_name}' has {len(base.material_slots)} material slots:")
        for i, slot in enumerate(base.material_slots):
            mat_name = slot.material.name if slot.material else "None"
            is_leaf = i in leaf_slots
            print(f"  Slot {i}: '{mat_name}' -> {'LEAF' if is_leaf else 'WOOD'}")
        print(f"[DEBUG] Leaf slots: {leaf_slots}")

        verts = [v.co.copy() for v in me.vertices]
        leaves_faces, wood_faces = [], []
        for poly in me.polygons:
            (leaves_faces if poly.material_index in leaf_slots else wood_faces).append(list(poly.vertices))
        
        print(f"[DEBUG] Face distribution: {len(leaves_faces)} leaf faces, {len(wood_faces)} wood faces")

        def make_part(obj_name, faces, semantic, target_coll):
            if not faces:
                return None
            m = bpy.data.meshes.new(f"{base_name}_{obj_name}Mesh")
            m.from_pydata(verts, [], faces)
            m.update()
            obj = bpy.data.objects.new(obj_name, m)  # "Wood" or "Leaves" (dedup-friendly)
            # copy world transform (works with parents)
            obj.matrix_world = base.matrix_world.copy()
            if base.parent:
                obj.parent = base.parent
                obj.matrix_parent_inverse = base.matrix_parent_inverse.copy()
            obj["semantic"] = semantic
            obj["instance_id"] = inst_id
            obj["helios_part_id"] = inst_id
            target_coll.objects.link(obj)
            rows.append({
                "part_id": inst_id,
                "instance_id": inst_id,
                "semantic": semantic,
                "collection": target_coll.name,
                "object_name": obj.name.split('.')[0],
            })
            return obj

        wood_obj   = make_part("Wood",   wood_faces,   "wood",   coll_wood)
        leaves_obj = make_part("Leaves", leaves_faces, "leaves", coll_leaves)

        # print BEFORE removing base (to avoid StructRNA removal error)
        print(f"[SPLIT-FAST] Processed '{base_name}' ({idx+1}/{total}) → "
              f"{'Wood' if wood_obj else 'No Wood'}, {'Leaves' if leaves_obj else 'No Leaves'}")

        # clean up evaluated mesh and remove the source object
        eval_obj.to_mesh_clear()
        bpy.data.objects.remove(base, do_unlink=True)

    # optionally remove now-empty Trees collection
    try:
        bpy.data.collections.remove(trees)
        print(f"[SPLIT-FAST] Removed original '{trees_coll_name}' collection.")
    except Exception as e:
        print(f"[WARN] Could not remove '{trees_coll_name}': {e}")

    # default landscape id=0
    if (land := bpy.data.collections.get("Landscape")):
        for o in land.objects:
            if o.type == 'MESH' and "helios_part_id" not in o:
                o["helios_part_id"] = 0
                o["semantic"] = "landscape"

    print(f"[SPLIT-FAST] Done. Generated {len(rows)} labeled part(s)")
    return rows


###############################################################################
# --------------------------------- Main --------------------------------------#
###############################################################################

def main():
    # Load .blend if specified
    if blend_file and os.path.exists(blend_file):
        print(f"[LOAD] Opening blend file: {blend_file}")
        bpy.ops.wm.open_mainfile(filepath=blend_file)

    rows = split_trees_into_wood_and_leaves(trees_collection)

    # Determine save path
    orig_path = bpy.data.filepath
    if not orig_path:
        raise RuntimeError("No .blend file is currently loaded; cannot save.")

    base, ext = os.path.splitext(orig_path)
    labeled_path = base + "_leafwood" + ext

    # Write CSV
    if write_csv:
        csv_path = os.path.splitext(labeled_path)[0] + "_labels.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["part_id","instance_id","semantic","collection","object_name"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"[LABELS] Wrote {csv_path}")

    # Save labeled .blend
    bpy.ops.wm.save_as_mainfile(filepath=labeled_path)
    print(f"[SAVE] Saved labeled blend to: {labeled_path}")

if __name__ == "__main__":
    main()