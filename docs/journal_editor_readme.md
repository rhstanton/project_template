# Quick Guide for Journal Editors and Reviewers

**One-page guide to replicate the results from [Your Paper Title]**

---

## ⚠️ IMPORTANT: Package Contents

**This replication package excludes:**

- `data-construction/` - Scripts that process proprietary raw data (if applicable)
- `notes/` - Authors' working notes
- `paper/` - Separate LaTeX repository
- Development files (.github/, .vscode/, etc.)

**See [JOURNAL_EXCLUDE](../JOURNAL_EXCLUDE) for the complete list.**

The package is **self-contained** with all data needed for replication.

---

# START HERE: Replication in 4 Steps

| Step | Command | What it does | Time |
|------|---------|--------------|------|
| 1 | `make environment` | Installs all dependencies | ~10 min |
| 2 | `make verify` | Quick smoke test | ~1 min |
| 3 | `make all` | Runs all analyses | ~5 min |
| 4 | `make test-outputs` | Verifies all expected outputs exist | ~5 sec |

**If you see any errors:**
- See [docs/troubleshooting.md](troubleshooting.md)
- Or contact: [Your Name], [Your Institution] (your.email@institution.edu)

---

## TL;DR: 3 Commands to Replicate Everything

```bash
make environment    # Setup (10 min, one-time only)
make verify         # Quick test (~1 min)
make all            # Run all analyses (~5 min)
```

**Expected outputs:** 4 files (2 figures + 2 tables) in `output/` directories

---

## What Success Looks Like

Here's what you should see at each step when everything works correctly.

### Step 1: `make environment` (Success)

```
$ make environment

==========================================================
Setting up software environment...
==========================================================

Checking for conda/mamba/micromamba...
  ✓ Found conda at /usr/local/bin/conda

Creating Python environment...
  Solving environment: done
  ✓ Python environment created at .env/

Installing Julia via juliacall...
  ✓ Julia ready at .julia/pyjuliapkg/

==========================================================
✓ Environment ready!
==========================================================

Python 3.11:    .env/bin/python
Julia:          .julia/pyjuliapkg/install/bin/julia

Next: make all (to build all artifacts)
```

**Key indicators:** Look for `✓` marks and "Environment ready!" at the end.

---

### Step 2: `make verify` (Success)

```
$ make verify

========================================
  Quick Verification (~1 minute)
========================================

1. Checking Python environment...
   Python 3.11.x ✓

2. Checking key packages...
   pandas ✓
   matplotlib ✓
   pyyaml ✓
   juliacall ✓

3. Checking data availability...
   data/housing_panel.csv ✓
   SHA256: 48917387... ✓

4. Running minimal import test...
   scripts.provenance ✓

========================================
  ✓ Verification Complete
========================================

Environment is ready. Next steps:
  make all              # Run all analyses
  make price_base       # Run single analysis
```

**Key indicators:** All checks show `✓`, ends with "Verification Complete".

---

### Step 3: `make all` (Success)

```
$ make all
Building price_base...
  Loading data: data/housing_panel.csv (50 rows)
  Generating figure: output/figures/price_base.pdf
  Generating table: output/tables/price_base.tex
  Writing provenance: output/provenance/price_base.yml
  ✓ price_base complete

Building remodel_base...
  Loading data: data/housing_panel.csv (50 rows)
  Generating figure: output/figures/remodel_base.pdf
  Generating table: output/tables/remodel_base.tex
  Writing provenance: output/provenance/remodel_base.yml
  ✓ remodel_base complete

==========================================
✓ All analyses complete!
==========================================

Results:
  - Figures: output/figures/
  - Tables:  output/tables/
  - Provenance: output/provenance/
```

**Key indicators:** Shows row counts, ends with "All analyses complete!"

---

### Step 4: `make test-outputs` (Success)

```
$ make test-outputs
Verifying all expected outputs exist...

Output directories:
  ✓ output/figures/
  ✓ output/tables/
  ✓ output/provenance/

Expected files:
  ✓ output/figures/price_base.pdf
  ✓ output/figures/remodel_base.pdf
  ✓ output/tables/price_base.tex
  ✓ output/tables/remodel_base.tex

All expected outputs present!

For detailed output descriptions, see docs/expected_outputs.md
```

**Key indicators:** All files show `✓`.

---

### Final Check: Count Your Outputs

```bash
$ ls output/figures/*.pdf | wc -l
2

$ ls output/tables/*.tex | wc -l
2
```

**Expected:** 2 PDF figures, 2 TEX tables.

---

## What Gets Produced

### Main Results

| Paper Exhibit | Output File | Make Target | Description |
|---------------|-------------|-------------|-------------|
| Figure 1: Price Effects | `output/figures/price_base.pdf` | `make price_base` | Event study of house prices |
| Figure 2: Remodeling | `output/figures/remodel_base.pdf` | `make remodel_base` | Remodeling activity |
| Table 1: Price Coefficients | `output/tables/price_base.tex` | `make price_base` | DiD regression results |
| Table 2: Remodeling Coefficients | `output/tables/remodel_base.tex` | `make remodel_base` | DiD regression results |

**Complete mapping:** See [paper_output_mapping.md](paper_output_mapping.md) for all figures and tables

---

## System Requirements

**Software:**

- Python 3.11 (installed automatically via `make environment`)
- Julia 1.10+ (installed automatically via juliacall)
- GNU Make 4.3+ (on macOS: `brew install make`, then use `gmake`)

**Hardware:**

- RAM: 8 GB minimum (16 GB recommended)
- Disk: 5 GB free space
- Time: ~15 minutes total (10 min setup + 5 min execution)

**Platforms:**

