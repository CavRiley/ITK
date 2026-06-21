# The itk meta-package is pure-Python (wheel.platlib=false): it builds no native
# code and installs nothing. This trivial CMake project lets scikit-build-core
# produce a metadata-only wheel whose dependencies (the 6 group wheels) come from
# [project] in pyproject.toml.
cmake_minimum_required(VERSION 3.26.6 FATAL_ERROR)
project(itk_meta NONE)
