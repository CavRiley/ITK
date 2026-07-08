#!/usr/bin/env python3
"""Configure the wrapped ITK tree for wheel slicing (the `configure-wheels` task).

A Python driver rather than an inline pixi task: pixi's task shell parses only
bare ``$VAR`` — it rejects the ``${WHEEL_CC:+...}`` form needed to add the
compiler defines only when set. Here that stays conditional. WHEEL_CC / WHEEL_CXX
override the pixi env compiler (e.g. Clang for the weekly wheel build,
InsightSoftwareConsortium/ITK#4656); unset leaves CMake on the env default.
"""
from __future__ import annotations
import os
import subprocess
import sys

CMAKE = [
    "cmake",
    "-S.",
    "-GNinja",
    "-DITK_WRAP_PYTHON:BOOL=ON",
    "-DCMAKE_BUILD_TYPE:STRING=Release",
    "-DBUILD_TESTING:BOOL=OFF",
    "-DWRAP_ITK_INSTALL_COMPONENT_PER_MODULE:BOOL=ON",
    "-DWRAP_ITK_INSTALL_COMPONENT_IDENTIFIER:STRING=PythonWheel",
    "-DPY_SITE_PACKAGES_PATH:STRING=.",
]


def main() -> int:
    # Build tree location. Defaults to build-python (local/pixi flow); CI points
    # it at a container-shared volume so the one build is reused across wheels.
    build_dir = os.environ.get("WHEEL_ITK_BUILD_DIR", "build-python")
    cmd = ["cmake", f"-B{build_dir}", *CMAKE[1:]]
    if cc := os.environ.get("WHEEL_CC"):
        cmd.append(f"-DCMAKE_C_COMPILER:STRING={cc}")
    if cxx := os.environ.get("WHEEL_CXX"):
        cmd.append(f"-DCMAKE_CXX_COMPILER:STRING={cxx}")
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
