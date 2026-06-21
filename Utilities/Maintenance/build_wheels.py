#!/usr/bin/env python3
"""Build ITK Python wheels by slicing a pre-built, Python-wrapped ITK tree.

Run via pixi:  pixi run -e wheel build-wheels
Or directly:   python Utilities/Maintenance/build_wheels.py [GROUP ...]

The wheel *definitions* (per-group pyproject.toml, the slicing CMake, WHEEL_NAMES.txt)
live in Wrapping/Packaging/. This script is just the driver that loops over them.

Prerequisite: a wrapped ITK build tree configured for slicing — produce it once
with `pixi run -e wheel build-wrapped-itk` (sets WRAP_ITK_INSTALL_COMPONENT_PER_MODULE,
the PythonWheel component identifier, and a relative PY_SITE_PACKAGES_PATH).
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent           # Utilities/Maintenance
REPO = HERE.parents[1]                            # ITK source root
PACKAGING = REPO / "Wrapping" / "Packaging"       # wheel definitions live here


def wheel_groups() -> list[str]:
    """Group names (e.g. 'core') from WHEEL_NAMES.txt, excluding the meta wheel."""
    names = (PACKAGING / "WHEEL_NAMES.txt").read_text().split()
    return [n[len("itk-"):] for n in names if n.startswith("itk-") and n != "itk-meta"]


def run_build(src: Path, dist: Path, defines: list[str]) -> None:
    cmd = [
        sys.executable, "-m", "build", "--wheel", "--no-isolation",
        "--skip-dependency-check", "--outdir", str(dist),
        *defines, str(src),
    ]
    print(f"\n=== building {src.name} ===", flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("groups", nargs="*", help="group(s) to build (default: all + meta)")
    ap.add_argument("--itk-build-dir",
                    default=os.environ.get("ITK_BINARY_DIR", str(REPO / "build-python")),
                    help="pre-built wrapped ITK tree to slice (default: <repo>/build-python)")
    ap.add_argument("--dist", default=str(PACKAGING / "dist"), help="output directory for wheels")
    ap.add_argument("--use-tbb", default="OFF", help="ITKPythonPackage_USE_TBB (ON/OFF)")
    args = ap.parse_args()

    itk_build = Path(args.itk_build_dir).resolve()
    if not (itk_build / "cmake_install.cmake").exists():
        sys.exit(
            f"ERROR: '{itk_build}' is not a built ITK tree (no cmake_install.cmake).\n"
            f"       Build it once first:  pixi run -e wheel build-wrapped-itk"
        )
    dist = Path(args.dist)
    dist.mkdir(parents=True, exist_ok=True)

    slice_defines = [
        f"--config-setting=cmake.define.ITK_BINARY_DIR={itk_build}",
        f"--config-setting=cmake.define.ITK_SOURCE_DIR={REPO}",
        "--config-setting=cmake.define.ITKPythonPackage_ITK_BINARY_REUSE=ON",
        f"--config-setting=cmake.define.ITKPythonPackage_USE_TBB={args.use_tbb}",
    ]

    groups = args.groups or wheel_groups()
    for g in groups:
        run_build(
            PACKAGING / g, dist,
            [f"--config-setting=cmake.define.ITKPythonPackage_WHEEL_NAME=itk-{g}", *slice_defines],
        )

    # Build the pure-Python meta wheel only on a full run (no explicit groups given).
    if not args.groups:
        run_build(PACKAGING / "meta", dist, [])

    print(f"\nWheels in {dist}:")
    for whl in sorted(dist.glob("*.whl")):
        print(f"  {whl.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
