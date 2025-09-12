# Export the scene from Blender to Helios using Blender2Helios addon
import sys
import os
import bpy
import shutil
from mathutils import Vector
# import pdb;pdb.set_trace()

argv = sys.argv
if "--" in argv:
    # Get all args after "--"
    argv = argv[argv.index("--") + 1:]  # get all args after "--"
else:
    # No args after "--", so we can use the default values
    argv = []

# Parse the arguments
def get_arg_value(arg_name, default_value=None):
    try:
        index = argv.index(arg_name)
        return argv[index + 1]
    except (ValueError, IndexError):
        return default_value
    
# Read the bounding box from the scene
def save_bbox(obj_name, output_file):
    # Get the object by name
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"Object '{obj_name}' not found.")
        return

    # Obtain the object's bounding box (8 points in local space)
    local_bbox = [Vector(corner) for corner in obj.bound_box]

    # Convert local bbox coordinates to world coordinates
    world_bbox = [obj.matrix_world @ p for p in local_bbox]

    # Compute min and max for x, y, and z
    minx = min(p.x for p in world_bbox)
    maxx = max(p.x for p in world_bbox)
    miny = min(p.y for p in world_bbox)
    maxy = max(p.y for p in world_bbox)
    minz = min(p.z for p in world_bbox)
    maxz = max(p.z for p in world_bbox)

    # Print coordinates for inspection
    print("Bounding box in world coordinates:")
    print(f"X: {minx:.2f} to {maxx:.2f}")
    print(f"Y: {miny:.2f} to {maxy:.2f}")
    print(f"Z: {minz:.2f} to {maxz:.2f}")

    # Save the 2D bounding box (for flight planning, we use only x and y)
    bbox_2d = f"{minx} {miny} {maxx} {maxy}\n"
    # Save the Z range as well (if needed later)
    z_range = f"{minz} {maxz}\n"

    # Check if the output directory exists, if not create it
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, "w") as f:
        f.write(bbox_2d)
        f.write(z_range)
    print(f"Saved bounding box to: {output_file}")


def export_materials_file(src_file, dest_file):
    # Check if the source file exists
    if not os.path.exists(src_file):
        print(f"Source materials file '{src_file}' does not exist.")
        return

    # Check if the destination directory exists, if not create it
    dest_dir = os.path.dirname(dest_file)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Copy the file
    shutil.copy2(src_file, dest_file)
    print(f"Copied materials file from '{src_file}' to '{dest_file}'.")


# Get the arguments
materials_dir = os.path.normpath(get_arg_value("--materials_dir", "./materials"))
output_dir = os.path.normpath(get_arg_value("--output_dir", "./helios"))
scene_name = get_arg_value("--scene_name", "blender2heliosScene")
use_own_materials = get_arg_value("--use_own_materials", "True")
materials_name = get_arg_value("--materials_name", "example")
save_scene_bbox = get_arg_value("--save_scene_bbox", "True")
save_survey_file = get_arg_value("--write_survey_file", "False")

# Set the variables in the addon preferences
addon_prefs = bpy.context.preferences.addons["Blender2Helios"].preferences
addon_prefs.pref_heliosBaseDir = output_dir
addon_prefs.pref_sceneName = scene_name
addon_prefs.pref_useOwnMaterials = use_own_materials.lower() == "true"
addon_prefs.pref_alsoWriteSurveyFile = save_survey_file.lower() == "true"

# Create necessary directories before calling the addon
scenes_dir = os.path.join(output_dir, "data", scene_name, "scenes")
sceneparts_dir = os.path.join(output_dir, "data", scene_name, "sceneparts")
surveys_dir = os.path.join(output_dir, "data", scene_name, "surveys")

for dir_path in [scenes_dir, sceneparts_dir, surveys_dir]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

# Find a mesh in the scene and set it as the active object
# This is necessary for the export operator to work correctly
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
if mesh_objs:
    bpy.context.view_layer.objects.active = mesh_objs[0]

# Run the export operator while showing the progress bar
bpy.ops.scene.blender2helios()

# Export the materials file if needed
if use_own_materials.lower() == "true":
    # Export the materials file
    src_file = os.path.join(materials_dir, f"{materials_name}.mtl")
    dest_file = os.path.join(output_dir, "data", scene_name, "sceneparts", "materials.mtl")
    export_materials_file(src_file, dest_file)

if save_scene_bbox.lower() == "true":
    # Save the bounding box of the scene TODO customize to avoid hardcoding the name
    save_bbox("Landscape", os.path.join(output_dir, "data", scene_name, "surveys", f"scene_bbox.txt"))

print("Export finished for scene: ", scene_name)