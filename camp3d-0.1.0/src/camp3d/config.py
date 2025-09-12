
from __future__ import annotations
from typing import Any, Dict, Optional, List
import os, yaml
from pydantic import BaseModel, Field

class BlenderCfg(BaseModel):
    bin: str = Field(default=os.environ.get("BLENDER_BIN", "blender"))

class U2HCfg(BaseModel):
    materials_dir: str = "./materials"  # where materials/ lives in the project

class HeliosCfg(BaseModel):
    output_dir: Optional[str] = Field(default=None, description="Output directory for HELIOS simulation data and results. Defaults to ./helios/")
    
    def get_output_dir(self) -> str:
        """Get HELIOS output directory, defaulting to ./helios/ if not set."""
        if self.output_dir:
            return self.output_dir
        return "./helios"

class SceneSemanticsCfg(BaseModel):
    trees_collection: Optional[str] = "Trees"
    leaf_keywords: List[str] = []
    write_csv: bool = False

class TilingCfg(BaseModel):
    enabled: bool = False
    nx: int = 2
    ny: int = 2

class SceneCfg(BaseModel):
    name: Optional[str] = None
    blend: Optional[str] = None
    scene_dir: str = "./scene"  # directory for Unreal exports and blend files
    semantics: SceneSemanticsCfg = SceneSemanticsCfg()
    tiling: TilingCfg = TilingCfg()

class ExportCfg(BaseModel):
    use_own_materials: bool = True
    materials_name: Optional[str] = None
    save_scene_bbox: bool = True
    save_survey_file: bool = False

class PlanningCfg(BaseModel):
    rotate_deg: float = 0.0
    survey_mode: str = "ULS"
    spacing: float = 20.0
    relative_altitude: float = 60.0
    speed: float = 5.0
    pulse_freq_hz: int = 200000
    pattern: str = "criss-cross"

class SurveyCfg(BaseModel):
    file: Optional[str] = None
    callback_frequency: int = 10000
    output_dir: Optional[str] = None

class PostprocessCfg(BaseModel):
    input_root: Optional[str] = None
    output_root: Optional[str] = None
    tile_size: float = 50.0
    merge_all_ts: bool = False
    ground_label: int = 2
    wood_label: int = 3 # semantic id for wood / tree
    leaf_label: int = 4 # semantic id for leaves
    leafwood: bool = False  # default: ./output/<SceneName>

class Config(BaseModel):
    blender: BlenderCfg = BlenderCfg()
    u2h: U2HCfg = U2HCfg()
    helios: HeliosCfg = HeliosCfg()
    unreal: Dict[str, Any] = {}
    scene: SceneCfg = SceneCfg()
    export: ExportCfg = ExportCfg()
    planning: PlanningCfg = PlanningCfg()
    survey: SurveyCfg = SurveyCfg()
    postprocess: PostprocessCfg = PostprocessCfg()

def load(path: Optional[str]) -> Config:
    if path is None:
        return Config()
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return Config.model_validate(data)
