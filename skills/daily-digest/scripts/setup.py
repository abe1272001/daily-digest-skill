#!/usr/bin/env python3
"""Setup script for daily-digest. Creates venv and installs dependencies."""

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

PYTHON_DEPS = [
    "feedparser",
    "yt-dlp",
    "faster-whisper",
    "httpx",
    "pyyaml",
]

SYSTEM_TOOLS = [
    ("curl", "brew install curl / apt install curl"),
    ("ffmpeg", "brew install ffmpeg / apt install ffmpeg"),
]

DEFAULT_VENV_DIR = "daily-digest-venv"


def get_venv_python(venv_dir: str) -> str:
    """Get path to python in venv."""
    return str(Path(venv_dir) / "bin" / "python")


def check_venv(venv_dir: str) -> bool:
    """Check if venv exists and is valid."""
    return os.path.isfile(get_venv_python(venv_dir))


def create_venv(venv_dir: str):
    """Create a virtual environment."""
    print(f"  Creating virtual environment at {venv_dir}/...")
    venv.create(venv_dir, with_pip=True)
    print("  [v] Virtual environment created")


def check_python_dep(venv_dir: str, package: str) -> bool:
    """Check if a Python package is installed in the venv."""
    python = get_venv_python(venv_dir)
    import_name = package.replace("-", "_")
    try:
        subprocess.run(
            [python, "-c", f"import {import_name}"],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_system_tool(name: str) -> bool:
    return shutil.which(name) is not None


def run_check(venv_dir: str) -> dict:
    """Check all dependencies and return status."""
    results = {"python": {}, "system": {}, "venv": False, "all_ok": True}

    print("=" * 50)
    print("  Daily Digest — Dependency Check")
    print("=" * 50)

    print(f"\n  Virtual environment ({venv_dir}/):")
    if check_venv(venv_dir):
        print("  [v] exists")
        results["venv"] = True
    else:
        print("  [x] NOT FOUND — run with --install to create")
        results["all_ok"] = False
        results["venv"] = False

    if results["venv"]:
        print("\n  Python packages:")
        for dep in PYTHON_DEPS:
            ok = check_python_dep(venv_dir, dep)
            status = "OK" if ok else "MISSING"
            symbol = "  [v]" if ok else "  [x]"
            print(f"  {symbol} {dep} ... {status}")
            results["python"][dep] = ok
            if not ok:
                results["all_ok"] = False

    print("\n  System tools:")
    for tool, hint in SYSTEM_TOOLS:
        ok = check_system_tool(tool)
        status = "OK" if ok else f"MISSING ({hint})"
        symbol = "  [v]" if ok else "  [x]"
        print(f"  {symbol} {tool} ... {status}")
        results["system"][tool] = ok
        if not ok:
            results["all_ok"] = False

    print("\n" + "=" * 50)
    if results["all_ok"]:
        print("  All dependencies are installed!")
    else:
        print("  Some dependencies are missing. Run with --install to fix.")
    print("=" * 50)

    return results


def run_install(venv_dir: str):
    """Create venv and install missing Python dependencies."""
    print("=" * 50)
    print("  Daily Digest — Installing Dependencies")
    print("=" * 50)

    # Step 1: Create venv
    if not check_venv(venv_dir):
        print("\n  [1/3] Creating virtual environment...")
        create_venv(venv_dir)
    else:
        print("\n  [1/3] Virtual environment already exists")

    python = get_venv_python(venv_dir)

    # Step 2: Upgrade pip
    print("\n  [2/3] Upgrading pip...")
    subprocess.run(
        [python, "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    print("    [v] pip upgraded")

    # Step 3: Install packages
    missing = [dep for dep in PYTHON_DEPS if not check_python_dep(venv_dir, dep)]

    if not missing:
        print("\n  [3/3] All Python packages already installed!")
    else:
        print(f"\n  [3/3] Installing {len(missing)} packages...")
        for i, dep in enumerate(missing, 1):
            print(f"    ({i}/{len(missing)}) {dep}...", end=" ", flush=True)
            try:
                subprocess.check_call(
                    [python, "-m", "pip", "install", dep],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                print("[v]")
            except subprocess.CalledProcessError as e:
                print(f"[x] {e}")

    # Check system tools
    missing_tools = [
        (tool, hint) for tool, hint in SYSTEM_TOOLS if not check_system_tool(tool)
    ]
    if missing_tools:
        print("\n  System tools still needed (install manually):")
        for tool, hint in missing_tools:
            print(f"    [x] {tool} — {hint}")

    print("\n" + "=" * 50)
    print(f"  Done! Python: {python}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Daily Digest setup")
    parser.add_argument("--check", action="store_true", help="Check dependencies")
    parser.add_argument("--install", action="store_true", help="Create venv and install deps")
    parser.add_argument("--venv-dir", default=DEFAULT_VENV_DIR, help="Venv directory path")
    args = parser.parse_args()

    if args.install:
        run_install(args.venv_dir)
    elif args.check:
        run_check(args.venv_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
