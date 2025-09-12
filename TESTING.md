# Testing CAMP3D

> **Note**: This is a detailed testing guide. For quick start, see [README.md](README.md).

## Prerequisites

1. **Install the package**:
   ```bash
   pip install -e .
   ```

2. **Install the adapted Blender2Helios addon** (required):
   ```bash
   camp3d tools write-addon ~/.config/blender/4.2/scripts/addons/
   ```

3. **Check your environment**:
   ```bash
   camp3d doctor all
   ```

4. **Install example materials and scenes**:
   ```bash
   camp3d tools install-materials
   camp3d tools install-examples
   ```

## Required Dependencies

- **Blender 4.2+** (accessible via `blender` command)
- **pyhelios** (for HELIOS++ integration)
- **Blender2Helios addon** (installed via `u2h tools write-addon`)
- **Python packages**: pyyaml, typer, rich, pydantic, numpy, plyfile

## Running Tests

### 1. Unit Tests
```bash
python test_unreal2helios.py
```

### 2. Full Pipeline Test
```bash
# In Git Bash
bash test_pipeline.sh
```

### 3. Quick Test with quickdemo Example

1. **Test environment checks**:
   ```bash
   camp3d doctor all
   ```

2. **Test scene statistics** (if Blender is available):
   ```bash
   camp3d stats-blend --blend ./scene/quickdemo/quickdemo.blend
   ```

3. **Test scene creation** (if you have FBX files):
   ```bash
   camp3d create-blend --create-new-scene \
     --landscape-fbx ./scene/quickdemo/quickdemo_landscape.fbx \
     --trees-fbx ./scene/quickdemo/quickdemo_trees.fbx \
     --blend-path ./scene/quickdemo/quickdemo.blend
   ```

4. **Test full pipeline** (if Blender and HELIOS are properly configured):
   ```bash
   camp3d run -c examples/quickdemo_config.yaml
   ```

5. **Test post-processing** (if you have simulation output):
   ```bash
   camp3d postprocess-cmd --input-root ./helios/output/quickdemo --output-root ./ml_data
   ```

### 4. Advanced Test with Deciduous4 Example

For more comprehensive testing, you can use the Deciduous4 example (available separately):

1. **Download Deciduous4 example** from the GitHub repository
2. **Place in your project directory**:
   ```
   MyProject/
   ├─ scene/
   │  └─ Deciduous4/
   │     ├─ Deciduous4_landscape.fbx
   │     ├─ Deciduous4_trees.fbx
   │     └─ Deciduous4.blend
   └─ ...
   ```

3. **Run full pipeline**:
   ```bash
   camp3d run -c examples/deciduous4_config.yaml
   ```

## Expected Results

- Unit tests should pass without errors
- Environment checks should show all components as available
- Scene statistics should display information about the test scene
- Full pipeline should process the example data through all stages

## Troubleshooting

- If Blender is not found, ensure it's in your PATH or set `BLENDER_BIN` environment variable
- If pyhelios import fails, ensure the helios conda environment is activated
- If materials are missing, run `camp3d tools install-materials` first
- If example scenes are missing, run `camp3d tools install-examples` first

## Example Scenes

### quickdemo
- **Purpose**: Quick testing and validation
- **Size**: Minimal (single tree)
- **Installation**: `camp3d tools install-examples`
- **Use case**: Development, debugging, quick validation

### Deciduous4
- **Purpose**: Full pipeline demonstration
- **Size**: Complete forest scene
- **Source**: Quixel assets from Unreal Marketplace
- **Installation**: Download separately from GitHub repository
- **Use case**: Complete workflow demonstration, research validation

## Performance Notes

- **quickdemo**: Fast processing (~1-2 minutes for full pipeline)
- **Deciduous4**: Longer processing (~10-30 minutes depending on hardware)
- **Memory usage**: Deciduous4 requires more RAM for post-processing
