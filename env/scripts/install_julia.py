#!/usr/bin/env python3
"""
Trigger Julia installation via juliacall.

This script imports juliacall, which automatically downloads and installs
Julia if not already present. This allows 'make environment' to set up
the complete environment in one command.
"""

import os
import shutil
import subprocess
import sys

print("=" * 80)
print("Installing Julia via juliacall...")
print("=" * 80)
print()

# Calculate environment directory FIRST (before importing juliacall)
# This script is in lib/scripts/, so we need to go up to lib/ then across to env/
script_dir = os.path.dirname(os.path.abspath(__file__))  # lib/scripts/
lib_dir = os.path.dirname(script_dir)  # lib/
repo_root = os.path.dirname(lib_dir)  # project root
env_dir = os.path.join(repo_root, "env")  # env/
julia_depot = os.path.join(repo_root, ".julia")

# Configure Julia to use project-local depot (not ~/.julia)
os.environ["JULIA_DEPOT_PATH"] = julia_depot

# CRITICAL: PythonCall should NOT be in env/Project.toml!
# It is managed by juliacall in .julia/pyjuliapkg/ and should only exist there.
# Adding it to env/Project.toml causes "Package PythonCall does not seem to be
# installed" errors because Julia looks for it in the wrong project.

# Tell juliacall to create its pyjuliapkg environment inside .julia/
# Juliacall will create .julia/pyjuliapkg/ subdirectory with Project.toml and Manifest.toml
# If not set, juliacall defaults to ~/.julia/pyjuliapkg (global, not project-local)
os.environ["PYTHON_JULIAPKG_PROJECT"] = julia_depot

# Configure PythonCall to use system Python (not CondaPkg)
# This prevents CondaPkg from creating a redundant Python environment
os.environ["JULIA_CONDAPKG_BACKEND"] = "Null"
os.environ["JULIA_PYTHONCALL_EXE"] = sys.executable

# Prefer the bundled Julia in .julia/pyjuliapkg/install/bin/julia
bundled_julia = os.path.join(julia_depot, "pyjuliapkg", "install", "bin", "julia")
if os.path.isfile(bundled_julia):
    os.environ["PYTHON_JULIAPKG_EXE"] = bundled_julia
    print(f"Using bundled Julia at {bundled_julia}")
else:
    # Drop juliaup from PATH so juliacall installs into pyjuliapkg instead of
    # reusing a global juliaup copy.
    path_parts = os.environ.get("PATH", "").split(os.pathsep)
    filtered = [p for p in path_parts if "juliaup" not in p.lower()]
    if filtered != path_parts:
        os.environ["PATH"] = os.pathsep.join(filtered)
        print(
            "No bundled Julia found; removing juliaup from PATH to force local install"
        )

# Let juliacall download Julia to project-local location
# This ensures zero prerequisites - no need for system Julia or juliaup!
print("Allowing juliacall to manage Julia installation...")
print("This ensures the project is self-contained with zero prerequisites.")
print()

print(f"Julia depot: {julia_depot}")
print(f"Julia project: {env_dir}")
print(f"Python executable: {sys.executable}")
print("(CondaPkg disabled - Julia will use the conda environment Python)")
print()

want_cuda = os.environ.get("JULIA_ENABLE_CUDA") == "1"
if want_cuda:
    print("GPU support requested (JULIA_ENABLE_CUDA=1)")
    print("Note: CUDA.jl is optional and loaded at runtime when available.")
    print("It will be installed on-demand if you have a CUDA-capable GPU.")
else:
    print("GPU support not requested (JULIA_ENABLE_CUDA unset/0)")
    print("Julia will use CPU-only backends.")

# Temporarily hide Manifest.toml during juliacall import to avoid
# chicken-egg problem: Manifest references PythonCall, but depot doesn't have it yet.
# The Manifest will be properly generated during Pkg.instantiate() below.
manifest_path = os.path.join(env_dir, "Manifest.toml")
manifest_backup = None
if os.path.exists(manifest_path):
    manifest_backup = manifest_path + ".backup"
    try:
        shutil.move(manifest_path, manifest_backup)
        print("Temporarily moved Manifest.toml aside for juliacall import")
    except Exception as e:
        print(f"⚠ Could not move Manifest.toml: {e}")
        manifest_backup = None

