# QuickDemo Example

This is a minimal example scene for quick testing of the CAMP3D pipeline. It contains a single tree extracted from the original Deciduous4 scene.

## Files

- `quickdemo.blend` - Blender scene file with a single tree
- `quickdemo_landscape.fbx` - Landscape FBX export from Unreal Engine
- `quickdemo_trees.fbx` - Trees FBX export from Unreal Engine

## Usage

This example is automatically installed when you run:
```bash
camp3d tools install-examples
```

## Quick Test

After installation, you can run a quick test:
```bash
# Check environment
camp3d doctor all

# Test scene statistics
camp3d stats-blend --blend ./scene/quickdemo/quickdemo.blend

# Run full pipeline
camp3d run -c examples/quickdemo_config.yaml
```
