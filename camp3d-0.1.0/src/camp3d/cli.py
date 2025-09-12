
from typing import Optional, List
import typer
from . import config as cfg
from .stages import create, semantics, tiling, export, plan, survey, stats, doctor, postprocess
from . import tools as tools

app = typer.Typer(
    name="camp3d",
    add_completion=False, 
    no_args_is_help=True,
    help="CAMP3D: Cambridge Arboreal Modelling - Panoptic 3D pipeline"
)
app.add_typer(doctor.app, name="doctor", help="Environment checks")
app.add_typer(tools.app, name="tools", help="Utilities: materials, addon")

@app.command()
def run(config: Optional[str] = typer.Option(None, "--config", "-c"),
        skip_create: bool = False,
        skip_semantics: bool = False,
        skip_tiling: bool = True,
        skip_export: bool = False,
        skip_plan: bool = False,
        skip_survey: bool = False):
    conf = cfg.load(config)
    from .pipeline import run as run_pipeline
    run_pipeline(conf, skip_create, skip_semantics, skip_tiling, skip_export, skip_plan, skip_survey)

@app.command()
def create_blend(config: Optional[str] = typer.Option(None, "--config", "-c"),
                 batch_dir: Optional[str] = None,
                 batch_overwrite: bool = False,
                 create_new_scene: bool = False,
                 landscape_fbx: Optional[str] = None,
                 trees_fbx: Optional[str] = None,
                 objects_fbx: Optional[str] = None,
                 blend_path: Optional[str] = None,
                 tree_keywords: Optional[List[str]] = typer.Option(None, help="Keywords to detect tree meshes in *_objects.fbx*")):
    conf = cfg.load(config)
    create.run(conf, batch_dir=batch_dir, batch_overwrite=batch_overwrite,
               create_new_scene=create_new_scene, landscape_fbx=landscape_fbx,
               trees_fbx=trees_fbx, objects_fbx=objects_fbx, blend_path=blend_path,
               tree_keywords=tree_keywords)

@app.command()
def semantics_blend(config: Optional[str] = typer.Option(None, "--config", "-c"),
                    blend: Optional[str] = None,
                    trees_collection: Optional[str] = None,
                    leaf_keywords: Optional[List[str]] = None,
                    write_csv: bool = typer.Option(False, "--write-csv/--no-write-csv")):
    conf = cfg.load(config)
    semantics.run(conf, blend=blend, trees_collection=trees_collection,
                  leaf_keywords=leaf_keywords, write_csv=write_csv)

@app.command()
def export_helios(config: Optional[str] = typer.Option(None, "--config", "-c"),
                  blend: Optional[str] = None,
                  materials_dir: Optional[str] = None,
                  output_dir: Optional[str] = None,
                  scene_name: Optional[str] = None,
                  use_own_materials: bool = True,
                  materials_name: Optional[str] = None,
                  save_scene_bbox: bool = True,
                  save_survey_file: bool = False):
    conf = cfg.load(config)
    export.run(conf, blend=blend, materials_dir=materials_dir, output_dir=output_dir, scene_name=scene_name,
               use_own_materials=use_own_materials, materials_name=materials_name,
               save_scene_bbox=save_scene_bbox, save_survey_file=save_survey_file)

@app.command()
def plan_path(config: Optional[str] = typer.Option(None, "--config", "-c"),
              scene_name: Optional[str] = None,
              survey_mode: str = "ULS",
              survey_name: Optional[str] = None,
              spacing: Optional[float] = None,
              rotate_deg: Optional[float] = None,
              relative_altitude: Optional[float] = None,
              speed: Optional[float] = None,
              pulse_freq_hz: Optional[int] = None,
              pattern: Optional[str] = None):
    conf = cfg.load(config)
    plan.run(conf, scene_name=scene_name, survey_mode=survey_mode, survey_name=survey_name,
             spacing=spacing, rotate_deg=rotate_deg, relative_altitude=relative_altitude,
             speed=speed, pulse_freq_hz=pulse_freq_hz, pattern=pattern)

@app.command()
def survey_run(config: Optional[str] = typer.Option(None, "--config", "-c"),
               survey_file: Optional[str] = None,
               assets_dir: Optional[str] = None,
               output_dir: Optional[str] = None,
               callback_frequency: Optional[int] = None,
               seed: str = "123"):
    conf = cfg.load(config)
    survey.run(conf, survey_file=survey_file, assets_dir=assets_dir,
               output_dir=output_dir, callback_frequency=callback_frequency, seed=seed)

@app.command()
def stats_blend(config: Optional[str] = typer.Option(None, "--config", "-c"),
                blend: Optional[str] = None):
    conf = cfg.load(config)
    stats.run(conf, blend=blend)

@app.command()
def postprocess_ml(config: Optional[str] = typer.Option(None, "--config", "-c"),
                    input_root: Optional[str] = None,
                    output_root: Optional[str] = None,
                    tile_size: Optional[float] = None,
                    merge_all_ts: bool = False,
                    ground_label: Optional[int] = None,
                    wood_label: Optional[int] = None,
                    leaf_label: Optional[int] = None,
                    leafwood: bool = False):
    """Post-process HELIOS simulation output to ML-ready format with tiling."""
    conf = cfg.load(config)
    postprocess.run(conf, input_root=input_root, output_root=output_root,
                   tile_size=tile_size, merge_all_ts=merge_all_ts,
                   ground_label=ground_label, wood_label=wood_label,
                   leaf_label=leaf_label, leafwood=leafwood)
