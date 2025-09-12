#!/bin/bash

echo "=== CAMP3D Pipeline Test Runner ==="
echo

# Install the package
echo "Step 1: Installing CAMP3D package..."
pip install -e .

# Install the Blender2Helios addon
echo "Step 2: Installing Blender2Helios addon..."
camp3d tools write-addon ~/.config/blender/4.2/scripts/addons/

# Install example materials and scenes
echo "Step 3: Installing example materials and scenes..."
camp3d tools install-materials
camp3d tools install-examples

# Run unit tests
echo "Step 4: Running unit tests..."
python test_camp3d.py

# Test CLI
echo "Step 5: Testing CLI availability..."
camp3d --help

# Run doctor
echo "Step 6: Running environment checks..."
camp3d doctor all

# Test scene stats (only if Blender is working)
echo "Step 7: Testing scene statistics..."
if command -v blender &> /dev/null; then
    camp3d stats-blend --blend ./scene/quickdemo/quickdemo.blend
else
    echo "Blender not found, skipping scene statistics test"
fi

# Test creating a new blend file from FBX
echo "Step 8: Testing scene creation from FBX..."
if command -v blender &> /dev/null; then
    echo "Creating blend file from FBX exports..."
    camp3d create-blend --create-new-scene \
        --landscape-fbx ./scene/quickdemo/quickdemo_landscape.fbx \
        --trees-fbx ./scene/quickdemo/quickdemo_trees.fbx \
        --blend-path ./scene/quickdemo/quickdemo_test.blend
else
    echo "Blender not found, skipping scene creation test"
fi

# Test post-processing (if simulation output exists)
echo "Step 9: Testing post-processing..."
if [ -d "./helios/output" ]; then
    echo "Found simulation output, testing post-processing..."
    camp3d postprocess-cmd --input-root ./helios/output --output-root ./ml_data_test --tile-size 50.0
else
    echo "No simulation output found, skipping post-processing test"
fi

echo
echo "=== All tests completed ==="
