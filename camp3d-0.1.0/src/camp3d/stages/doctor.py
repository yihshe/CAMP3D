
import typer, shutil, subprocess, os
from rich import print
from ..config import Config, load
from ..blender_exec import check_addon

app = typer.Typer(help="Environment checks")

@app.command()
def all(config: str = typer.Option(None, "--config", "-c")):
    conf = load(config)
    # Blender on PATH
    blender = shutil.which(conf.blender.bin) or shutil.which("blender")
    print(f"[bold]Blender:[/bold] {blender or 'NOT FOUND'}")
    if blender:
        try:
            out = subprocess.check_output([blender, "--version"], text=True, timeout=8)
            print(out.strip().splitlines()[0])
        except Exception as e:
            print(f"[yellow]Warning:[/yellow] Could not query blender version: {e}")
        # Blender2Helios add-on enabled?
        status = check_addon(blender, "Blender2Helios")
        print(f"[bold]Blender2Helios add-on enabled:[/bold] {status}")

    # pyhelios available?
    try:
        import pyhelios  # noqa: F401
        print("[bold]pyhelios importable:[/bold] yes")
    except Exception as e:
        print(f"[bold]pyhelios importable:[/bold] no — {e}")

    # Materials directory
    mat_root = conf.u2h.materials_dir
    has_dir = os.path.isdir(mat_root)
    print(f"[bold]materials directory:[/bold] {mat_root}  ({'ok' if has_dir else 'missing'})")

    # Output dir
    od = conf.helios.get_output_dir()
    print(f"[bold]Output directory:[/bold] {od}")