# Import juliacall - this triggers Julia auto-install if needed
try:
    from juliacall import Main as jl

    print("✓ juliacall imported successfully")
    print()

    # Don't restore Manifest.toml - let Pkg.instantiate() generate a fresh one
    # from env/Project.toml. The backup will be cleaned up if it exists.
    if manifest_backup and os.path.exists(manifest_backup):
        try:
            os.remove(manifest_backup)
            print("Removed old Manifest.toml backup (will be regenerated)")
        except Exception as e:
            print(f"⚠ Could not remove Manifest.toml backup: {e}")

    # Check Julia version
    julia_version = jl.seval("VERSION")
    print(f"✓ Julia version: {julia_version}")
    print()

    # Get Julia executable path from juliacall
    try:
        julia_cmd = jl.seval("Base.julia_cmd()")
        # Extract executable from Cmd object
        julia_exe = (
            julia_cmd.exec[0]
            if hasattr(julia_cmd, "exec")
            else str(julia_cmd).split()[0]
        )
    except Exception:
        # Method 2: Use Sys.BINDIR
        julia_exe = jl.seval('joinpath(Sys.BINDIR, "julia")')

    print(f"Julia executable: {julia_exe}")
    print()

    # Install packages using subprocess (more robust, won't segfault Python)
    print("Installing Julia packages from Project.toml...")
    print()

    # Build Julia command
    julia_env = os.environ.copy()

    # CRITICAL: Set JULIA_DEPOT_PATH to use local .julia/ directory
    # Without this, Julia may use ~/.julia or other system depots
    julia_env["JULIA_DEPOT_PATH"] = julia_depot

    # CRITICAL: Unset JULIA_PROJECT so Pkg.activate() in Julia code can work
    # juliacall may have set this to the depot project
    julia_env.pop("JULIA_PROJECT", None)
    julia_env.pop("JULIAPKG_PROJECT", None)

    julia_env["JULIA_CONDAPKG_BACKEND"] = "Null"
    julia_env["JULIA_PYTHONCALL_EXE"] = sys.executable

    # Build Julia installation code
    # CRITICAL: Don't use "using Pkg" - it tries to load all project dependencies first!
    # Use "import Pkg" instead which doesn't load dependencies
    julia_code_parts = [
        f"""
        import Pkg

        # Activate the env/ project (not .julia/ or .julia/pyjuliapkg/)
        Pkg.activate("{env_dir}")

        println("Active project: ", Base.active_project())

        println("Resolving dependencies...")
        Pkg.resolve()
        println()
        println("Installing packages...")
        Pkg.instantiate()
        """
    ]

    # Install CUDA.jl if requested (won't add to [deps], uses temporary environment)
    if want_cuda:
        julia_code_parts.append("""
        println()
        println("Installing CUDA.jl for GPU support...")
        # Install without adding to Project.toml [deps]
        Pkg.add("CUDA"; preserve=Pkg.Types.PRESERVE_ALL)
        """)

    julia_code_parts.append("""
        println()
        println("Precompiling packages...")
        Pkg.precompile()
    """)

    # Don't verify PythonCall here - it's in a different project (depot vs env)
    # The verification will happen when scripts actually use Julia

    if want_cuda:
        julia_code_parts.append("""
        try
            using CUDA
            if CUDA.functional()
                println("  ✓ CUDA.jl (GPU functional)")
            else
                println("  ⚠ CUDA.jl installed but GPU not functional")
            end
        catch e
            println("  ⚠ CUDA.jl install failed: ", e)
        end
        """)

    julia_code = "".join(julia_code_parts)

    # Run with --project=env/ to force using env/ project instead of depot
    # This is more reliable than Pkg.activate() which can be overridden by env vars
    cmd = [
        julia_exe,
        f"--project={env_dir}",
        "-e",
        julia_code,
    ]

    def run_julia_install():
        return subprocess.run(cmd, env=julia_env, cwd=env_dir).returncode == 0

    if not run_julia_install():
        print()
        print("✗ Julia package installation failed")
        print("Retrying after cleanup (compiled cache + Manifest.toml)...")
        compiled_dir = os.path.join(julia_depot, "compiled")
        manifest_path = os.path.join(env_dir, "Manifest.toml")

        if os.path.isdir(compiled_dir):
            try:
                shutil.rmtree(compiled_dir)
                print(f"  Removed compiled cache: {compiled_dir}")
            except Exception as cleanup_err:
                print(f"  ⚠ Failed to remove compiled cache: {cleanup_err}")

        if os.path.exists(manifest_path):
            try:
                os.remove(manifest_path)
                print(f"  Removed Manifest.toml: {manifest_path}")
            except Exception as cleanup_err:
                print(f"  ⚠ Failed to remove Manifest.toml: {cleanup_err}")

        print("Retrying Julia package installation...")
        if not run_julia_install():
            print()
            print("✗ Julia package installation failed after retry")
            sys.exit(1)

    # Clean up stray pyjuliapkg directory
    stray_pyjuliapkg = os.path.join(env_dir, "pyjuliapkg")
    if os.path.isdir(stray_pyjuliapkg):
        try:
            shutil.rmtree(stray_pyjuliapkg)
            print(f"Removed stray pyjuliapkg metadata dir: {stray_pyjuliapkg}")
        except Exception as cleanup_err:
            print(f"⚠ Failed to remove stray pyjuliapkg dir: {cleanup_err}")

    print()
    print("✓ Julia packages installed successfully")
    print()

    print("=" * 80)
    print("Julia environment setup complete!")
    print("=" * 80)
    sys.exit(0)

except Exception as e:
    print(f"✗ Error: {e}", file=sys.stderr)
    print()
    print("Julia installation failed. This may be due to:")
    print("  - Network connectivity issues")
    print("  - Insufficient disk space")
    print("  - Permission issues")
    print()
    print("You can retry by running:")
    print("  make environment")
    print()
    sys.exit(1)
