# Data Documentation

**Complete documentation of all datasets used in this project.**

---

## Quick Reference

| File | Variables | Observations | Source | Panel? |
|------|-----------|--------------|--------|--------|
| `housing_panel.csv` | 8 | 50 | Simulated | Yes (10 units × 5 years) |

**Total disk space:** ~0.3 KB (sample data only)

---

## Data Dictionary

### housing_panel.csv

**Description:** Sample housing panel data demonstrating remodeling and price dynamics

**Unit of observation:** Property-year

**Time period:** 5 years

**Panel structure:** Balanced panel of 10 properties over 5 years (50 observations)

#### Variables

| Variable | Type | Description | Units | Range | Missing Values |
|----------|------|-------------|-------|-------|----------------|
| `property_id` | int | Unique property identifier | - | 1-10 | None |
| `year` | int | Year of observation | - | 1-5 | None |
| `fire_exposed` | int | Property exposed to fire (1=yes, 0=no) | Binary | 0-1 | None |
| `fire_year` | int | Year when fire occurred (0 if no fire) | - | 0-5 | None |
| `time_to_fire` | int | Years relative to fire (0 = fire year) | Years | -4 to 4 | None |
| `sqft` | float | Property size | Square feet | 800-2200 | None |
| `price` | float | Property value | Thousands $ | 200-500 | None |
| `remodeled` | int | Property remodeled this year (1=yes) | Binary | 0-1 | None |

#### Variable Construction

**`time_to_fire`**: Calculated as `year - fire_year` for fire-exposed properties
- Negative values: years before fire
- 0: fire year
- Positive values: years after fire
- For non-fire-exposed properties: time relative to a pseudo fire year

**`fire_exposed`**: Indicator for treatment group (properties affected by fire)

#### Data Quality Notes

- **No missing values:** This is clean sample data
- **No outliers:** All values within realistic ranges
- **Balanced panel:** All properties observed in all years

---

## Data Sources

### Sample Data (Simulated)

**File:** `housing_panel.csv`

**Source:** Simulated data for template demonstration

**Generation:** See `scripts/generate_sample_data.py` (if you create this)

**Purpose:** 
- Demonstrates analysis workflow
- Allows testing without proprietary data
- Shows expected data structure

**Limitations:**
- Not real data
- Simplified dynamics
- Not suitable for actual research

**To replace with your data:** 
1. Replace `data/housing_panel.csv` with your actual data
2. Ensure same variable names OR update analysis scripts
3. Update this documentation

---

## Data Access and Restrictions

**Current data:** Simulated sample data (public domain, no restrictions)

**For proprietary data projects:**
- See `DATA_AVAILABILITY.md` for access instructions
- Restricted data files should be symlinked to `data/raw/`
- Processed data goes in `data/processed/`

---

## Suggested Directory Structure for Full Projects

For projects with multiple data sources and processing steps:

```
data/
├── README.md              # This file
├── DATA_README.md         # Detailed documentation (this file)
├── CHECKSUMS.txt          # SHA256 checksums
├── raw/                   # Original data (symlinks to external)
│   ├── .gitignore         # Exclude from git
│   ├── README.md          # Source documentation
│   └── [data files]       # Symlinks to external storage
├── processed/             # Analysis-ready datasets
│   ├── .gitignore         # Exclude large files
│   ├── README.md          # Processing notes
│   └── [data files]       # Output of data-construction/
├── sample/                # Sample data for testing
│   └── [small datasets]   # Included in git
└── housing_panel.csv      # Main input (sample data)
```

---

## Data Processing Pipeline

**If you build datasets from raw sources:**

### Stage 1: Import Raw Data

**Scripts:** `data-construction/01_import_*.py`

**Inputs:** `data/raw/*`

**Outputs:** `data/processed/*_raw.csv`

**Purpose:** Import, validate, initial cleaning

### Stage 2: Clean and Filter

**Scripts:** `data-construction/02_clean_*.py`

**Inputs:** `data/processed/*_raw.csv`

**Outputs:** `data/processed/*_clean.csv`

**Purpose:** 
- Remove duplicates
- Filter outliers
- Handle missing values
- Standardize formats

### Stage 3: Merge and Construct Variables

