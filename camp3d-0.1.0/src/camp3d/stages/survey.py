
from __future__ import annotations
from typing import Optional
import os, time
from ..config import Config

def run(conf: Config, survey_file: Optional[str] = None, assets_dir: Optional[str] = None,
        output_dir: Optional[str] = None, callback_frequency: Optional[int] = None, seed: str = "123"):
    try:
        import pyhelios
    except Exception as e:
        print("[ERROR] pyhelios is required to run surveys:", e)
        raise SystemExit(1)

    # Resolve defaults from config
    survey_file = survey_file or conf.survey.file
    if not survey_file:
        # default to HELIOS/data/<scene>/surveys/<scene>_<mode>.xml
        scene = conf.scene.name or "Scene"
        mode = conf.planning.survey_mode
        helios_dir = conf.helios.get_output_dir()
        survey_file = os.path.join(helios_dir, "data", scene, "surveys", f"{scene}_{mode}.xml")
    assets_dir = assets_dir or os.path.join(conf.helios.get_output_dir(), "assets")
    if output_dir is None:
        scene = conf.scene.name or "Scene"
        output_dir = os.path.join(conf.helios.get_output_dir(), "output", scene)
    
    callback_frequency = int(callback_frequency or conf.survey.callback_frequency)

    # Silence Helios logger, fix RNG seed
    pyhelios.loggingQuiet()
    pyhelios.setDefaultRandomnessGeneratorSeed(str(seed))

    # Determine helios directory from survey file path
    # The survey file should be in: <helios_dir>/data/<scene>/surveys/<survey>.xml
    # So we need to go up 3 levels from the survey file to get to helios_dir
    survey_file_abs = os.path.abspath(survey_file)
    survey_dir = os.path.dirname(survey_file_abs)  # surveys/
    scene_dir = os.path.dirname(survey_dir)        # <scene>/
    data_dir = os.path.dirname(scene_dir)          # data/
    helios_dir = os.path.dirname(data_dir)         # helios/
    
    if not os.path.exists(os.path.join(helios_dir, "data")):
        print(f"[ERROR] Could not find helios directory with 'data' subdirectory from survey file: {survey_file}")
        print(f"[ERROR] Expected helios directory at: {helios_dir}")
        raise SystemExit(1)
    
    # Convert survey file path to be relative to helios directory
    survey_file_rel = os.path.relpath(os.path.abspath(survey_file), helios_dir)
    
    print(f"[INFO] Building simulation from '{survey_file_rel}' (helios dir: {helios_dir})…")
    
    # Change to helios directory so relative paths in survey file work correctly
    original_cwd = os.getcwd()
    os.chdir(helios_dir)
    
    try:
        simB = pyhelios.SimulationBuilder(str(survey_file_rel), str(assets_dir), str(output_dir))
        simB.setLasOutput(False)
        simB.setZipOutput(False)
        simB.setCallbackFrequency(callback_frequency)
        simB.setRebuildScene(False)

        t0 = time.time()
        sim = simB.build()
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
    print(f"[INFO] Built simulation in {time.time()-t0:.1f}s")

    print("[INFO] Starting simulation…")
    start_time = time.time()
    sim.start()

    if sim.isStarted():
        survey = sim.sim.getSurvey()
        scanner = sim.sim.getScanner()
        print(f"→ Survey Name: {survey.name}")
        print(f"→ Scanner: {scanner.toString()}\n")

    while sim.isRunning():
        elapsed = time.time() - start_time
        m, s = divmod(int(elapsed), 60)
        print(f"\r[RUN] Elapsed {m: >2}m {s: >2}s", end="", flush=True)
        time.sleep(10)
    print()

    if sim.isFinished():
        print("[INFO] Simulation finished!")

    output = sim.join()
    measurements = output.measurements
    trajectories = output.trajectories

    print(f"\n[RESULT] Number of measurements : {len(measurements)}")
    print(f"[RESULT] Number of trajectory points: {len(trajectories)}")

    base = os.path.join(output_dir, "Survey Playback", sim.sim.getSurvey().name)
    print(f"\nPoint clouds & trajectories saved under:\n  {base}")
