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
# Two toolchain paths, because the per-wheel extension (compiled later by
# scikit-build-core) must link ITK's static libs without pulling in symbols
# newer than the wheel's ABI baseline:
#   * manylinux container: build ITK with the image's own gcc-toolset. The
#     conda-forge compiler (via pixi) links a newer libstdc++/glibc, so
#     auditwheel rejects the wheel with "too-recent versioned symbols". The
#     manylinux gcc-toolset matches the compiler cibuildwheel uses for the
#     extension, keeping every symbol within the manylinux_2_28 baseline.
#   * macOS/native: the pixi `wheel` env supplies clang, cmake, and ninja
#     (delocate handles the dylib ABI, so no glibc concern applies).
#
set -euo pipefail

PROJECT="${1:-$PWD}"
BUILD="${PROJECT}/build-python"

if [ -f "${BUILD}/cmake_install.cmake" ]; then
  echo "[cibw-before-all] wrapped ITK already present at ${BUILD} — reusing."
  exit 0
fi

cd "${PROJECT}"

# /opt/python is the manylinux image layout; its absence means a native build.
if [ -d /opt/python ]; then
  echo "[cibw-before-all] manylinux container — building ITK with the image gcc-toolset ..."

  # Newest gcc-toolset on the image (manylinux_2_28 ships gcc-toolset-14). Its
  # binaries stay compatible with the image's baseline glibc/libstdc++.
  gts_enable=""
  for f in /opt/rh/gcc-toolset-*/enable; do
    [ -e "${f}" ] && gts_enable="${f}"
  done
  if [ -n "${gts_enable}" ]; then
    # shellcheck disable=SC1090
    source "${gts_enable}"
  fi

  # cp39 interpreter + pip-provided cmake/ninja; no pixi/conda toolchain here.
  export PATH="/opt/python/cp39-cp39/bin:${PATH}"
  python -m pip install --upgrade cmake ninja

  export WHEEL_CC=gcc WHEEL_CXX=g++
  python "${PROJECT}/Utilities/Maintenance/configure_wrapped_itk.py"
  cmake --build "${BUILD}"
else
  echo "[cibw-before-all] native build via the pixi wheel env ..."
  if ! command -v pixi >/dev/null 2>&1; then
    echo "[cibw-before-all] pixi not found — installing it..."
    export PIXI_HOME="${PIXI_HOME:-$HOME/.pixi}"
    curl -fsSL https://pixi.sh/install.sh | bash
    export PATH="${PIXI_HOME}/bin:${PATH}"
  fi
  # configure-wheels + build-wrapped-itk carry the slice flags (per-module
  # components, the PythonWheel identifier, relative PY_SITE_PACKAGES_PATH) and
  # pull cmake/ninja/compiler from the env.
  pixi run -e wheel build-wrapped-itk
fi

echo "[cibw-before-all] wrapped ITK build complete."
