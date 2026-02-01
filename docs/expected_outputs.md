# Expected Outputs Checklist

After running `make all`, you should have **4 files** from 2 analyses:
- 2 figures (`.pdf` in `output/figures/`)
- 2 tables (`.tex` in `output/tables/`)
- 2 provenance records (`.yml` in `output/provenance/`)

---

## Quick Verification

```bash
# Run this after make all:
make test-outputs

# Or manually check:
ls -1 output/figures/*.pdf | wc -l    # Should be 2
ls -1 output/tables/*.tex | wc -l     # Should be 2
ls -1 output/provenance/*.yml | wc -l # Should be 2
```

---

## Figures (output/figures/) - 2 files

### Price Base Analysis
- [ ] **`price_base.pdf`** - Main price effects event study
  - Event study plot with coefficients and confidence intervals
  - Time on x-axis: -4 to +4 years (relative to fire)
  - Y-axis: Treatment effect on log price
  - Should show negative effect around t=0
  - Blue line with shaded confidence interval
  - Horizontal reference line at y=0
  - Approximate size: 10-20 KB

### Remodeling Base Analysis
- [ ] **`remodel_base.pdf`** - Main remodeling effects event study
  - Event study plot showing remodeling activity
  - Time on x-axis: -4 to +4 years
  - Y-axis: Treatment effect on square footage or remodeling indicator
  - Should show positive spike near t=0
  - Red line with confidence interval
  - Approximate size: 10-20 KB

---

## Tables (output/tables/) - 2 files

### Price Base Analysis
- [ ] **`price_base.tex`** - LaTeX table of DiD regression results
  - Contains treatment effect coefficients for each time period
  - Standard errors in parentheses
  - Significance stars (*, **, ***)
  - R-squared and observation count
  - Fixed effects indicators
  - Can be directly `\input{}` into LaTeX document
  - Approximate size: <1 KB

### Remodeling Base Analysis
- [ ] **`remodel_base.tex`** - LaTeX table of remodeling regression results
  - Similar structure to price table
  - Treatment effects over time
  - Statistical significance indicators
  - Model diagnostics
  - Approximate size: <1 KB

---

## Provenance Records (output/provenance/) - 2 files

### Price Base Provenance
- [ ] **`price_base.yml`** - Build metadata for price analysis
  - Git commit hash
  - Build timestamp
  - Input data SHA256 checksum
  - Output file SHA256 checksums
  - Command that was run
  - Approximate size: <1 KB

### Remodeling Base Provenance
- [ ] **`remodel_base.yml`** - Build metadata for remodeling analysis
  - Same structure as price provenance
  - Links outputs to exact code version and data
  - Approximate size: <1 KB

---

## Sample Output Contents

### Example Figure (price_base.pdf)

**Visual description:**
```
      │
  0.2 ├─────────────────────────────
      │         ╱╲
  0.1 ├────────╱  ╲────────────────
      │       ╱    ╲
  0.0 ├──────┼─────▼───────────────
      │     ╱       ╲╲
 -0.1 ├────╱─────────╲──────────────
      │   ╱           ╲╲
 -0.2 ├──╱─────────────╲───────────
      │ ╱               ╲╲
 -0.3 ├╱─────────────────╲─────────
      │                   ╲
      └────────────────────────────
       -4  -2   0   2   4
           Time to Fire (years)
```

Event study showing price drop at fire event (t=0) with recovery.

---

### Example Table (price_base.tex)

```latex
\begin{tabular}{lcc}
\hline\hline
 & (1) & (2) \\
\hline
Treatment $\times$ t=-4 & 0.021 & 0.019 \\
 & (0.015) & (0.014) \\
Treatment $\times$ t=-3 & 0.012 & 0.010 \\
 & (0.013) & (0.012) \\
... [additional rows] ...
Treatment $\times$ t=0 & -0.251*** & -0.248*** \\
 & (0.018) & (0.017) \\
... [post-treatment rows] ...
\hline
Property FE & Yes & Yes \\
Year FE & Yes & Yes \\
Observations & 50 & 50 \\
R-squared & 0.847 & 0.851 \\
\hline\hline
\end{tabular}
```

---

### Example Provenance (price_base.yml)

```yaml
artifact: price_base
built_at_utc: '2026-01-17T12:34:56+00:00'
command:
  - python
  - build_price_base.py
  - --data
  - data/housing_panel.csv
  - --out-fig
  - output/figures/price_base.pdf
  - --out-table
  - output/tables/price_base.tex
  - --out-meta
  - output/provenance/price_base.yml
git:
  is_git_repo: true
  commit: abc123def456789...
  branch: main
  dirty: false
  ahead: 0
  behind: 0
inputs:
  - path: /full/path/to/data/housing_panel.csv
    sha256: 48917387ef250e81b4ec8a43e25a01f512a5c00c857614f82fee0729e48f91ce
    bytes: 325
    mtime: 1737115200.0
outputs:
  - path: /full/path/to/output/figures/price_base.pdf
    sha256: 3855687dcbeff3673679f5bb05a2019f94987f19e1c6d8fc5c2284fec73f9025
    bytes: 12482
    mtime: 1737115210.0
  - path: /full/path/to/output/tables/price_base.tex
    sha256: 958062fbe20ff4dee6ad0ae6af81fc45c8c4c2408418fabee0810fb4bc5a19bc
    bytes: 193
    mtime: 1737115210.0
```

