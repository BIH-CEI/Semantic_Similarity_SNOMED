# Script Inventory & Analysis

**Date**: 2025-10-19
**Total Scripts**: 22 Python scripts + 3 Jupyter notebooks
**Status**: Analysis of current state and recommendations for cleanup

---

## 📊 Executive Summary

### Current State
- **Core pipeline**: 5 essential scripts ✅
- **Redundant scripts**: 7 scripts with overlapping functionality ⚠️
- **Outdated scripts**: 3 scripts superseded by newer versions ❌
- **Support infrastructure**: 4 utility scripts ✅
- **Visualization**: 3 scripts ✅

### Recommendations
1. **Keep**: 12 scripts (core functionality)
2. **Delete**: 3 scripts (superseded)
3. **Integrate**: 7 scripts (consolidate into fewer files)

---

## 🔄 Data Processing Pipeline

### ✅ KEEP - Core Pipeline

| Script | Purpose | Status | Dependencies |
|--------|---------|--------|--------------|
| `extract_mapping_table.py` | Extract raw data from Excel | **ESSENTIAL** | Excel file |
| `clean_mapping_data.py` | Clean & validate SNOMED IDs | **ESSENTIAL** | extract output |
| `build_distance_matrix.py` | Build SNOMED distance matrices | **ESSENTIAL** | SNOMED graphs |
| `obds_modules.py` | Module name constants | **ESSENTIAL** | None |

**Pipeline Flow**:
```
Excel → extract_mapping_table.py → obds_mapping_table_raw.csv
  ↓
clean_mapping_data.py → obds_mapping_table.csv
  ↓
build_distance_matrix.py → obds_distance_matrix.csv
```

---

## 📈 Krippendorff's Alpha Calculations

### ✅ CONSOLIDATED - Single Comprehensive Implementation

| Script | Purpose | Status | Notes |
|--------|---------|--------|-------|
| `calculate_all_alphas.py` | **ALL THREE alphas + verification** | **ACTIVE** | ✅ Primary script |
| `calculate_semantic_krippendorff_isa_optimized.py` | Optimized IS-A alpha | **REFERENCE** | ⚠️ Keep for optimization techniques |

**Status**: ✅ **CLEANUP COMPLETE (2025-10-19)**
- ❌ **DELETED** (3 scripts): `calculate_krippendorff.py`, `calculate_semantic_krippendorff.py`, `calculate_semantic_krippendorff_isa.py`
- ✅ **RENAMED**: `recalculate_krippendorff_with_details.py` → `calculate_all_alphas.py`
- ✅ **RESULT**: Single source of truth for all Krippendorff calculations

---

## 🔍 Analysis & Metrics

### ✅ KEEP - Unique Analysis Scripts

| Script | Purpose | Keep? | Notes |
|--------|---------|-------|-------|
| `analyze_missing_values.py` | Missing value patterns | ✅ **YES** | Unique analysis |
| `calculate_mapping_difficulty.py` | Mapping Difficulty Index (MDI) | ✅ **YES** | Gap analysis |
| `calculate_quality_score.py` | Completeness × Agreement | ✅ **YES** | Quality metric |
| `identify_difficult_concepts.py` | Find hard-to-map concepts | ⚠️ **INTEGRATE** | Similar to MDI |

### ⚠️ INTEGRATE - Mapper Performance

| Script | Purpose | Status | Recommendation |
|--------|---------|--------|----------------|
| `analyze_mapper_performance.py` | Mapper completeness, agreement | ✅ **KEEP** | Comprehensive |
| `analyze_mapper_contributions.py` | Leave-one-out analysis | ⚠️ **INTEGRATE** | Add to performance |

**Recommendation**: Merge `analyze_mapper_contributions.py` into `analyze_mapper_performance.py`

---

## 📊 Visualization

### ✅ KEEP - All Visualization Scripts

| Script | Purpose | Outputs | Keep? |
|--------|---------|---------|-------|
| `visualize_results.py` | Basic alpha visualizations | 3 PNG files | ✅ **YES** |
| `create_presentation_figures.py` | Publication figures | 6 PNG files | ✅ **YES** |
| `explain_alpha_baselines.py` | Educational/documentation | Console only | ⚠️ **CONVERT TO MD** |

