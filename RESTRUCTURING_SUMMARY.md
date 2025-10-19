# Repository Restructuring Summary

**Date:** October 14, 2025
**Purpose:** Improve project organization and reproducibility

## Changes Made

### 1. New Directory Structure
```
Before:                          After:
.                                .
├── graphbuilder/                ├── data/
├── rawData/                     │   ├── raw/      (was rawData/)
├── *.ipynb (3 files)            │   ├── interim/  (timestamped outputs)
├── krippendorff_analysis.py     │   └── processed/ (final data)
└── obds_*.json/csv/txt          ├── scripts/
                                 │   └── graphbuilder/ (was graphbuilder/)
                                 ├── notebooks/    (was *.ipynb)
                                 ├── results/      (new)
                                 └── requirements.txt (new)
```

### 2. Files Moved

**Data reorganization:**
- `rawData/` → `data/raw/`
- `obds_cleaned_data_*.json` → `data/interim/`
- `obds_unique_concepts_*.txt/csv` → `data/interim/`

**Code reorganization:**
- `graphbuilder/` → `scripts/graphbuilder/`
- `*.ipynb` → `notebooks/`
- Deleted: `krippendorff_analysis.py` (was empty placeholder)

### 3. Path Updates

**GraphBuilder.py:**
- SNOMED concept file: `data/...` → `../../data/raw/SnomedCT_.../Snapshot/Terminology/sct2_Concept_Snapshot_INT_20250201.txt`
- SNOMED relationship file: Similar update
- Output pickle files: Now save to `../../data/processed/snomed-20250201_dag_*.pkl`
- Version updated: 20250401 → 20250201 (to match actual SNOMED version)

**Main.py:**
- Graph loading: `data/snomed-*.pkl` → `../../data/processed/snomed-*.pkl`

**oBDS_Data_Import.ipynb:**
- Excel path: `rawData/oBDS_Module_alle_neu.xlsx` → `../data/raw/oBDS/oBDS_Module_alle_neu.xlsx`
- Added dtype parameter to prevent .0 conversion on import

**validation.ipynb:**
- SNOMED directory: Absolute path → `../data/raw/SnomedCT_.../`
- Concept list: Root path → `../data/interim/obds_unique_concepts_*.txt`

### 4. New Files Created

**requirements.txt:**
- pandas, numpy, openpyxl
- networkx
- jupyter, ipykernel
- Ready for pip install

**CLAUDE.md updates:**
- Added directory structure documentation
- Updated all file paths
- Added setup instructions
- Clarified working directory requirements

### 5. Data Cleaning Improvement

**oBDS_Data_Import.ipynb cell 7:**
- Added `dtype` parameter to force SNOMED ID columns (3, 6, 9, 12) to string
- Prevents pandas float conversion at source
- Eliminates need for `.0` cleanup in later cells

## Benefits

1. **Reproducibility:** Clear separation of raw/interim/processed data
2. **Version Control:** Raw data easily gitignored, scripts tracked
3. **Collaboration:** Standard project structure familiar to researchers
4. **Testing:** Relative paths work from script directories
5. **Scalability:** Easy to add new scripts/notebooks/results

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Test GraphBuilder: `cd scripts/graphbuilder && python GraphBuilder.py`
3. Run cleaned data import: Open `notebooks/oBDS_Data_Import.ipynb`
4. Continue with Krippendorff analysis

## Notes

- All scripts should be run from their containing directories
- Raw data is never modified
- Timestamped outputs in `data/interim/` for audit trail
- Final clean data and graphs go to `data/processed/`
