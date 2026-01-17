# Data Availability Statement

**Last updated:** January 17, 2026

---

## Summary

This replication package contains all data necessary to reproduce the results in the paper. The data consists of:

- ✅ **Sample data** included in repository (`data/housing_panel.csv`)
- 🔒 **Proprietary/restricted data** (if applicable) - instructions below
- 📊 **Processed datasets** (if applicable) - included/instructions below

---

## Data Files Included

### In This Repository

| File | Description | Source | Size | License |
|------|-------------|--------|------|---------|
| `data/housing_panel.csv` | Sample housing panel data | Simulated/public domain | ~0.3KB | Public domain |

**SHA256 checksums** for verification:
```bash
# Verify data files haven't been modified:
sha256sum data/housing_panel.csv
# Expected: [checksum will be in provenance records after first build]
```

---

## Data Not Included (If Applicable)

### Proprietary/Restricted Data

**If your analysis uses proprietary data, document here:**

#### [Data Source Name 1]

- **Description:** Brief description of the data
- **Provider:** Organization name
- **Access:** How to obtain (URL, application process, cost)
- **Restrictions:** Terms of use, redistribution limitations
- **Contact:** data.provider@organization.org
- **Our access:** We obtained this data under [agreement type] on [date]

**To obtain access:**
1. Visit [URL]
2. Complete application at [application link]
3. Expected turnaround: [timeframe]
4. Cost: [cost if any]

#### [Data Source Name 2]

[Repeat structure above]

---

## Data Construction Pipeline

**If you process raw data into analysis-ready datasets:**

### Raw Data → Processed Data

Our complete data construction pipeline is in `data-construction/` (excluded from journal package as it requires proprietary raw data access).

**For replicators with raw data access:**

```bash
# 1. Place raw data files:
cd data/raw
ln -s /path/to/your/raw/data/* .

# 2. Run construction pipeline:
cd ../data-construction
make all

# 3. Verify processed data:
sha256sum ../processed/*.csv
# Compare with checksums in data/CHECKSUMS.txt
```

**What gets built:**
- `data/processed/dataset1.csv` - Description
- `data/processed/dataset2.csv` - Description

**Runtime:** ~[X hours] on [hardware specs]

---

## Sample Data for Testing

**For replicators without access to proprietary data:**

We provide sample data in `data/` that allows testing the replication code:

```bash
# Use sample data:
export DATA_DIR=data/sample  # If sample/ subdirectory exists
make all
```

**Sample data characteristics:**
- Subset of full data (e.g., 1% sample, one year, one region)
- Preserves data structure and variable definitions
- Produces qualitatively similar results (not identical)
- Useful for verifying code runs without errors

---

## Data Citation

If you use our processed datasets, please cite:

```bibtex
@data{yourname2026data,
  author = {Your Name},
  title = {Replication Data for: Your Paper Title},
  year = {2026},
  publisher = {Repository Name},
  version = {1.0},
  doi = {10.xxxx/xxxxx},
  url = {https://doi.org/10.xxxx/xxxxx}
}
```

---

## IRB and Privacy Compliance

**If applicable:**

- This research was approved by [Institution] IRB, protocol #[number]
- All personally identifiable information has been removed
- Data has been aggregated to [geographic unit] level to protect privacy
- Cell suppression applied for cells with <[N] observations

---

## Data Modifications

**Relative to original sources, we have:**

- [ ] Subset to relevant observations (criteria: [describe])
- [ ] Filtered outliers (criteria: [describe])  
- [ ] Aggregated/anonymized for privacy
- [ ] Merged across sources
- [ ] Created derived variables (see data construction scripts)

**No modifications** - data is used as received from provider

---

## Verification

**To verify data files match our originals:**

```bash
# Compare checksums:
sha256sum -c data/CHECKSUMS.txt

# Or check provenance records:
cat output/provenance/price_base.yml
# Shows SHA256 of each input file
```

---

## Questions About Data Access?

**Contact:**
- [Your Name], [Institution]
- Email: your.email@institution.edu
- Please include "Data Access Request" in subject line

**Response time:** We aim to respond within [timeframe]

---

## Data Availability for Journal Editors

**For journal editors/reviewers without data access:**

We have deposited:
- ✅ Complete processed datasets on [repository]
- ✅ Sample data in this GitHub repository
- ✅ Data construction code (requires raw data access)

**Temporary access for peer review:**
- Contact us for temporary access to processed datasets
- Available via secure data enclave at [institution]
- See [secure data access instructions]

---

## Future Data Availability

**After publication, data will be available at:**
- [ ] Publicly at: [repository URL]
- [ ] Via application to: [organization]
- [ ] As supplementary material to published article
- [ ] On author's website: [URL]

**Persistent identifier (DOI) will be assigned upon deposit.**

---

## License

**For data we created/processed:**
- License: [CC BY 4.0 / CC0 / other]
- Attribution: [required citation]
- Restrictions: [any]

**For third-party data:**
- Governed by original provider's terms
- See individual data sources above

---

**See also:**
- `data/README.md` - Data directory structure
- `data/DATA_README.md` - Detailed data documentation
- `data/CHECKSUMS.txt` - File verification checksums
- `docs/provenance.md` - How we track data provenance