- ✅ Linux (tested on Ubuntu 22.04)
- ✅ macOS 11+ (use `gmake` instead of `make`)
- ⚠️  Windows (use WSL 2)

---

## Quick Verification

**Check all outputs exist:**
```bash
make test-outputs
```

**Verify data integrity:**
```bash
sha256sum -c data/CHECKSUMS.txt
```

**Check provenance records:**
```bash
cat output/provenance/price_base.yml
# Shows exact git commit, data checksums, build time
```

---

## Output Verification

After running `make all`, all outputs should exist and match the following structure:

```
output/
├── figures/
│   ├── price_base.pdf      # Event study plot
│   └── remodel_base.pdf    # Event study plot
├── tables/
│   ├── price_base.tex      # LaTeX table
│   └── remodel_base.tex    # LaTeX table
└── provenance/
    ├── price_base.yml      # Build metadata
    └── remodel_base.yml    # Build metadata
```

For detailed descriptions of each output, see [expected_outputs.md](expected_outputs.md).

---

## If Something Goes Wrong

### Common Issues

**1. "conda: command not found"**
```bash
# Auto-installs during make environment
# Or manually install: https://docs.conda.io/en/latest/miniconda.html
```

**2. "make: *** No rule to make target 'all'"**
```bash
# Your make is too old (< 4.3)
make --version
# On macOS: brew install make; use gmake
# On Linux: sudo apt install make
```

**3. Build fails with import errors**
```bash
# Environment not activated properly
make clean
make environment
make all
```

### Check Logs

```bash
# Logs are written to output/logs/
ls output/logs/
cat output/logs/price_base.log
```

### Clear and Retry

```bash
make clean          # Remove outputs
make environment    # Reinstall environment
make all            # Rebuild everything
```

### Get Help

- **Quick issues:** See [docs/troubleshooting.md](troubleshooting.md)
- **Data questions:** See [DATA_AVAILABILITY.md](../DATA_AVAILABILITY.md)
- **Technical details:** See [README.md](../README.md)
- **Contact:** [Your Name], [Institution] (your.email@institution.edu)

---

## Understanding the Code Structure

```
project_template/
├── build_price_base.py      # Analysis script (well-commented)
├── build_remodel_base.py    # Analysis script
├── data/
│   └── housing_panel.csv    # Input data
├── scripts/
│   └── provenance.py        # Provenance tracking
├── output/                  # All results go here
│   ├── figures/             # PDF plots
│   ├── tables/              # LaTeX tables
│   └── provenance/          # Build metadata
└── Makefile                 # Build orchestration
```

**Key insight:** Each `build_*.py` script:

1. Loads data from `data/`
2. Generates one figure + one table
3. Records full provenance (git state, data checksums, timestamps)

---

## Technical Notes

**Provenance Tracking:** Every output is linked to:

- Exact git commit that generated it
- SHA256 checksums of input data
- Timestamp of generation
- Full command that was run

**Reproducibility:** 

- Random seeds are fixed (if applicable)
- All package versions pinned
- Floating point differences across systems are negligible

**Caching:** Not used in this template (each run is fresh)

---

## Replication Steps in Detail

### 1. Environment Setup (One-Time)

```bash
make environment
```

This installs:
- Python 3.11 with conda
- Required packages: pandas, matplotlib, pyyaml, juliacall
- Julia 1.10+ via juliacall
- All in local `.env/` and `.julia/` directories (no global changes)

### 2. Quick Verification

```bash
make verify
```

Tests that:
- Python environment is accessible
- Required packages are installed
- Data files are present and valid
- Basic imports work

### 3. Run Analyses

```bash
make all              # All analyses
# Or individual:
make price_base       # Just price analysis
make remodel_base     # Just remodeling analysis
```

Each analysis:

- Reads data from `data/housing_panel.csv`
- Performs calculations
- Generates figure (PDF) and table (LaTeX)
- Records provenance

### 4. Verify Outputs

```bash
make test-outputs
```

Checks that all expected files were created.

### 5. Inspect Results

```bash
# View figures:
open output/figures/price_base.pdf

# View tables:
cat output/tables/price_base.tex

# Check provenance:
cat output/provenance/price_base.yml
```

---

## Alternative: Step-by-Step Manual Execution

**If you prefer to run commands manually:**

```bash
# 1. Setup
make environment

# 2. Activate environment (optional - scripts use wrappers)
conda activate .env

# 3. Run individual analysis
env/scripts/runpython build_price_base.py \
  --data data/housing_panel.csv \
  --out-fig output/figures/price_base.pdf \
  --out-table output/tables/price_base.tex \
  --out-meta output/provenance/price_base.yml

# 4. Check output
ls -lh output/figures/price_base.pdf
```

---

## Questions?

1. **Quick issues:** See [docs/troubleshooting.md](troubleshooting.md)
2. **Data access:** See [DATA_AVAILABILITY.md](../DATA_AVAILABILITY.md)
3. **Full documentation:** See [README.md](../README.md)
4. **Code details:** See inline comments in `build_*.py` scripts

---

## Comparison with Paper

**Figure/Table Numbers:** See [paper_output_mapping.md](paper_output_mapping.md) for exact mapping between paper exhibits and output files.

**Numerical Differences:** Should be <0.001% due to floating point precision across platforms. See provenance records for exact values used in paper.

**Sample vs. Full Data:** This package uses sample data. Results are qualitatively similar but not numerically identical to paper (which uses full proprietary data).

---

**Last updated:** January 17, 2026  
**Contact:** [Your Name], [Institution] (your.email@institution.edu)

---

**Thank you for replicating our work!** 

If you encounter any issues, please let us know so we can improve this package.
