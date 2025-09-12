
from __future__ import annotations
import os
import subprocess, shlex
from importlib.resources import files
from typing import List, Optional

def blender_script_path(script_name: str) -> str:
    return str(files("camp3d.resources.blender_scripts").joinpath(script_name))

def run_blender(blender_bin: str, script_name: str, blend_file: Optional[str], args: List[str]) -> int:
    cmd = [blender_bin]
    if blend_file:
        cmd += ["--background", blend_file]
    else:
        cmd += ["--background"]
    
    # Check if script_name is a file path or script name
    if os.path.exists(script_name):
        # It's a file path
        cmd += ["--python", script_name, "--"]
    else:
        # It's a script name, resolve the path
        cmd += ["--python", blender_script_path(script_name), "--"]
    
    cmd += args
    return subprocess.run(cmd).returncode

def check_addon(blender_bin: str, addon_name: str = "Blender2Helios") -> str:
    code = "import addon_utils; s=addon_utils.check('%s'); print(s[1])" % addon_name
    try:
        out = subprocess.check_output([blender_bin, "--background", "--python-expr", code], text=True, timeout=20)
        return out.strip().splitlines()[-1]
    except Exception as e:
        return f"ERROR: {e}"
