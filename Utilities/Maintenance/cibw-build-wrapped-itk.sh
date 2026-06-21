#!/usr/bin/env bash
#
# cibuildwheel CIBW_BEFORE_ALL hook (SKETCH).
#
# Builds the Python-wrapped ITK tree ONCE, *inside* the build container
# (e.g. manylinux), configured for wheel slicing. Guarded so that the
# 2nd..Nth wheel builds in the same cibuildwheel job reuse it instead of
# recompiling ITK 7x. This is the "build ITK in the same image" step that
# every wheel then slices.
#
# The toolchain (cmake, ninja, C++ compiler) and the exact configure flags come
# from the `wheel` pixi environment defined in pyproject.toml, so CI uses the
# same pinned tools and the same build definition as the local
# `pixi run -e wheel build-wrapped-itk` flow. cibuildwheel runs CIBW_BEFORE_ALL
# at the project root:
#   * Linux:   inside the manylinux container, project mounted at /project
#              (pixi is not preinstalled there, so we bootstrap it)
#   * macOS/Windows: natively, in the checked-out repo
#
set -euo pipefail

PROJECT="${1:-$PWD}"
BUILD="${PROJECT}/build-python"

if [ -f "${BUILD}/cmake_install.cmake" ]; then
  echo "[cibw-before-all] wrapped ITK already present at ${BUILD} — reusing."
  exit 0
fi

# Use pixi if present; otherwise bootstrap it into the container (manylinux).
if ! command -v pixi >/dev/null 2>&1; then
  echo "[cibw-before-all] pixi not found — installing it..."
  export PIXI_HOME="${PIXI_HOME:-$HOME/.pixi}"
  curl -fsSL https://pixi.sh/install.sh | bash
  export PATH="${PIXI_HOME}/bin:${PATH}"
fi

echo "[cibw-before-all] building wrapped ITK into ${BUILD} via the pixi wheel env ..."
cd "${PROJECT}"

# configure-wheels + build-wrapped-itk carry the slice flags
# (per-module components, the PythonWheel identifier, relative
# PY_SITE_PACKAGES_PATH) and pull cmake/ninja/compiler from the env.
pixi run -e wheel build-wrapped-itk

echo "[cibw-before-all] wrapped ITK build complete."
