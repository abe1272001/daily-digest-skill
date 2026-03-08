#!/usr/bin/env python3
"""Setup script for daily-digest dependencies. Checks and installs requirements."""

import argparse
import shutil
import subprocess
import sys

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


def check_python_dep(package: str) -> bool:
    """Check if a Python package is importable."""
    # yt-dlp imports as yt_dlp, faster-whisper as faster_whisper
    import_name = package.replace("-", "_")
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def check_system_tool(name: str) -> bool:
    return shutil.which(name) is not None


def run_check() -> dict:
    """Check all dependencies and return status."""
    results = {"python": {}, "system": {}, "all_ok": True}

    print("=" * 50)
    print("  Daily Digest — Dependency Check")
    print("=" * 50)

    print("\n📦 Python packages:")
    for dep in PYTHON_DEPS:
        ok = check_python_dep(dep)
        status = "OK" if ok else "MISSING"
        symbol = "  [v]" if ok else "  [x]"
        print(f"  {symbol} {dep} ... {status}")
        results["python"][dep] = ok
        if not ok:
            results["all_ok"] = False

    print("\n🔧 System tools:")
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


def run_install():
    """Install missing Python dependencies."""
    print("=" * 50)
    print("  Daily Digest — Installing Dependencies")
    print("=" * 50)

    missing = [dep for dep in PYTHON_DEPS if not check_python_dep(dep)]

    if not missing:
        print("\n  All Python packages already installed!")
        return

    for i, dep in enumerate(missing, 1):
        print(f"\n  Step {i}/{len(missing)}: Installing {dep}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", dep],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            print(f"    [v] {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"    [x] Failed to install {dep}: {e}")
            print(f"    Try manually: pip install {dep}")

    # Check system tools
    missing_tools = [
        (tool, hint) for tool, hint in SYSTEM_TOOLS if not check_system_tool(tool)
    ]
    if missing_tools:
        print("\n  System tools still needed (install manually):")
        for tool, hint in missing_tools:
            print(f"    [x] {tool} — {hint}")

    print("\n" + "=" * 50)
    print("  Installation complete! Run --check to verify.")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Daily Digest setup")
    parser.add_argument("--check", action="store_true", help="Check dependencies")
    parser.add_argument(
        "--install", action="store_true", help="Install missing dependencies"
    )
    args = parser.parse_args()

    if args.install:
        run_install()
    elif args.check:
        run_check()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
