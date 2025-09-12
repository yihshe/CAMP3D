
import shutil, os
import typer
from importlib.resources import files

app = typer.Typer(help="Helper utilities")

@app.command("install-materials")
def install_materials(materials_dir: str = "./materials"):
    """Copy example .mtl files into <materials_dir>."""
    try:
        # Try to get the examples directory from the package
        src_dir = files("camp3d").joinpath("..", "..", "examples", "materials").resolve()
    except:
        # Fallback to relative path from the current file
        src_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "examples", "materials")
    
    os.makedirs(materials_dir, exist_ok=True)
    count = 0
    for name in ("example.mtl","spread.mtl","spread_leafwood.mtl"):
        src_file = os.path.join(src_dir, name)
        if os.path.exists(src_file):
            shutil.copy2(src_file, os.path.join(materials_dir, name))
            count += 1
        else:
            typer.echo(f"Warning: {src_file} not found")
    typer.echo(f"Installed {count} materials to {materials_dir}")

@app.command("write-addon")
def write_addon(target_dir: str):
    """Write adapted Blender2Helios.py into Blender's addons folder."""
    try:
        # Find the addon file - examples are included in the package distribution
        # The examples folder is at the same level as the src folder in the distribution
        src = files("camp3d").joinpath("../../examples/addons/Blender2Helios.py").resolve()
        
        # Check if source file exists
        if not os.path.exists(src):
            typer.echo(f"Error: Source addon file not found at {src}")
            typer.echo("Please ensure the camp3d package is properly installed.")
            raise typer.Exit(1)
        
        # Create target directory if it doesn't exist
        try:
            os.makedirs(target_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            typer.echo(f"Error: Cannot create directory {target_dir}")
            typer.echo(f"Reason: {e}")
            typer.echo("\nAlternative: You can manually install the addon by:")
            typer.echo("1. Copy the file from: examples/addons/Blender2Helios.py")
            typer.echo("2. Paste it to your Blender addons directory")
            typer.echo("3. Enable it in Blender: Edit → Preferences → Add-ons → search 'Blender2Helios'")
            raise typer.Exit(1)
        
        dest = os.path.join(target_dir, "Blender2Helios.py")
        
        # Try to copy the file
        try:
            shutil.copy2(src, dest)
            typer.echo(f"Successfully wrote add-on to: {dest}")
            typer.echo("Enable it in Blender: Edit → Preferences → Add-ons → search 'Blender2Helios'")
        except (OSError, PermissionError) as e:
            typer.echo(f"Error: Cannot write to {dest}")
            typer.echo(f"Reason: {e}")
            typer.echo("\nAlternative: You can manually install the addon by:")
            typer.echo("1. Copy the file from: examples/addons/Blender2Helios.py")
            typer.echo("2. Paste it to your Blender addons directory")
            typer.echo("3. Enable it in Blender: Edit → Preferences → Add-ons → search 'Blender2Helios'")
            raise typer.Exit(1)
            
    except Exception as e:
        typer.echo(f"Unexpected error: {e}")
        typer.echo("\nAlternative: You can manually install the addon by:")
        typer.echo("1. Copy the file from: examples/addons/Blender2Helios.py")
        typer.echo("2. Paste it to your Blender addons directory")
        typer.echo("3. Enable it in Blender: Edit → Preferences → Add-ons → search 'Blender2Helios'")
        raise typer.Exit(1)

@app.command("install-examples")
def install_examples(scene_dir: str = "./scene"):
    """Install example scenes for quick testing."""
    try:
        # Get the examples directory from the package
        src_dir = files("camp3d").joinpath("..", "..", "examples", "scenes").resolve()
    except:
        # Fallback to relative path from the current file
        src_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "examples", "scenes")
    
    os.makedirs(scene_dir, exist_ok=True)
    
    # Copy quickdemo example
    single_tree_src = os.path.join(src_dir, "quickdemo")
    single_tree_dest = os.path.join(scene_dir, "quickdemo")
    
    if os.path.exists(single_tree_src):
        if os.path.exists(single_tree_dest):
            shutil.rmtree(single_tree_dest)
        shutil.copytree(single_tree_src, single_tree_dest)
        typer.echo(f"Installed quickdemo example to {single_tree_dest}")
    else:
        typer.echo(f"Warning: quickdemo example not found at {single_tree_src}")
    
    typer.echo(f"Example scenes installed to {scene_dir}")
    typer.echo("You can now run: camp3d stats-blend --blend ./scene/quickdemo/quickdemo.blend")
