# Wrapping/Packaging — in-tree Python wheel build

Build ITK's Python wheels from this repository by slicing a single pre-built,
Python-wrapped ITK tree into per-group wheels, with no per-wheel recompilation.

ITK already emits a per-module install component
(`<Module>PythonWheelRuntimeLibraries`) when wrapping is configured with
`-DWRAP_ITK_INSTALL_COMPONENT_PER_MODULE=ON` — that is the slicing seam. This
directory adds only the wheel definitions on top of it: a per-group
`pyproject.toml` plus the placement and per-component install CMake under
`cmake/` (relocated from ITKPythonPackage). Each wheel build is a standard
PEP 517 build that runs `cmake --install` of only its group's components.

> Experimental. Nothing here is wired into ITK's default build.

## Layout

```
Wrapping/Packaging/
├── CMakeLists.txt          shared scikit-build-core source for all groups
├── WHEEL_NAMES.txt         the wheel names
├── cmake/                  module->wheel placement + per-component install
├── core/  numerics/  io/  filtering/  registration/  segmentation/
│                           one pyproject.toml per group wheel
└── meta/                   the "itk" umbrella package
```

Group wheels are versioned at ITK's version (they are ITK, sliced). The `itk`
meta-package depends on the six group wheels pinned at that version.

## Build

The `wheel` pixi environment provides cmake, ninja, the compiler, and the build
frontend:

```sh
pixi run -e wheel build-wrapped-itk   # compile wrapped ITK once (the reuse target)
pixi run -e wheel build-wheels        # slice it into every wheel
```

`build-wrapped-itk` configures with the flags the slice requires:
`WRAP_ITK_INSTALL_COMPONENT_PER_MODULE`, `WRAP_ITK_INSTALL_COMPONENT_IDENTIFIER`,
and a relative `PY_SITE_PACKAGES_PATH` (so the install lands in the wheel, not
the environment). `build-wheels` runs `Utilities/Maintenance/build_wheels.py`,
which slices each group plus the meta wheel.

For CI, `.github/workflows/python-wheels.yml` drives the same flow with
cibuildwheel.

## Design notes

- **Self-contained wheels.** ITK is built static (`BUILD_SHARED_LIBS=OFF`), so
  each extension embeds the ITK code it needs and links only system libraries.
  Wheels carry no ITK shared libs and wheel-repair is nearly a no-op.
- **Dependency-driven placement.** Each module is assigned to the lowest wheel
  group that all of its dependents share ("common ancestor"), so a module used
  across layers sinks toward Core. Placement needs `ITK_SOURCE_DIR` for group
  membership and `find_package(ITK)` for the dependency graph.
- **Meta wheel is platform-tagged.** The `itk` package ships no code but is
  tagged to the platform + ABI (not `py3-none-any`), matching the PyPI `itk`
  wheel, so `pip install itk` only resolves where the group wheels exist.
- **Compiler.** Local builds use the pixi env compiler (gcc on Linux, clang on
  macOS). Set `WHEEL_CC` / `WHEEL_CXX` to override — e.g. to drive the Linux
  build with Clang, the target for weekly wheels (ITK#4656, gated on #3093).
  `.github/workflows/wheel-compiler-benchmark.yml` times gcc vs Clang. In the
  manylinux CI container the wrapped-ITK build instead uses the image's own
  gcc-toolset (see `cibw-build-wrapped-itk.sh`) so ITK's static libraries share
  the extension's ABI baseline and pass `auditwheel`.