---

## Verification Commands

### Check All Files Exist

```bash
# Using make target:
make test-outputs

# Manual check:
test -f output/figures/price_base.pdf && echo "✓ Price figure" || echo "✗ Missing"
test -f output/figures/remodel_base.pdf && echo "✓ Remodel figure" || echo "✗ Missing"
test -f output/tables/price_base.tex && echo "✓ Price table" || echo "✗ Missing"
test -f output/tables/remodel_base.tex && echo "✓ Remodel table" || echo "✗ Missing"
```

### Check File Sizes Are Reasonable

```bash
# Figures should be 10-100 KB
find output/figures -name "*.pdf" -size +1k -size -200k | wc -l
# Should be 2

# Tables should be <10 KB
find output/tables -name "*.tex" -size +0 -size -20k | wc -l
# Should be 2
```

### Verify Checksums Match Provenance

```bash
# Check price figure:
sha256sum output/figures/price_base.pdf
# Compare with hash in output/provenance/price_base.yml

# Or use grep:
grep "price_base.pdf" output/provenance/price_base.yml -A 2
```

### Check PDF Files Are Valid

```bash
# PDFs should be openable:
file output/figures/*.pdf
# Should say "PDF document"

# Can also try opening:
open output/figures/price_base.pdf  # macOS
xdg-open output/figures/price_base.pdf  # Linux
```

### Check LaTeX Tables Are Valid

```bash
# Tables should contain \begin{tabular}:
grep "begin{tabular}" output/tables/*.tex
# Should find both tables

# Check for common issues:
grep "NaN\|inf\|Error" output/tables/*.tex
# Should return nothing
```

---

## Expected Content Characteristics

### Figures Should Have:
- ✅ Axis labels and title
- ✅ Legend (if multiple series)
- ✅ Confidence intervals shaded
- ✅ Reference line at y=0
- ✅ Clear time axis
- ✅ Professional appearance (suitable for publication)

### Tables Should Have:
- ✅ Valid LaTeX syntax
- ✅ Header row with column labels
- ✅ Coefficient estimates
- ✅ Standard errors in parentheses
- ✅ Significance stars (*, **, ***)
- ✅ Model diagnostics (R², N)
- ✅ Horizontal rules (\hline)

### Provenance Should Have:
- ✅ Git commit hash (40 characters)
- ✅ Timestamp in ISO format
- ✅ Input file SHA256 (64 hex characters)
- ✅ Output file SHA256s
- ✅ Complete command including all arguments
- ✅ Git status (dirty, ahead, behind)

---

## Common Issues and Solutions

### Missing Output Files

**If files don't exist:**
```bash
# Check logs:
cat output/logs/price_base.log

# Rebuild from scratch:
make clean
make price_base
```

### Incorrect File Sizes

**If PDFs are 0 bytes or unusually small:**
- Check logs for matplotlib errors
- Ensure data loaded correctly
- Verify no exceptions during plotting

**If PDFs are >1 MB:**
- May indicate very complex plots or embedded data
- Usually not an issue, but check content

### Provenance Missing Data

**If provenance files incomplete:**
- Check that `repro_tools` is installed and working
- Ensure git repository initialized
- Verify data files exist when analysis runs

### Checksum Mismatches

**If checksums don't match between runs:**
- This is expected if data changed
- Check git status of data files
- Review provenance to see when file changed

---

## Reference Output Characteristics

**From our test runs (your results should be similar):**

| File | Size | Lines (if text) | Key Content |
|------|------|-----------------|-------------|
| `price_base.pdf` | ~12 KB | - | Event study plot, 9 time points |
| `remodel_base.pdf` | ~11 KB | - | Event study plot, 9 time points |
| `price_base.tex` | ~193 bytes | ~25 | LaTeX table, 2 columns |
| `remodel_base.tex` | ~190 bytes | ~25 | LaTeX table, 2 columns |

**Note:** Exact sizes will vary based on:
- Figure resolution/complexity
- Number of data points
- Table formatting
- Platform differences in PDF generation

---

## For Journal Editors

**After running `make all`, verify outputs with:**

```bash
make test-outputs
```

**Expected terminal output:**
```
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
```

**If any ✗ appear:** See [docs/troubleshooting.md](troubleshooting.md) or contact authors.

---

## Adding New Outputs

**When you add a new analysis, update this checklist:**

1. Add entry to "Figures" or "Tables" section above
2. Describe what the output should look like
3. Add verification command
4. Update file counts in summary

**Template:**
```markdown
### Your New Analysis
- [ ] **`your_analysis.pdf`** - Description
  - What it shows
  - Expected appearance
  - Approximate size
```

---

**See also:**
- [paper_output_mapping.md](paper_output_mapping.md) - Paper figures/tables → output files
- [journal_editor_readme.md](journal_editor_readme.md) - Quick replication guide
- [provenance.md](provenance.md) - Provenance system documentation

---

**Last updated:** January 17, 2026
