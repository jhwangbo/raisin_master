import os
import subprocess
import shutil
from pathlib import Path
from typing import Tuple

# --- Configuration ---
BUILD_ARCHITECTURE = "x64" # Target architecture (e.g., x64, x86)

def find_vswhere() -> Path:
    """Finds the vswhere.exe utility."""
    program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
    vswhere_path = program_files_x86 / "Microsoft Visual Studio/Installer/vswhere.exe"
    if not vswhere_path.exists():
        raise FileNotFoundError(f"vswhere.exe not found at {vswhere_path}")
    return vswhere_path

def find_visual_studio_path() -> Path:
    """Finds the latest Visual Studio installation path using vswhere."""
    vswhere_path = find_vswhere()
    command = [
        str(vswhere_path),
        "-latest",
        "-property", "installationPath",
        "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    vs_path = Path(result.stdout.strip())
    if not vs_path.exists():
        raise FileNotFoundError("Visual Studio installation not found.")
    return vs_path

def get_developer_environment(vs_path: Path, arch: str) -> dict:
    """
    Executes vcvarsall.bat and captures the resulting environment variables.
    """
    vcvarsall_path = vs_path / "VC/Auxiliary/Build/vcvarsall.bat"
    if not vcvarsall_path.exists():
        raise FileNotFoundError(f"vcvarsall.bat not found at {vcvarsall_path}")

    command = f'"{vcvarsall_path}" {arch} && set'
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)

    env = {}
    for line in result.stdout.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            env[key] = value

    full_env = os.environ.copy()
    full_env.update(env)
    return full_env

def find_build_tools(arch: str) -> Tuple[str, str, dict]:
    """
    Finds Visual Studio and Ninja, returning their paths and the configured
    developer environment.
    """
    vs_path = find_visual_studio_path()
    developer_env = get_developer_environment(vs_path, arch)

    ninja_path_str = shutil.which("ninja", path=developer_env.get("PATH"))
    if not ninja_path_str:
        raise FileNotFoundError("ninja.exe could not be found in the developer environment PATH.")

    return str(vs_path.as_posix()), str(Path(ninja_path_str).as_posix()), developer_env