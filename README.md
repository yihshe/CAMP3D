# Cambridge Arboreal Modelling Panoptic 3D (CAMP3D)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Blender 4.2](https://img.shields.io/badge/blender-4.2-orange.svg)](https://www.blender.org/)

**Pipeline and Dataset From Paper: *Scaling Up Forest Vision with Synthetic Data* (She et al., 2025)**

A reproducible pipeline to go from **Unreal Engine exports → Blender (4.2) → HELIOS++ LiDAR simulation → ML-ready point clouds**, including optional **leaf/wood semantics**, UAV flight planning, survey execution, and post-processing for machine learning.

- **Python package**: `camp3d`
- **CLI entry point**: `camp3d`
- **Dataset**: [Download here](https://github.com/yihshe/CAMP3D/releases) (coming soon - synthetic forest point clouds with semantic labels)
- **Citation**: See [Citation](#citation) section below

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
- [Quick Start](#quick-start)
- [Example Scenes](#example-scenes)
- [Command Reference](#command-reference)
- [Materials](#materials-using-ours-or-your-own)
- [Post-processing for Machine Learning](#post-processing-for-machine-learning)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [Testing](#testing)
- [Citation](#citation)
- [License](#license)

## Features

- **Scene Creation**: Convert Unreal Engine FBX exports to Blender scenes
- **Semantic Labeling**: Automatic tree/leaf/ground classification with customizable keywords
- **HELIOS Integration**: Export scenes to HELIOS++ format for LiDAR simulation
- **UAV Planning**: Generate survey flight paths with configurable parameters
- **LiDAR Simulation**: Run HELIOS++ surveys to generate point cloud data
- **ML Post-processing**: Convert simulation output to ML-ready PLY format with tiling
- **Environment Management**: Built-in dependency checking and setup validation

## Prerequisites

Before installing CAMP3D, ensure you have:

- **Python 3.8+** installed
- **Blender 4.2** installed and accessible from command line
- **HELIOS++** installed (see [HELIOS++ installation guide](https://github.com/3dgeo-heidelberg/helios))
- **pyhelios** Python package installed (`pip install pyhelios`)

### Required Dependencies

CAMP3D requires several external dependencies that must be installed separately:

1. **HELIOS++ LiDAR Simulator**: 
   - Download from: https://github.com/3dgeo-heidelberg/helios
   - Follow the installation guide for your operating system
   - Ensure the `helios` executable is in your PATH

2. **pyhelios Python Package**:
   ```bash
   pip install pyhelios
   ```
   - This provides Python bindings for HELIOS++
   - Required for survey planning and execution

3. **Blender 4.2**:
   - Download from: https://www.blender.org/download/
   - Ensure `blender` command is accessible from terminal
   - Required for 3D scene processing and export

**Note**: These dependencies are not automatically installed with CAMP3D and must be set up manually before use.

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/yihshe/CAMP3D.git
cd CAMP3D

# Install in development mode
pip install -e ./camp3d-0.1.0
```

### Option 2: Install from PyPI (when available)

```bash
pip install camp3d
```

## Setup

After installation, set up the required components:

```bash
# Install Blender addon (automatic)
camp3d tools write-addon ~/.config/blender/4.2/scripts/addons/

# Or install manually if automatic installation fails:
# 1. Copy examples/addons/Blender2Helios.py to your Blender addons directory
# 2. Enable it in Blender: Edit → Preferences → Add-ons → search 'Blender2Helios'

# Install example materials and scenes
camp3d tools install-materials
camp3d tools install-examples
```

## Quick Start

### 1. Test Your Setup

```bash
# Check if everything is installed correctly
camp3d doctor all
```

### 2. Run the Quick Demo

The quick demo contains a single tree extracted from the original Deciduous4 scene for fast testing:

```bash
# Run the complete pipeline
camp3d run -c camp3d-0.1.0/examples/quickdemo_config.yaml
```

This will:
1. **Create** a Blender scene from FBX files
2. **Add** semantic labels (leaf/wood classification)
3. **Export** to HELIOS++ format
4. **Plan** UAV survey flight path
5. **Simulate** LiDAR scanning
6. **Post-process** results to ML-ready format

> **Expected Output**: A point cloud dataset obtained by virtual UAV laser scans, semantically labeled with ground/wood/leaf classifications and instance labels, ready for machine learning tasks.

### 3. View Results

After completion, you'll find:
- **Blender scene**: `./scene/quickdemo/quickdemo.blend`
- **HELIOS data**: `./helios/data/quickdemo/`
- **Point clouds**: `./ml_data/quickdemo/`

## Example Scenes

### quickdemo (Quick Test)
- **Purpose**: Fast validation and testing
- **Size**: Minimal (single tree from Deciduous4 scene)
- **Installation**: `camp3d tools install-examples`
- **Processing time**: ~1-2 minutes

### Deciduous4 (Full Demo)
- **Purpose**: Complete pipeline demonstration
- **Size**: Full forest scene with procedural foliage
- **Source**: Quixel assets from Unreal Marketplace
- **Installation**: Download separately from GitHub repository
- **Processing time**: ~40-60 minutes

> **Note**: A detailed documentation on Unreal Engine procedural foliage generation and scene export will be provided later. For now, we provide exported scene files from Unreal Engine as examples.

## Command Reference

### Environment & Setup
```bash
# Check if everything is installed correctly
camp3d doctor all

# Install Blender2Helios addon (or install manually - see "Setup" section)
camp3d tools write-addon ~/.config/blender/4.2/scripts/addons/

# Install example materials
camp3d tools install-materials

# Install example scenes
camp3d tools install-examples
```

### Scene Creation
```bash
# Create blend file from Unreal FBX exports
camp3d create-blend --create-new-scene \
  --landscape-fbx ./scene/quickdemo/quickdemo_landscape.fbx \
  --trees-fbx ./scene/quickdemo/quickdemo_trees.fbx \
  --blend-path ./scene/quickdemo/quickdemo.blend

# Get scene statistics
camp3d stats-blend --blend ./scene/quickdemo/quickdemo.blend
```

### Semantic Labeling
```bash
# Add leaf/wood semantics to trees
camp3d semantics-blend \
  --blend ./scene/quickdemo/quickdemo.blend \
  --trees-collection Trees \
  --leaf-keywords "Leaves,Needles,MTL_RW_Needles,MI_birch_branch,MI_pine_branch,MI_Leaves,leaf,MI_Pine_Tree_Needles,MI_Scots_Pine_Sheet_Sick,MI_Scots_Pine_Sheet,MI_Pine_Mountain_Ash_Sheet,TwoSided" \
  --write-csv
```

### HELIOS++ Export
```bash
# Export scene for HELIOS++ simulation
camp3d export-helios \
  --blend ./scene/quickdemo/quickdemo_leafwood.blend \
  --materials-dir ./materials \
  --output-dir ./helios \
  --scene-name quickdemo \
  --use-own-materials \
  --materials-name spread_leafwood \
  --save-scene-bbox \
  --save-survey-file
```

### UAV Path Planning
```bash
# Plan survey flight path
camp3d plan-path \
  --scene-name quickdemo \
  --survey-mode ULS \
  --spacing 20 \
  --rotate-deg 0 \
  --relative-altitude 60 \
  --speed 5 \
  --pulse-freq-hz 200000 \
  --pattern criss-cross
```

### LiDAR Simulation
```bash
# Run HELIOS++ simulation
camp3d survey-run \
  --survey-file ./helios/data/quickdemo/surveys/quickdemo_ULS.xml \
  --output-dir ./helios/output/
```

### ML Post-processing
```bash
# Convert simulation output to ML-ready format. Process the last timestamp directory by default
camp3d postprocess-ml \
  --input-root ./helios/output/quickdemo_ULS \
  --output-root ./ml_data \
  --tile-size 50.0 \
  --leafwood

# Process specific timestamp directory
camp3d postprocess-ml \
  --input-root ./helios/output/quickdemo_ULS/2025-09-11_20-35-12 \
  --output-root ./ml_data \
  --leafwood

# Merge all timestamps
camp3d postprocess-ml \
  --input-root ./helios/output/quickdemo_ULS \
  --output-root ./ml_data \
  --leafwood \
  --merge-all-ts 
```

### Full Pipeline
```bash
# Run complete pipeline with config file
camp3d run -c camp3d-0.1.0/examples/quickdemo_config.yaml

# Run with custom parameters
camp3d run \
  --blend ./scene/quickdemo/quickdemo.blend \
  --materials-dir ./materials \
  --output-dir ./helios \
  --scene-name quickdemo \
  --skip-semantics
```

## Materials: Using Ours or Your Own

- **Where:** put `.mtl` files under your project **`materials/`**.
- **How to reference:** use `--materials-name <basename>` (no `.mtl`), e.g. `spread_leafwood`.

You can add any number of `.mtl` files here. The important keys are:
- `helios_classification` (integer label),
- `helios_isGround` (0/1),
- `newmtl <CollectionName>` (e.g., `Landscape`, `Trees`, `Trees_Wood`, `Trees_Leaves`).

The export script copies `materials/<name>.mtl` to HELIOS: `helios/data/<Scene>/sceneparts/materials.mtl`.

## Post-processing for Machine Learning

The `camp3d postprocess-ml` command converts HELIOS simulation output into ML-ready format:

### **Features:**
- **Format conversion**: Converts `.xyz` point cloud files to `.ply` format
- **Tiling**: Splits large scenes into manageable tiles (default: 50m × 50m)
- **Semantic labels**: Preserves ground/vegetation classifications
- **Tree ID tracking**: Maintains individual tree identifiers for segmentation tasks
- **Flexible labeling**: Supports both simplified (ground/vegetation) and detailed (ground/wood/leaf) modes

### **Usage:**
```bash
# Basic post-processing (uses latest timestamp if multiple exist)
camp3d postprocess-ml --input-root ./helios/output/quickdemo_ULS --output-root ./ml_data

# Or specify the directory which contains the XYZ files to process
camp3d postprocess-ml --input-root ./helios/output/quickdemo_ULS/2025-09-11_20-35-12 \
                --output-root ./ml_data 

# Merge all timestamps into single scene
camp3d postprocess-ml --input-root ./helios/output/quickdemo_ULS \
                --output-root ./ml_data \
                --merge-all-ts

# Advanced options with leafwood mode (used when the scene file has been converted into leaf wood semantics)
camp3d postprocess-ml --input-root ./helios/output/quickdemo_ULS \
                --output-root ./ml_data \
                --tile-size 50.0 \
                --leafwood
```

### **Output Structure:**
```
ml_data/
└─ quickdemo/
    └─2025-09-11_20-35-12/       # Single timestamp or latest timestamp
      ├─ quickdemo_plot_0_annotated.ply
      ├─ quickdemo_plot_1_annotated.ply
      └─ ...
```

Each `.ply` file contains:
- **x, y, z**: 3D coordinates
- **intensity**: LiDAR return intensity
- **semantic_seg**: Ground (1) or vegetation (2), or detailed labels (2/3/4)
- **treeID**: Individual tree identifier (-1 for ground points)

## Configuration

The pipeline uses YAML configuration files. See `examples/quickdemo_config.yaml` for a complete example:

```yaml
camp3d:
  materials_dir: ./materials

helios:
  output_dir: ./helios

scene:
  name: quickdemo
  scene_dir: ./scene
  blend: ./scene/quickdemo/quickdemo.blend
  semantics:
    trees_collection: Trees
    leaf_keywords: ["Leaves", "MTL_RW_Needles", "MI_birch_branch", "MI_pine_branch", "MI_Leaves", "leaf", "MI_Pine_Tree_Needles", "MI_Scots_Pine_Sheet_Sick", "MI_Scots_Pine_Sheet", "MI_Pine_Mountain_Ash_Sheet", "TwoSided"]
    write_csv: false

export:
  use_own_materials: true
  materials_name: spread_leafwood
  save_scene_bbox: true
  save_survey_file: true

planning:
  rotate_deg: 0
  survey_mode: ULS
  spacing: 20.0
  relative_altitude: 60.0
  speed: 5.0
  pulse_freq_hz: 200000
  pattern: criss-cross

survey:
  callback_frequency: 10000
  output_dir: ./helios/output

postprocess:
  tile_size: 50.0
  merge_all_ts: false
  ground_label: 2
  wood_label: 3
  leaf_label: 4
  leafwood: true
```

## Contributing

We welcome contributions to CAMP3D! Here are some ways you can contribute:

### 1. Adding Your Own Scenes

You can contribute by adding your own forest scenes generated using Unreal Engine's procedural foliage system:

1. **Export from Unreal Engine**:
   - Split foliage into individual trees
   - Export trees to FBX file with `_trees` suffix
   - Export landscape to FBX file with `_landscape` suffix
   - **Important**: Don't select LOD (Level of Details) when exporting

2. **Create scene folder**:
   - Create a folder under `scene/` to store your files
   - Place both FBX files in this folder

3. **Customize leaf keywords** (if needed):
   - CAMP3D automatically detects leaf materials using keywords in material names
   - Default keywords include: `Leaves`, `MTL_RW_Needles`, `MI_birch_branch`, `MI_pine_branch`, `MI_Leaves`, `leaf`, `MI_Pine_Tree_Needles`, `MI_Scots_Pine_Sheet_Sick`, `MI_Scots_Pine_Sheet`, `MI_Pine_Mountain_Ash_Sheet`, `TwoSided`
   - If your materials use different naming conventions, update the `leaf_keywords` in your config file:
     ```yaml
     scene:
       semantics:
         leaf_keywords: ["YourLeafKeyword1", "YourLeafKeyword2", ...]
     ```

4. **Test your scene**:
   - Run `camp3d run -c your_config.yaml` to test your scene
   - Share your results and any issues you encounter

> **Note**: A detailed tutorial on Unreal Engine procedural foliage generation and scene export will be added later.

### 2. Expanding Survey Modes

Currently, CAMP3D supports UAV laser scanning (ULS). You can contribute by expanding to other survey modes:

- **MLS** (Mobile Laser Scanning)
- **TLS** (Terrestrial Laser Scanning) 
- **ALS** (Airborne Laser Scanning)

These modes are supported by the HELIOS simulator, but the path planning and survey file generation would need to be developed in this package.

### 3. Other Contributions

- Bug fixes and improvements
- Documentation improvements
- Additional post-processing features
- Integration with other LiDAR simulation tools

## Testing

For detailed testing instructions, see [TESTING.md](TESTING.md).

### Quick Test

1. **Install and setup**:
   ```bash
   pip install -e .
   camp3d tools write-addon ~/.config/blender/4.2/scripts/addons/  # or install manually
   camp3d tools install-materials
   camp3d tools install-examples
   ```

2. **Run tests**:
   ```bash
   # Check environment
   camp3d doctor all
   
   # Unit tests
   python test_camp3d.py
   
   # Quick pipeline test
   camp3d run -c camp3d-0.1.0/examples/quickdemo_config.yaml
   ```

3. **Full pipeline test**:
   ```bash
   bash test_pipeline.sh
   ```

## Blender Addon Script: `Blender2Helios.py` (adapted) 

Base project: https://github.com/neumicha/Blender2Helios  (GPLv3)

Differences vs upstream:
1. Uses per-object `helios_part_id` for `<part id="...">` in the scene XML.
2. Emits **relative** OBJ paths under `data/<scene>/sceneparts`.
3. Survey generation is decoupled (we build UAV-LS surveys via `plan_path`).
4. Uses `wm.obj_export` with modifiers; materials via `materials.mtl` when `useOwnMaterials=True`.
5. Guarded directory creation inside HELIOS base dir.

## Notes & Tips

- Blender target: **4.2**. Decimation (optional): UI → *Decimate* modifier on tree meshes.
- Unreal export: two FBX per scene (`*_landscape.fbx` and `*_trees.fbx`), with trees **separated per object**.
- Export writes into `<output_dir>/data/<SceneName>/...`.
- `survey-run` defaults outputs to `<output_dir>/output/<SceneName>`; override with `--output-dir`.

## Citation

If you find CAMP3D useful in your research, please consider to cite our paper:

```bibtex
@article{she2024scaling,
  title={Scaling Up Forest Vision with Synthetic Data},
  author={She, Yihang and others},
  journal={arXiv preprint arXiv:XXXX.XXXXX},
  year={2024}
}
```

## License

- **Python package**: MIT License
- **Example adapted Blender2Helios add-on**: GPLv3 (inherits upstream's license)