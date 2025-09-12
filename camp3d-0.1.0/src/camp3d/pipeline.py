
from __future__ import annotations
from .config import Config
from .stages import create, semantics, tiling, export, plan, survey

def run(conf: Config,
        skip_create=False, skip_semantics=False, skip_tiling=True,
        skip_export=False, skip_plan=False, skip_survey=False):
    if not skip_create:
        create.run(conf)
    if not skip_semantics:
        semantics.run(conf)
    if not skip_tiling and conf.scene.tiling.enabled:
        tiling.run(conf)
    if not skip_export:
        export.run(conf)
    if not skip_plan:
        plan.run(conf)
    if not skip_survey:
        survey.run(conf)
