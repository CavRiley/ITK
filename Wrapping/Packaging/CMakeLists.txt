# Shared scikit-build-core source for every ITK wheel group.
cmake_minimum_required(VERSION 3.26.6 FATAL_ERROR) # first cmake with SABIModule

project(ITKWheels CXX)

# Default to the repository root (two levels up).
if(NOT DEFINED ITK_SOURCE_DIR)
  get_filename_component(
    ITK_SOURCE_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/../.."
    ABSOLUTE
  )
endif()

# Pre-built, Python-wrapped ITK tree to reuse; supplied by the driver.
if(
  NOT
    DEFINED
      ITK_BINARY_DIR
  OR
    NOT
      EXISTS
        "${ITK_BINARY_DIR}/cmake_install.cmake"
)
  message(
    FATAL_ERROR
    "ITK_BINARY_DIR must point at a pre-built ITK build tree containing "
    "cmake_install.cmake. Got: '${ITK_BINARY_DIR}'"
  )
endif()

message(STATUS "ITK_SOURCE_DIR = ${ITK_SOURCE_DIR}")
message(STATUS "ITK_BINARY_DIR = ${ITK_BINARY_DIR} (reused, not rebuilt)")

# Which module group this build packages. build_wheels.py passes it explicitly;
# a plain `pip wheel` / cibuildwheel build defaults it from the scikit-build
# project name (itk-core, itk-io, ...). scikit-build-core normalizes that to
# underscores (itk_core), so restore the itk-<group> form ipp_wheel_to_group wants.
if(NOT DEFINED ITKPythonPackage_WHEEL_NAME AND DEFINED SKBUILD_PROJECT_NAME)
  string(REPLACE "_" "-" ITKPythonPackage_WHEEL_NAME "${SKBUILD_PROJECT_NAME}")
endif()

include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/ITKPythonPackage_Utils.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/ITKPythonPackage_BuildWheels.cmake)