**Recommendation**:
- Keep both visualization scripts (different purposes)
- Convert `explain_alpha_baselines.py` to markdown documentation

---

## 🛠️ Supporting Infrastructure

### ✅ KEEP - Utility Scripts

| Script | Purpose | Keep? |
|--------|---------|-------|
| `check_distance_matrix_coverage.py` | Verify matrix coverage | ✅ **YES** (diagnostic) |
| `obds_modules.py` | Module name constants | ✅ **YES** (essential) |

---

## 🌳 Graph Builder (Semantic Similarity)

### ✅ KEEP - Core Graph Infrastructure

Located in `scripts/graphbuilder/`:

| Script | Purpose | Keep? | Notes |
|--------|---------|-------|-------|
| `GraphBuilder.py` | Build SNOMED graphs from RF2 | ✅ **YES** | Core infrastructure |
| `Worker.py` | Graph traversal (LCA, paths) | ✅ **YES** | Used by distance calc |
| `Measure.py` | Semantic similarity measures | ✅ **YES** | 7 different metrics |
| `Main.py` | Entry point/examples | ⚠️ **OPTIONAL** | Mostly testing code |

**Source**: Adapted from https://github.com/skfit-uni-luebeck/semantic-similarity

---

## 📓 Jupyter Notebooks

Located in `notebooks/`:

| Notebook | Purpose | Status | Keep? |
|----------|---------|--------|-------|
| `oBDS_Data_Import.ipynb` | Data exploration & cleaning logic | **ARCHIVED** | ⚠️ MOVE TO `archive/` |
| `validation.ipynb` | Validate SNOMED concepts | **USEFUL** | ✅ **YES** |
| `Concept_Quality_Check.ipynb` | Quality analysis | **OUTDATED** | ⚠️ SUPERSEDED BY SCRIPTS |

**Recommendation**:
- Keep `validation.ipynb` for ad-hoc validation
- Archive `oBDS_Data_Import.ipynb` (logic now in scripts)
- Delete or archive `Concept_Quality_Check.ipynb` (use scripts instead)

---

## 🎯 Recommended Actions

### 1️⃣ DELETE (3 scripts) ❌

**Reason**: Superseded by `recalculate_krippendorff_with_details.py`

```bash
# Delete old Krippendorff implementations
rm scripts/calculate_krippendorff.py
rm scripts/calculate_semantic_krippendorff.py
rm scripts/calculate_semantic_krippendorff_isa.py
```

### 2️⃣ INTEGRATE (4 scripts) 🔄

#### A. Merge Mapper Analysis Scripts
```bash
# Merge analyze_mapper_contributions.py INTO analyze_mapper_performance.py
# Result: One comprehensive mapper analysis script
```

#### B. Merge Difficulty Analysis Scripts
```bash
# Merge identify_difficult_concepts.py INTO calculate_mapping_difficulty.py
# Both identify hard-to-map concepts
```

#### C. Integrate Optimized Alpha
```bash
# Take optimization techniques from calculate_semantic_krippendorff_isa_optimized.py
# Apply to recalculate_krippendorff_with_details.py
# Then delete the optimized version
```

### 3️⃣ RENAME (2 scripts) 📝

```bash
# Make purpose clearer
mv scripts/recalculate_krippendorff_with_details.py scripts/calculate_all_alphas.py
mv scripts/visualize_results.py scripts/visualize_basic_results.py
```

### 4️⃣ CONVERT (1 script) 📄

```bash
# Convert to documentation
# explain_alpha_baselines.py → docs/UNDERSTANDING_ALPHA_BASELINES.md
```

### 5️⃣ ARCHIVE (2 notebooks) 📦

```bash
mkdir -p notebooks/archive
mv notebooks/oBDS_Data_Import.ipynb notebooks/archive/
mv notebooks/Concept_Quality_Check.ipynb notebooks/archive/
```

---

## 📋 Final Recommended Structure

### After Cleanup (12 core scripts):

