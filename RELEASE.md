# Releasing CAMP3D to PyPI

## Prerequisites

1. **Install build tools**:
   ```bash
   pip install build twine
   ```

2. **Update version** in `pyproject.toml`:
   ```toml
   [project]
   version = "0.1.0"  # Update this version number
   ```

3. **Ensure all tests pass**:
   ```bash
   python test_unreal2helios.py
   bash test_pipeline.sh
   ```

## Release Process

### 1. Clean and Build
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build
```

### 2. Test Upload (Optional)
```bash
# Upload to TestPyPI first (recommended)
python -m twine upload --repository testpypi dist/*
```

Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ unreal2helios
```

### 3. Upload to PyPI
```bash
# Upload to PyPI
python -m twine upload dist/*
```

### 4. Verify Installation
```bash
# Install from PyPI
pip install camp3d

# Test the installation
camp3d --help
camp3d doctor all
camp3d tools install-examples
```

## Package Structure

The package includes:
- **Source code**: `src/camp3d/`
- **CLI entry point**: `camp3d`
- **Example files**: `examples/` (materials, addons, config, quickdemo scene)
- **Test files**: `test_camp3d.py`, `test_pipeline.sh`, `run_full_pipeline.sh`
- **Documentation**: `README.md`, `TESTING.md`

## Dependencies

The package automatically installs:
- `pyyaml`
- `typer`
- `rich`
- `pydantic`
- `numpy`
- `plyfile`

## User Installation

After release, users can install with:
```bash
pip install camp3d
```

Then follow the setup in README.md:
1. `camp3d tools write-addon ~/.config/blender/4.2/scripts/addons/`
2. `camp3d tools install-materials`
3. `camp3d tools install-examples`
4. `camp3d doctor all`

## Example Scenes

### quickdemo (Included)
- **Purpose**: Quick testing and validation
- **Installation**: `camp3d tools install-examples`
- **Use case**: Development, debugging, quick validation

### Deciduous4 (Separate)
- **Purpose**: Full pipeline demonstration
- **Source**: Quixel assets from Unreal Marketplace
- **Installation**: Download separately from GitHub repository
- **Use case**: Complete workflow demonstration, research validation

## Version Management

- **Patch version** (0.1.x): Bug fixes
- **Minor version** (0.x.0): New features, backward compatible
- **Major version** (x.0.0): Breaking changes

## Notes

- The package uses `pyproject.toml` for modern Python packaging
- All dependencies are specified in `pyproject.toml`
- The package includes example files, quickdemo scene, and documentation
- Users need to manually install Blender2Helios addon and HELIOS++ separately
- Deciduous4 example will be available separately on GitHub
