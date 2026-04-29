import subprocess
import sys
from pathlib import Path


def write_runner_script(root: Path) -> Path:
    script = root / "run_xmum_moodle_agent.ps1"
    python_exe = Path(sys.executable)
    content = f"""$ErrorActionPreference = "Stop"
Set-Location -LiteralPath "{root}"
$env:PYTHONPATH = "{root / 'src'}"
& "{python_exe}" -m xmum_moodle_agent.cli run
"""
    script.write_text(content, encoding="utf-8")
    return script


def install_windows_task(root: Path, task_name: str = "XMUM Moodle Agent", time: str = "08:00") -> str:
    script = write_runner_script(root)
    command = [
        "schtasks",
        "/Create",
        "/TN",
        task_name,
        "/TR",
        f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{script}"',
        "/SC",
        "DAILY",
        "/ST",
        time,
        "/F",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()
