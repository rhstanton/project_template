#!/usr/bin/env python
"""
Bootstrap script for customizing project_template after cloning.

This script helps you customize the template by removing unwanted languages
and optionally renaming the project.

Usage:
    python bootstrap.py --remove-julia --remove-stata
    python bootstrap.py --rename "My Research Project"
    python bootstrap.py --interactive
    python bootstrap.py --help

Examples:
    # Remove Julia support (keeps Python and Stata)
    python bootstrap.py --remove-julia

    # Remove Stata support (keeps Python and Julia)
    python bootstrap.py --remove-stata

    # Remove both (Python-only project)
    python bootstrap.py --remove-julia --remove-stata

    # Rename project
    python bootstrap.py --rename "Housing Market Analysis"

    # Interactive mode (prompts for each option)
    python bootstrap.py --interactive

    # Combine options
    python bootstrap.py --remove-stata --rename "My Project"
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


def remove_julia_files(repo_root: Path) -> None:
    """Remove Julia-specific files from the project."""
    print("\n🗑️  Removing Julia files...")
    
    files_to_remove = [
        "env/Project.toml",
        "env/scripts/runjulia",
        "env/scripts/install_julia.py",
        "env/examples/sample_julia.jl",
        "env/examples/sample_juliacall.py",
    ]
    
    for file_path in files_to_remove:
        full_path = repo_root / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"  ✓ Removed {file_path}")
        else:
            print(f"  ⚠ Not found: {file_path}")


def remove_stata_files(repo_root: Path) -> None:
    """Remove Stata-specific files from the project."""
    print("\n🗑️  Removing Stata files...")
    
    files_to_remove = [
        "env/stata-packages.txt",
        "env/scripts/runstata",
        "env/scripts/execute.ado",
        "env/examples/sample_stata.do",
    ]
    
    for file_path in files_to_remove:
        full_path = repo_root / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"  ✓ Removed {file_path}")
        else:
            print(f"  ⚠ Not found: {file_path}")


def update_python_yml(repo_root: Path, remove_julia: bool) -> None:
    """Update env/python.yml to remove Julia dependencies if requested."""
    if not remove_julia:
        return
    
    print("\n📝 Updating env/python.yml...")
    python_yml = repo_root / "env" / "python.yml"
    
    if not python_yml.exists():
        print("  ⚠ env/python.yml not found")
        return
    
    content = python_yml.read_text()
    
    # Remove juliacall from pip dependencies
    # Match the juliacall line (with indentation)
    content = re.sub(r'\n\s+- juliacall.*?\n', '\n', content)
    
    python_yml.write_text(content)
    print("  ✓ Removed juliacall dependency")


def update_env_makefile(repo_root: Path, remove_julia: bool, remove_stata: bool) -> None:
    """Update env/Makefile to remove language-specific targets."""
    if not (remove_julia or remove_stata):
        return
    
    print("\n📝 Updating env/Makefile...")
    env_makefile = repo_root / "env" / "Makefile"
    
    if not env_makefile.exists():
        print("  ⚠ env/Makefile not found")
        return
    
    content = env_makefile.read_text()
    
    if remove_julia:
        # Remove julia-install-via-python from all-env dependencies
        content = re.sub(r'\s+julia-install-via-python', '', content)
        
        # Remove the julia-install-via-python target section
        content = re.sub(
            r'\.PHONY: julia-install-via-python.*?(?=\n\.PHONY|\n#|\Z)',
            '',
            content,
            flags=re.DOTALL
        )
        print("  ✓ Removed Julia targets")
    
    if remove_stata:
        # Remove stata-env from all-env dependencies
        content = re.sub(r'\s+stata-env', '', content)
        
        # Remove the Stata section (marked with # ---------- Stata ----------)
        content = re.sub(
            r'# ---------- Stata ----------.*?(?=\n# ---|\.PHONY|\Z)',
            '',
            content,
            flags=re.DOTALL
        )
        print("  ✓ Removed Stata targets")
    
    env_makefile.write_text(content)


def update_main_makefile(repo_root: Path, remove_julia: bool, remove_stata: bool) -> None:
    """Update main Makefile to remove language-specific runners."""
    if not (remove_julia or remove_stata):
        return
    
    print("\n📝 Updating Makefile...")
    makefile = repo_root / "Makefile"
    
    if not makefile.exists():
        print("  ⚠ Makefile not found")
        return
    
    content = makefile.read_text()
    
    if remove_julia:
        # Remove JULIA runner line
        content = re.sub(r'JULIA\s*:=.*?\n', '', content)
        print("  ✓ Removed JULIA runner")
    
    if remove_stata:
        # Remove STATA runner line
        content = re.sub(r'STATA\s*:=.*?\n', '', content)
        print("  ✓ Removed STATA runner")
    
    makefile.write_text(content)


def update_readme(repo_root: Path, remove_julia: bool, remove_stata: bool, new_name: str | None) -> None:
    """Update README.md to reflect language choices and optionally rename project."""
    print("\n📝 Updating README.md...")
    readme = repo_root / "README.md"
    
    if not readme.exists():
        print("  ⚠ README.md not found")
        return
    
    content = readme.read_text()
    
    # Update title if renaming
    if new_name:
        # Replace first heading
        content = re.sub(
            r'^#\s+.*?\n',
            f'# {new_name}\n',
            content,
            count=1
        )
        print(f"  ✓ Updated title to '{new_name}'")
    
    # Update language list
    languages = ["Python 3.11"]
    if not remove_julia:
        languages.append("Julia 1.10-1.12")
    if not remove_stata:
        languages.append("Stata (optional)")
    
    lang_list = ", ".join(languages)
    
    # Update multi-language support line
    content = re.sub(
        r'- \*\*Multi-language support\*\*:.*?\n',
        f'- **Language support**: {lang_list}\n',
        content
    )
    
    if remove_julia and remove_stata:
        print("  ✓ Updated to Python-only project")
    elif remove_julia:
        print("  ✓ Updated to Python + Stata project")
    elif remove_stata:
        print("  ✓ Updated to Python + Julia project")
    
    readme.write_text(content)


def rename_project(repo_root: Path, new_name: str) -> None:
    """Rename the project throughout documentation."""
    print(f"\n📝 Renaming project to '{new_name}'...")
    
    # Update README.md
    update_readme(repo_root, False, False, new_name)
    
    # Update QUICKSTART.md
    quickstart = repo_root / "QUICKSTART.md"
    if quickstart.exists():
        content = quickstart.read_text()
        content = re.sub(
            r'^#\s+.*?\n',
            f'# {new_name} - Quick Start\n',
            content,
            count=1
        )
        quickstart.write_text(content)
        print("  ✓ Updated QUICKSTART.md")
    
    # Update shared/config.py
    config_py = repo_root / "shared" / "config.py"
    if config_py.exists():
        content = config_py.read_text()
        # Update the project name comment if it exists
        content = re.sub(
            r'# Project:.*?\n',
            f'# Project: {new_name}\n',
            content
        )
        config_py.write_text(content)
        print("  ✓ Updated shared/config.py")


def interactive_mode(repo_root: Path) -> None:
    """Run in interactive mode, prompting for each option."""
    print("\n" + "=" * 60)
    print("Project Template Bootstrap - Interactive Mode")
    print("=" * 60)
    print()
    print("This will help you customize the template for your project.")
    print()
    
    # Ask about languages
    print("Which languages do you need? (default: all)")
    use_python = True  # Always included
    use_julia = input("  Include Julia? [Y/n]: ").strip().lower() != 'n'
    use_stata = input("  Include Stata? [Y/n]: ").strip().lower() != 'n'
    
    # Ask about renaming
    print()
    rename = input("Rename project? [y/N]: ").strip().lower() == 'y'
    new_name = None
    if rename:
        new_name = input("  New project name: ").strip()
        if not new_name:
            print("  ⚠ No name provided, skipping rename")
            new_name = None
    
    # Confirm
    print()
    print("Summary of changes:")
    print(f"  - Python: ✓ (always included)")
    print(f"  - Julia: {'✓' if use_julia else '✗ (will be removed)'}")
    print(f"  - Stata: {'✓' if use_stata else '✗ (will be removed)'}")
    if new_name:
        print(f"  - Rename to: {new_name}")
    print()
    
    confirm = input("Proceed? [Y/n]: ").strip().lower()
    if confirm == 'n':
        print("Cancelled.")
        sys.exit(0)
    
    # Apply changes
    remove_julia = not use_julia
    remove_stata = not use_stata
    
    if remove_julia:
        remove_julia_files(repo_root)
        update_python_yml(repo_root, remove_julia=True)
    
    if remove_stata:
        remove_stata_files(repo_root)
    
    update_env_makefile(repo_root, remove_julia, remove_stata)
    update_main_makefile(repo_root, remove_julia, remove_stata)
    update_readme(repo_root, remove_julia, remove_stata, new_name)
    
    if new_name:
        rename_project(repo_root, new_name)
    
    print()
    print("=" * 60)
    print("✅ Bootstrap complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review the changes: git status")
    print("  2. Set up environment: make environment")
    print("  3. Run sample analysis: make all")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap project_template after cloning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--remove-julia",
        action="store_true",
        help="Remove Julia support (files, dependencies, targets)",
    )
    parser.add_argument(
        "--remove-stata",
        action="store_true",
        help="Remove Stata support (files, dependencies, targets)",
    )
    parser.add_argument(
        "--rename",
        metavar="NAME",
        help="Rename project (updates README, QUICKSTART, config.py)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode (prompts for each option)",
    )
    
    args = parser.parse_args()
    
    # Find repository root
    repo_root = Path(__file__).parent.resolve()
    
    # Interactive mode
    if args.interactive:
        interactive_mode(repo_root)
        return
    
    # Non-interactive mode
    if not any([args.remove_julia, args.remove_stata, args.rename]):
        parser.print_help()
        print()
        print("Error: No actions specified. Use --interactive or provide options.")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("Project Template Bootstrap")
    print("=" * 60)
    
    # Apply requested changes
    if args.remove_julia:
        remove_julia_files(repo_root)
        update_python_yml(repo_root, remove_julia=True)
    
    if args.remove_stata:
        remove_stata_files(repo_root)
    
    if args.remove_julia or args.remove_stata:
        update_env_makefile(repo_root, args.remove_julia, args.remove_stata)
        update_main_makefile(repo_root, args.remove_julia, args.remove_stata)
        update_readme(repo_root, args.remove_julia, args.remove_stata, args.rename)
    
    if args.rename:
        rename_project(repo_root, args.rename)
    
    print()
    print("=" * 60)
    print("✅ Bootstrap complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review the changes: git status")
    print("  2. Set up environment: make environment")
    print("  3. Run sample analysis: make all")
    print()


if __name__ == "__main__":
    main()
