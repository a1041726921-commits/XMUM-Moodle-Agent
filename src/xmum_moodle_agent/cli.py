import argparse
import asyncio
import shutil
from pathlib import Path

from .agent import run_agent
from .config import ConfigError, load_config
from .moodle import MoodleAutomationError, MoodleClient
from .scheduler import install_windows_task


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="xmum-moodle-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Create local folders and .env example.")
    subparsers.add_parser("run", help="Log in, download Moodle materials, and update the DOCX.")
    subparsers.add_parser("check-login", help="Verify Moodle credentials and print discovered course count.")
    schedule_parser = subparsers.add_parser("install-schedule", help="Install a Windows daily 08:00 task.")
    schedule_parser.add_argument("--time", default="08:00", help="Daily run time in HH:MM, default 08:00.")

    args = parser.parse_args(argv)
    root = Path.cwd()

    try:
        if args.command == "init":
            return _init(root)
        if args.command == "run":
            config = load_config(root=root)
            stats = asyncio.run(run_agent(config))
            print(
                "Done: "
                f"{stats['courses']} courses, {stats['resources']} resources, "
                f"{stats['downloaded_or_changed']} downloaded/changed, {stats['parsed']} parsed."
            )
            print(f"Knowledge checklist: {config.docx_path}")
            return 0
        if args.command == "check-login":
            config = load_config(root=root)
            count = asyncio.run(_check_login(config))
            print(f"Moodle login OK. Discovered {count} course(s).")
            return 0
        if args.command == "install-schedule":
            output = install_windows_task(root=root, time=args.time)
            print(output or f"Installed Windows task for daily {args.time}.")
            return 0
    except (ConfigError, MoodleAutomationError, subprocess_error()) as exc:
        print(f"Error: {exc}")
        return 1

    return 1


def subprocess_error():
    import subprocess

    return subprocess.CalledProcessError


def _init(root: Path) -> int:
    (root / "data" / "courses").mkdir(parents=True, exist_ok=True)
    env = root / ".env"
    if not env.exists():
        shutil.copyfile(root / ".env.example", env)
        print("Created .env from .env.example. Fill in your Campus ID and password.")
    else:
        print(".env already exists; left it unchanged.")
    print("Created data/courses folder.")
    return 0


async def _check_login(config) -> int:
    async with MoodleClient(config) as moodle:
        await moodle.login()
        courses = await moodle.discover_courses()
        return len(courses)


if __name__ == "__main__":
    raise SystemExit(main())
