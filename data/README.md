# Data Directory

This directory contains input data for analysis scripts.

## 📚 Documentation

For comprehensive data documentation, see:
- **[DATA_README.md](DATA_README.md)** - Complete data dictionary with variable descriptions
- **[CHECKSUMS.txt](CHECKSUMS.txt)** - SHA256 checksums for data verification
- **[../DATA_AVAILABILITY.md](../DATA_AVAILABILITY.md)** - Data availability statement for journal submission

## Current Structure

```
data/
├── housing_panel.csv    # Sample housing dataset (tracked in git)
├── CHECKSUMS.txt        # SHA256 checksums for verification
└── DATA_README.md       # Comprehensive data documentation
```

## For Your Project

Depending on your data needs, you can organize this directory in several ways:

### Option 1: Simple (Small Datasets)

Keep all data in `data/` and track in git:

```
data/
├── dataset1.csv
├── dataset2.csv
└── README.md
```

**When to use:** Datasets < 10MB that can be publicly shared

### Option 2: External Data (Large Datasets)

Use symlinks to external storage:

```
data/
├── raw/              # Symlinks to external data (not in git)
├── processed/        # Generated datasets (not in git)
└── sample/           # Small sample data (in git for testing)
```

**Setup:**
```bash
cd data/raw
ln -s /mnt/external/large_dataset/ .
```

**Gitignore:**
```gitignore
# In .gitignore:
data/raw/*
!data/raw/.gitignore
!data/raw/README.md

data/processed/*
!data/processed/.gitignore
!data/processed/README.md
```

**When to use:** Datasets > 100MB, proprietary data, or data requiring licenses

### Option 3: Data Construction Pipeline

Separate raw data from analysis-ready data:

```
data/
├── raw/              # Original external data
├── processed/        # Cleaned, analysis-ready data
└── README.md

data-construction/    # Scripts to transform raw → processed
├── 01_import.py
├── 02_clean.py
└── 03_merge.py
```

**When to use:** Complex data cleaning/transformation pipelines

## Switching Data Sources

Analysis scripts can accept `--data` argument pointing to different files:

```bash
# Use sample data
make price_base DATA=data/sample/housing_panel_sample.csv

# Use full data
make price_base DATA=data/processed/housing_panel.csv
```

Or set in Makefile:
```makefile
DATA ?= data/housing_panel.csv  # Default
# Override: make all DATA=data/alternate.csv
```

## Data Documentation

For each dataset, document:
- **Source:** Where did it come from?
- **Date:** When was it downloaded/created?
- **Schema:** What columns exist?
- **License:** Can it be shared?
- **Size:** How large is it?

Consider creating a data dictionary file or adding a `CODEBOOK.md`.

## Example: Multiple Datasets

If your project uses multiple data files:

```makefile
# In Makefile:
HOUSING_DATA := data/housing_panel.csv
CENSUS_DATA := data/census_tracts.csv
FIRE_DATA := data/fire_perimeters.csv

# In build script:
python build_analysis.py \
  --housing-data $(HOUSING_DATA) \
  --census-data $(CENSUS_DATA) \
  --fire-data $(FIRE_DATA)
```

## See Also

- [TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md) - Customization guide
- [.gitignore](../.gitignore) - Data exclusion patterns
- [QUICKSTART.md](../QUICKSTART.md) - Getting started guide
