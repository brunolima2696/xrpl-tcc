from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from typing import Callable

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

def get_script_path(script_name: str) -> Path:
    return PROJECT_DIR / script_name


async def run_script(script_name: str, on_output: Callable[[str], None]) -> int:
    """
    Execute a Python script from /scripts and stream output line by line.

    Args:
        script_name: Name of the script file inside the scripts folder.
        on_output: Callback that receives each output line.

    Returns:
        Process exit code.
    """
    script_path = get_script_path(script_name)

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(PROJECT_DIR),
    )

    assert process.stdout is not None

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        on_output(line.decode("utf-8", errors="replace").rstrip())

    return await process.wait()