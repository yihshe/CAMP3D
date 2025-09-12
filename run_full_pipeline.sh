#!/bin/bash

echo "=== CAMP3D Full Pipeline Runner ==="
echo "This script runs the complete pipeline from Unreal exports to ML-ready data"
echo

# Configuration
SCENE_NAME="quickdemo"
LANDSCAPE_FBX="./scene/quickdemo/quickdemo_landscape.fbx"
TREES_FBX="./scene/quickdemo/quickdemo_trees.fbx"
BLEND_FILE="./scene/quickdemo/quickdemo.blend"
MATERIALS_DIR="./materials"
OUTPUT_DIR="./helios"
ML_OUTPUT_DIR="./ml_data"
CONFIG_FILE="examples/quickdemo_config.yaml"

# Step 1: Install package and dependencies
echo "Step 1: Installing package and dependencies..."
pip install -e .
camp3d tools write-addon ~/.config/blender/4.2/scripts/addons/
camp3d tools install-materials --materials-dir $MATERIALS_DIR
camp3d tools install-examples --scene-dir ./scene

# Step 2: Check environment
echo "Step 2: Checking environment..."
camp3d doctor all

# Step 3: Create Blender scene from FBX exports
echo "Step 3: Creating Blender scene from FBX exports..."
if [ -f "$LANDSCAPE_FBX" ] && [ -f "$TREES_FBX" ]; then
    camp3d create-blend --create-new-scene \
        --landscape-fbx "$LANDSCAPE_FBX" \
        --trees-fbx "$TREES_FBX" \
        --blend-path "$BLEND_FILE"
    echo "✓ Blender scene created: $BLEND_FILE"
else
    echo "⚠ FBX files not found, skipping scene creation"
    echo "  Expected: $LANDSCAPE_FBX"
    echo "  Expected: $TREES_FBX"
fi

# Step 4: Add semantic labeling (optional)
echo "Step 4: Adding semantic labeling..."
if [ -f "$BLEND_FILE" ]; then
    camp3d semantics-blend --blend "$BLEND_FILE" \
        --trees-collection Trees \
        --leaf-keywords "Leaves,Needles,MTL_RW_Needles,MI_birch_branch,MI_pine_branch,MI_Leaves,leaf,MI_Pine_Tree_Needles,MI_Scots_Pine_Sheet_Sick,MI_Scots_Pine_Sheet,MI_Pine_Mountain_Ash_Sheet,TwoSided" \
        --write-csv
    echo "✓ Semantic labeling completed"
else
    echo "⚠ Blender file not found, skipping semantic labeling"
fi

# Step 5: Export to HELIOS++
echo "Step 5: Exporting to HELIOS++ format..."
if [ -f "$BLEND_FILE" ]; then
    camp3d export-helios \
        --blend "$BLEND_FILE" \
        --materials-dir "$MATERIALS_DIR" \
        --output-dir "$OUTPUT_DIR" \
        --scene-name "$SCENE_NAME" \
        --use-own-materials \
        --materials-name spread_leafwood \
        --save-scene-bbox \
        --save-survey-file
    echo "✓ HELIOS++ export completed"
else
    echo "⚠ Blender file not found, skipping HELIOS++ export"
fi

# Step 6: Plan UAV survey
echo "Step 6: Planning UAV survey..."
camp3d plan-path \
    --scene-name "$SCENE_NAME" \
    --survey-mode ULS \
    --spacing 20.0 \
    --rotate-deg 0 \
    --relative-altitude 60.0 \
    --speed 5.0 \
    --pulse-freq-hz 200000 \
    --pattern criss-cross
echo "✓ UAV survey planned"

# Step 7: Run LiDAR simulation
echo "Step 7: Running LiDAR simulation..."
SURVEY_FILE="$OUTPUT_DIR/data/$SCENE_NAME/surveys/${SCENE_NAME}_ULS.xml"
if [ -f "$SURVEY_FILE" ]; then
    camp3d survey-run \
        --survey-file "$SURVEY_FILE" \
        --output-dir "$OUTPUT_DIR/output/"
    echo "✓ LiDAR simulation completed"
else
    echo "⚠ Survey file not found, skipping simulation"
    echo "  Expected: $SURVEY_FILE"
fi

# Step 8: Post-process for ML
echo "Step 8: Post-processing for machine learning..."
SIMULATION_OUTPUT="$OUTPUT_DIR/output/$SCENE_NAME"
if [ -d "$SIMULATION_OUTPUT" ]; then
    camp3d postprocess-cmd \
        --input-root "$SIMULATION_OUTPUT" \
        --output-root "$ML_OUTPUT_DIR" \
        --tile-size 50.0 \
        --leafwood
    echo "✓ ML post-processing completed"
    echo "  Output: $ML_OUTPUT_DIR"
else
    echo "⚠ Simulation output not found, skipping post-processing"
    echo "  Expected: $SIMULATION_OUTPUT"
fi

# Alternative: Run full pipeline with config file
echo
echo "Alternative: Run full pipeline with config file..."
if [ -f "$CONFIG_FILE" ]; then
    echo "Running: camp3d run -c $CONFIG_FILE"
    camp3d run -c "$CONFIG_FILE"
    echo "✓ Full pipeline completed with config file"
else
    echo "⚠ Config file not found: $CONFIG_FILE"
fi

echo
echo "=== Pipeline completed ==="
echo "Check the following outputs:"
echo "  - Blender scene: $BLEND_FILE"
echo "  - HELIOS data: $OUTPUT_DIR/data/"
echo "  - Simulation output: $OUTPUT_DIR/output/"
echo "  - ML-ready data: $ML_OUTPUT_DIR"