```
scripts/
├── # DATA PIPELINE (4)
│   ├── extract_mapping_table.py          ✅ Extract from Excel
│   ├── clean_mapping_data.py             ✅ Clean SNOMED IDs
│   ├── build_distance_matrix.py          ✅ Build distance matrices
│   └── obds_modules.py                   ✅ Module constants
│
├── # ANALYSIS (5)
│   ├── calculate_all_alphas.py           ✅ All Krippendorff calculations
│   ├── analyze_mapper_performance.py     ✅ Complete mapper analysis
│   ├── calculate_mapping_difficulty.py   ✅ MDI + difficult concepts
│   ├── calculate_quality_score.py        ✅ Quality metrics
│   └── analyze_missing_values.py         ✅ Missing patterns
│
├── # VISUALIZATION (2)
│   ├── visualize_basic_results.py        ✅ Basic visualizations
│   └── create_presentation_figures.py    ✅ Publication figures
│
├── # UTILITIES (1)
│   └── check_distance_matrix_coverage.py ✅ Diagnostic tool
│
└── graphbuilder/                          ✅ Graph infrastructure (4 scripts)
    ├── GraphBuilder.py
    ├── Worker.py
    ├── Measure.py
    └── Main.py
```

---

## 🔗 Script Dependencies Map

```
┌─────────────────────────────────────┐
│  Excel: oBDS_Module_alle_neu.xlsx   │
└──────────────┬──────────────────────┘
               │
               ▼
    extract_mapping_table.py
               │
               ▼
      obds_mapping_table_raw.csv
               │
               ▼
      clean_mapping_data.py
               │
               ▼
      obds_mapping_table.csv ◄────────────┐
               │                          │
               ├─────────────────┬────────┴─────────────┐
               ▼                 ▼                      ▼
    build_distance_matrix.py  calculate_all_alphas.py  analyze_mapper_performance.py
               │                 │                      │
               ▼                 │                      │
    obds_distance_matrix.csv    │                      │
               │                 │                      │
               └─────────────────┴──────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
         calculate_quality  analyze_missing  calculate_difficulty
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
                          results/*.csv
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
           visualize_basic_results  create_presentation_figures
                    │                         │
                    ▼                         ▼
            results/figures/*.png     results/figures/fig*.png
```

---

## 🎓 Summary Statistics

### Before Cleanup
- **Total scripts**: 22
- **Redundant**: 7 (32%)
- **Outdated**: 3 (14%)
- **Complexity**: HIGH (5 scripts for one metric!)

### After Cleanup
- **Total scripts**: 12 core + 4 graphbuilder = 16
- **Redundant**: 0 (0%)
- **Outdated**: 0 (0%)
- **Complexity**: LOW (clear purpose per script)
- **Space saved**: ~6 scripts deleted/archived

### Benefits
- ✅ Clearer project structure
- ✅ Easier to maintain
- ✅ Faster onboarding for new contributors
- ✅ Reduced confusion about which script to use
- ✅ Single source of truth for each analysis

---

## ⚡ Quick Start Guide (After Cleanup)

### Full Analysis Pipeline
```bash
# 1. Extract and clean data
python scripts/extract_mapping_table.py
python scripts/clean_mapping_data.py

# 2. Build distance matrix
python scripts/build_distance_matrix.py

# 3. Calculate all alphas (nominal, IS-A, full relations)
python scripts/calculate_all_alphas.py

# 4. Additional analyses
python scripts/analyze_mapper_performance.py
python scripts/calculate_mapping_difficulty.py
python scripts/calculate_quality_score.py

# 5. Create visualizations
python scripts/visualize_basic_results.py
python scripts/create_presentation_figures.py
```

---

## 📝 Implementation Checklist

- [x] Back up current `scripts/` directory (via git)
- [x] Delete 3 outdated Krippendorff scripts ✅ **DONE 2025-10-19**
- [x] Rename recalculate_krippendorff_with_details.py → calculate_all_alphas.py ✅ **DONE 2025-10-19**
- [ ] Merge mapper analysis scripts (analyze_mapper_contributions → analyze_mapper_performance)
- [ ] Convert explain_alpha_baselines.py to markdown documentation
- [ ] Archive old notebooks
- [ ] Update CLAUDE.md with new structure
- [ ] Update README with new quick start guide
- [ ] Test full pipeline end-to-end
- [ ] Update all imports in remaining scripts (if any)
- [ ] Commit changes with clear message

**Phase 1 Complete**: Safe deletions and rename executed successfully

---

**Last Updated**: 2025-10-19
**Maintained By**: Project Team
**Next Review**: After SNOMED Expo 2025