**Scripts:** `data-construction/03_merge_*.py`

**Inputs:** Multiple `*_clean.csv` files

**Outputs:** `data/processed/housing_panel.csv` (final analysis dataset)

**Purpose:**
- Merge across sources
- Create derived variables
- Construct panel structure

**To run full pipeline:**
```bash
cd data-construction
make all
```

---

## Summary Statistics

### housing_panel.csv

```
Variable     N    Mean     Std     Min      25%     50%     75%      Max
-----------  --   ------   ----   ------   ------  ------  ------   ------
sqft         50   1497.0   418.2   800.0   1150.0  1500.0  1850.0   2200.0
price        50   349.2    87.6    200.0    280.0   350.0   420.0    500.0
fire_exposed 50   0.4      0.5     0        0       0       1        1
remodeled    50   0.2      0.4     0        0       0       0        1
```

**To regenerate:** Run `make price_base` and see `output/tables/price_base_sumstats.tex`

---

## Data Quality Checks

### Validation Steps Applied

- [x] No duplicates (checked by property_id + year)
- [x] No missing values
- [x] Variable ranges sensible
- [x] Panel balanced
- [x] Time ordering correct
- [ ] Cross-referenced with external sources (if applicable)
- [ ] Verified merges (if applicable)

### Known Issues

**None for sample data**

**For real data projects, document:**
- Measurement errors
- Coding changes over time
- Merge discrepancies
- Any data quality concerns

---

## Data Versioning

**Current version:** 1.0 (2026-01-17)

**Version history:**
- 1.0 (2026-01-17): Initial sample data for template

**For projects with evolving data:**
- Tag data versions in git
- Document changes in CHANGELOG.md
- Keep old provenance records for comparison

---

## Reproducibility

### Verifying Data Integrity

```bash
# Check checksums:
sha256sum -c data/CHECKSUMS.txt

# Or check individual file:
sha256sum data/housing_panel.csv
# Expected: 48917387ef250e81b4ec8a43e25a01f512a5c00c857614f82fee0729e48f91ce
```

### Provenance Tracking

Every analysis run records input data checksums:

```bash
# Check what data was used for a specific output:
cat output/provenance/price_base.yml
# Shows SHA256 hash of data/housing_panel.csv
```

See `docs/provenance.md` for complete explanation.

---

## Variable Naming Conventions

**For consistency across analyses:**

- `_id`: Identifiers (property_id, year)
- `_flag`: Binary indicators (fire_exposed)
- `_date`: Dates (in ISO format if applicable)
- `_year`: Year variables
- `log_*`: Log-transformed variables
- `d_*`: First differences
- `i_*`: Interactions

**Update this section for your project**

---

## Missing Data Handling

**Current data:** No missing values

**For real projects, document:**

### Missing Value Codes

- `-999`: Not applicable
- `-998`: Refused to answer
- `-997`: Don't know
- `NaN`: Missing for unknown reason

### Imputation Strategy

- [Describe how missing values were handled]
- [Document any imputation methods]
- [Note robustness checks]

---

## Data Cleaning Decisions

**For real projects, document major decisions:**

### Outlier Treatment

- **Price:** Winsorized at 1st and 99th percentile
- **Size:** Dropped properties <500 or >10,000 sqft
- **Rationale:** [explain]

### Sample Restrictions

- **Time period:** [start] to [end]
- **Geographic scope:** [specify]
- **Inclusion criteria:** [list]

### Variable Transformations

- **Log transformations:** price → log_price
- **Standardization:** [if applicable]
- **Categorization:** [if applicable]

---

## Citation

If you use this data structure/template, cite:

```bibtex
@data{template2026,
  title = {Reproducible Research Template},
  year = {2026},
  url = {https://github.com/yourusername/project_template}
}
```

For your actual data sources, add proper citations in DATA_AVAILABILITY.md

---

## Questions?

**Data questions:** [Your email]

**Technical issues:** See `docs/troubleshooting.md`

**Access requests:** See `DATA_AVAILABILITY.md`

---

**See also:**
- `DATA_AVAILABILITY.md` - How to obtain data
- `CHECKSUMS.txt` - File verification
- `docs/provenance.md` - Data provenance tracking
- `data-construction/` - How data was built (if applicable)
