#!/usr/bin/env python3
"""
compare_outputs.py

Compare current outputs with previously published outputs or a reference version.
Helps track what changed between builds.

Usage:
    python scripts/compare_outputs.py [--reference paper] [--artifacts price_base remodel_base]
"""
import argparse
import hashlib
import sys
from pathlib import Path
import difflib
import subprocess


def sha256_file(filepath):
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def compare_pdfs(file1, file2):
    """Compare two PDF files."""
    if not file1.exists() or not file2.exists():
        return None
    
    hash1 = sha256_file(file1)
    hash2 = sha256_file(file2)
    
    if hash1 == hash2:
        return "identical"
    else:
        # Try to get page count or other metadata
        try:
            result1 = subprocess.run(
                ["pdfinfo", str(file1)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            result2 = subprocess.run(
                ["pdfinfo", str(file2)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result1.returncode == 0 and result2.returncode == 0:
                # Extract page counts
                pages1 = [line for line in result1.stdout.split('\n') if 'Pages:' in line]
                pages2 = [line for line in result2.stdout.split('\n') if 'Pages:' in line]
                
                return {
                    "status": "different",
                    "hash1": hash1[:8],
                    "hash2": hash2[:8],
                    "metadata1": pages1[0] if pages1 else "N/A",
                    "metadata2": pages2[0] if pages2 else "N/A",
                }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return {
            "status": "different",
            "hash1": hash1[:8],
            "hash2": hash2[:8],
        }


def compare_text_files(file1, file2):
    """Compare two text files and show diff."""
    if not file1.exists() or not file2.exists():
        return None
    
    with open(file1) as f:
        lines1 = f.readlines()
    
    with open(file2) as f:
        lines2 = f.readlines()
    
    if lines1 == lines2:
        return "identical"
    
    # Generate unified diff
    diff = list(difflib.unified_diff(
        lines1,
        lines2,
        fromfile=str(file1),
        tofile=str(file2),
        lineterm='',
    ))
    
    return {
        "status": "different",
        "lines_changed": len([line for line in diff if line.startswith('+') or line.startswith('-')]),
        "diff_preview": '\n'.join(diff[:20]),  # First 20 lines
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference",
        default="paper",
        help="Reference directory to compare against (default: paper)",
    )
    parser.add_argument(
        "--artifacts",
        nargs="*",
        help="Specific artifacts to compare (default: all)",
    )
    parser.add_argument(
        "--current-dir",
        default="output",
        help="Current output directory (default: output)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed diff output",
    )
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent
    current_dir = repo_root / args.current_dir
    reference_dir = repo_root / args.reference
    
    if not current_dir.exists():
        print(f"❌ Current directory not found: {current_dir}")
        print("   Run 'make all' first to build outputs")
        return 1
    
    if not reference_dir.exists():
        print(f"❌ Reference directory not found: {reference_dir}")
        return 1
    
    # Determine which artifacts to compare
    if args.artifacts:
        artifacts = args.artifacts
    else:
        # Auto-detect from current output
        fig_dir = current_dir / "figures"
        if fig_dir.exists():
            artifacts = [p.stem for p in fig_dir.glob("*.pdf")]
        else:
            print(f"❌ No figures found in {fig_dir}")
            return 1
    
    print(f"Comparing outputs: {current_dir} vs {reference_dir}")
    print(f"Artifacts: {', '.join(artifacts)}")
    print()
    
    all_identical = True
    
    for artifact in artifacts:
        print(f"{'='*60}")
        print(f"Artifact: {artifact}")
        print(f"{'='*60}")
        
        # Compare figure
        current_fig = current_dir / "figures" / f"{artifact}.pdf"
        ref_fig = reference_dir / "figures" / f"{artifact}.pdf"
        
        print(f"\n📊 Figure: {artifact}.pdf")
        if not current_fig.exists():
            print(f"   ⚠️  Current version not found")
        elif not ref_fig.exists():
            print(f"   ⚠️  Reference version not found (new artifact?)")
        else:
            result = compare_pdfs(current_fig, ref_fig)
            if result == "identical":
                print(f"   ✅ Identical")
            elif isinstance(result, dict):
                print(f"   ❌ Different")
                print(f"      Current hash:   {result['hash1']}...")
                print(f"      Reference hash: {result['hash2']}...")
                if 'metadata1' in result:
                    print(f"      Current:   {result['metadata1']}")
                    print(f"      Reference: {result['metadata2']}")
                all_identical = False
        
        # Compare table
        current_tbl = current_dir / "tables" / f"{artifact}.tex"
        ref_tbl = reference_dir / "tables" / f"{artifact}.tex"
        
        print(f"\n📋 Table: {artifact}.tex")
        if not current_tbl.exists():
            print(f"   ⚠️  Current version not found")
        elif not ref_tbl.exists():
            print(f"   ⚠️  Reference version not found (new artifact?)")
        else:
            result = compare_text_files(current_tbl, ref_tbl)
            if result == "identical":
                print(f"   ✅ Identical")
            elif isinstance(result, dict):
                print(f"   ❌ Different ({result['lines_changed']} lines changed)")
                all_identical = False
                
                if args.verbose and result['diff_preview']:
                    print(f"\n   Diff preview:")
                    for line in result['diff_preview'].split('\n'):
                        print(f"   {line}")
        
        print()
    
    print(f"{'='*60}")
    if all_identical:
        print("✅ All outputs identical to reference")
        return 0
    else:
        print("⚠️  Some outputs differ from reference")
        print("\nTo see detailed diffs for tables:")
        print(f"  diff {current_dir}/tables/<artifact>.tex {reference_dir}/tables/<artifact>.tex")
        print("\nTo visually compare PDFs:")
        print(f"  diff-pdf {current_dir}/figures/<artifact>.pdf {reference_dir}/figures/<artifact>.pdf")
        return 0  # Not an error, just informational


if __name__ == "__main__":
    sys.exit(main())
