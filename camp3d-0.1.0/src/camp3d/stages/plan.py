
from __future__ import annotations
from typing import Optional
import os
from ..config import Config

def read_bbox(bbox_file: str):
    with open(bbox_file, 'r', encoding='utf-8') as f:
        lines = f.read().strip().splitlines()
    if len(lines) < 2:
        raise ValueError("bbox file must contain 2 lines: 'minx miny maxx maxy' and 'minz maxz'")
    bbox = [float(v) for v in lines[0].split()]
    z = [float(v) for v in lines[1].split()]
    return bbox, z

def run(conf: Config,
        scene_name: Optional[str] = None,
        survey_mode: str = "ULS",
        survey_name: Optional[str] = None,
        spacing: Optional[float] = None,
        rotate_deg: Optional[float] = None,
        relative_altitude: Optional[float] = None,
        speed: Optional[float] = None,
        pulse_freq_hz: Optional[int] = None,
        pattern: Optional[str] = None,
        scanner_settings_id: str = "ls_template",
        scanner: str = "data/scanners_als.xml#riegl_vux-1uav",
        platform: str = "data/platforms.xml#copter_linearpath"):
    try:
        from pyhelios.util import flight_planner
    except Exception as e:
        print("[ERROR] pyhelios is required for planning:", e)
        raise SystemExit(1)

    scene_name = scene_name or conf.scene.name or "Scene"
    survey_mode = survey_mode or conf.planning.survey_mode
    survey_name = survey_name or f"{scene_name}_{survey_mode}"
    spacing = spacing if spacing is not None else conf.planning.spacing
    rotate_deg = rotate_deg if rotate_deg is not None else conf.planning.rotate_deg
    relative_altitude = relative_altitude if relative_altitude is not None else conf.planning.relative_altitude
    speed = speed if speed is not None else conf.planning.speed
    pulse_freq_hz = pulse_freq_hz if pulse_freq_hz is not None else conf.planning.pulse_freq_hz
    pattern = pattern or conf.planning.pattern

    output_dir = conf.helios.get_output_dir()
    bbox_path = os.path.join(output_dir, "data", scene_name, "surveys", "scene_bbox.txt")
    if not os.path.exists(bbox_path):
        print(f"[ERROR] bbox file not found: {bbox_path}")
        raise SystemExit(1)

    bbox, z_range = read_bbox(bbox_path)
    import numpy as np
    altitude = float(np.mean(z_range) + relative_altitude)

    wp, corners, total_dist = flight_planner.compute_flight_lines(
        bbox, spacing=spacing, rotate_deg=rotate_deg, flight_pattern=pattern
    )
    legs_xml = flight_planner.write_legs(wp, altitude=altitude, template_id=scanner_settings_id, speed=speed)

    scene_rel_path  = f"data/{scene_name}/scenes/{scene_name}.xml"
    scene_id = scene_name
    survey_file = os.path.join(output_dir, "data", scene_name, "surveys", f"{survey_name}.xml")
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <document>
        <scannerSettings id="{scanner_settings_id}" active="true" scanAngle_deg="90" pulseFreq_hz="{pulse_freq_hz}" scanFreq_hz="50" />
        <survey name="{survey_name}" platform="{platform}" scanner="{scanner}" scene="{scene_rel_path}#{scene_id}">
    {legs_xml}
        </survey>
    </document>
    '''
    os.makedirs(os.path.dirname(survey_file), exist_ok=True)
    with open(survey_file, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[INFO] Wrote survey: {survey_file}")
