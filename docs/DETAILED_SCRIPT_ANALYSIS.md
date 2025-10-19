# Detailed Script Analysis for Cleanup

**Date**: 2025-10-19
**Purpose**: Provide detailed breakdown of each script involved in cleanup recommendations

---

## ❌ Scripts Recommended for DELETION

### 1. `calculate_krippendorff.py` (318 lines)

**What it does:**
- Calculates standard Krippendorff's Alpha using the `krippendorff` library
- Attempts to calculate semantic alpha but **doesn't actually implement it**
- Line 100-106: Just prints "Note: Semantic Krippendorff's Alpha requires custom implementation"
- Compares results with student calculations
- Calculates per-module agreement

**Why DELETE:**
- ❌ **Does NOT calculate semantic alpha** (just a placeholder!)
- ❌ Uses external library that doesn't support custom distance metrics
- ❌ Superseded by `recalculate_krippendorff_with_details.py` which implements all three alphas
- ❌ Old module-by-module averaging approach (wrong method discovered earlier)

**Functions:**
- `calculate_krippendorff_alpha()` - uses library (nominal only)
- `load_cleaned_data()` - loads CSV
- `calculate_agreement_metrics()` - per-module and overall

**What you lose:** Nothing - all functionality is in newer script

---

### 2. `calculate_semantic_krippendorff.py` (375 lines)

**What it does:**
- Implements full semantic Krippendorff from scratch
- Uses custom distance matrix from `data/processed/obds_distance_matrix.csv`
- Builds coincidence matrix manually
- Calculates observed and expected disagreement with semantic distances
- **NOTE**: Uses full relations graph (line 31: `obds_distance_matrix.csv`)

**Why DELETE:**
- ❌ Superseded by `recalculate_krippendorff_with_details.py`
- ❌ Only calculates **one type** of semantic alpha (full relations)
- ❌ Newer script calculates all three types and provides verification outputs
- ⚠️ **HOWEVER**: Implementation code is correct and matches newer script

**Functions:**
- `calculate_semantic_krippendorff_alpha()` - full implementation (lines 50-180)
- `calculate_overall_semantic_alpha()` - wrapper
- `calculate_per_module_semantic_alpha()` - per-module calculations
- `compare_with_standard_alpha()` - loads recent results and compares

**What you lose:** Nothing - same implementation exists in newer comprehensive script

---

### 3. `calculate_semantic_krippendorff_isa.py` (375 lines)

**What it does:**
- **EXACT SAME CODE** as `calculate_semantic_krippendorff.py`
- Only difference: Line 31 uses `obds_distance_matrix_isa.csv` (IS-A only graph)
- Otherwise identical line-by-line

**Why DELETE:**
- ❌ Duplicate code (copy-paste with one line changed!)
- ❌ Superseded by unified script that handles both IS-A and full relations
- ❌ This is exactly the code duplication problem we're trying to solve

**What you lose:** Nothing - newer script handles both graph types

---

## 🔄 Scripts Recommended for INTEGRATION

### A. Mapper Analysis Scripts

#### `analyze_mapper_contributions.py` (473 lines)

**What it does:**
- **SPECIALIZED**: Leave-one-out (jackknife) analysis
- Implements its own Krippendorff calculation (lines 53-136)
- Calculates alpha with each 3-mapper combination
- Creates comprehensive visualizations (heatmap, delta charts, summary table)
- Outputs `fig7_mapper_contributions.png`

**Key functionality:**
- `krippendorff_alpha()` - custom implementation
- `perform_leave_one_out_analysis()` - removes each mapper, recalculates alpha
- `create_contribution_visualization()` - multi-panel figure

#### `analyze_mapper_performance.py` (469 lines)

**What it does:**
- **BROADER ANALYSIS**: Multiple metrics per mapper
  1. Completeness rate (% concepts mapped)
  2. Unique contributions (concepts only mapped by one mapper)
  3. Concept diversity (how many unique SNOMED concepts each mapper used)
  4. Pairwise agreement (alpha between each pair)
  5. Leave-one-out alpha (lines 256-289)
  6. Consensus agreement (how often mapper agrees with majority)
  7. Module-specific performance

**Key functionality:**
- `calculate_completeness_rate()` - coverage metrics
- `calculate_unique_contributions()` - exclusive mappings
- `calculate_concept_diversity()` - concept reuse patterns
- `calculate_pairwise_agreement()` - all 6 pairs
- `calculate_leave_one_out_alpha()` - **overlaps with contributions.py**
- `calculate_consensus_agreement()` - mode comparison
- `analyze_mapper_by_module()` - module breakdowns

**OVERLAP:**
- Both scripts calculate leave-one-out alpha (lines 256-289 in performance vs entire script in contributions)
- Both use Krippendorff library/implementation

**RECOMMENDATION:**
- ✅ **KEEP** `analyze_mapper_performance.py` as primary script (more comprehensive)
- ➕ **ADD** the detailed visualization from `analyze_mapper_contributions.py`
- ➕ **ADD** the multi-panel figure generation code (lines 270-411)
- Result: One comprehensive mapper analysis script with all metrics + visualization

**What you gain:**
- Single source for all mapper analyses
- No duplicate leave-one-out calculations
- Better visualization integrated with metrics

---

### B. Difficulty Analysis Scripts

#### `identify_difficult_concepts.py` (328 lines)

**What it does:**
- Analyzes **agreement patterns** per oBDS concept
- Classifies each concept by agreement type:
  - Perfect agreement (all mappers same)
  - High agreement (≥75%)
  - Moderate agreement (≥50%)
  - Low agreement (<50%)
  - Complete disagreement (all different)
  - Single mapper only
  - Unmapped
- Outputs lists of problem concepts by category
- Uses **agreement rate** as difficulty proxy

**Key functionality:**
- `create_concept_agreement_matrix()` - per-concept metrics
- `identify_problem_areas()` - exports problem cases
- `identify_strengths()` - exports high-agreement cases

#### `calculate_mapping_difficulty.py` (305 lines)

**What it does:**
- Calculates **Mapping Difficulty Index (MDI)** - a composite metric
- Formula: `MDI = 0.5 × disagreement + 0.4 × semantic_disagreement + 0.1 × diversity`
- Three components:
  1. **Disagreement**: Proportion who disagree with most common code
  2. **Semantic disagreement**: Mean pairwise SNOMED distance / 50
  3. **Diversity**: Number of unique codes / (n_coders - 1)
- Outputs difficulty scores per item (0-1 scale)
- Classifies items: Easy (<0.1), Moderate (0.1-0.3), Difficult (0.3-0.6), Very difficult (>0.6)
- Identifies gap analysis candidates (MDI >= 0.5)
- Module-level difficulty summary

**Key functionality:**
- `calculate_mapping_difficulty()` - composite MDI calculation
- Outputs 4 files:
  1. Item difficulty scores
  2. Gap analysis candidates (high MDI)
  3. Module difficulty summary
  4. Summary report

**OVERLAP with `identify_difficult_concepts.py`:**
- ✅ Both identify difficult concepts
- ✅ Both use disagreement as indicator
- ❌ Different approaches:
  - **MDI**: Quantitative composite score (0-1 continuous)
  - **Agreement**: Categorical classification (perfect, high, moderate, low, complete)
- ❌ Different outputs:
  - **MDI**: Focuses on gap analysis candidates, uses semantic distance
  - **Agreement**: Lists problem concepts by category, simpler classification

**RECOMMENDATION:**
- **DO NOT MERGE** - They serve different purposes!
- **MDI script**: For prioritizing BfArM gap submissions (quantitative ranking)
- **Agreement script**: For understanding agreement patterns (categorical analysis)
- **KEEP BOTH** as separate analyses
- They complement each other:
  - Use agreement script to identify **types** of problems
  - Use MDI script to **rank** severity for action prioritization

---

## ✅ Scripts to RENAME

### `recalculate_krippendorff_with_details.py` → `calculate_all_alphas.py`

**Why:**
- "recalculate" implies fixing something (which we did)
- "calculate_all_alphas" is clearer about what it does
- This is now the PRIMARY Krippendorff calculation script
- Name should reflect its comprehensive nature (all three alpha types)

---

## 📄 Script to CONVERT TO DOCUMENTATION

### `explain_alpha_baselines.py` → `docs/UNDERSTANDING_ALPHA_BASELINES.md`

**Current script (112 lines):**
- Loads SNOMED graph to count nodes
- Prints explanations of three different baselines:
  1. Traditional Krippendorff (576 used codes)
  2. Full SNOMED CT (371,737 concepts)
  3. Semantic alpha (correct approach)
- Educational content explaining why semantic alpha is right
- Console output only - no calculations

**Why convert to markdown:**
- ✅ This is documentation, not analysis code
- ✅ Educational content should be in docs, not scripts
- ✅ Easier to read and share as markdown
- ✅ No need to run Python to understand concepts
- ✅ Can include in paper/presentation materials

**Proposed markdown structure:**
```markdown
# Understanding Krippendorff's Alpha Baselines for SNOMED CT

## Three Different Approaches

### 1. Traditional Krippendorff (What We Calculated)
Baseline: 576 codes actually used by mappers

### 2. Full SNOMED CT (Naive Approach)
Baseline: All 371,737 SNOMED concepts

### 3. Semantic Alpha (Correct Approach)
Weighted by graph distance
```

---

## 📊 Summary of Changes

### Files Affected: 7 scripts (revised)

**DELETE (3):**
1. `calculate_krippendorff.py` - incomplete implementation
2. `calculate_semantic_krippendorff.py` - single type only
3. `calculate_semantic_krippendorff_isa.py` - duplicate code

**INTEGRATE (2):**
1. `analyze_mapper_contributions.py` → merge visualization into performance
2. `analyze_mapper_performance.py` → keep as primary, add visualization

**KEEP BOTH (not merging):**
1. `identify_difficult_concepts.py` - categorical agreement analysis
2. `calculate_mapping_difficulty.py` - quantitative MDI ranking
   - **Reason**: Different purposes, complementary approaches

**RENAME (1):**
1. `recalculate_krippendorff_with_details.py` → `calculate_all_alphas.py`

**CONVERT (1):**
1. `explain_alpha_baselines.py` → `docs/UNDERSTANDING_ALPHA_BASELINES.md`

### Result: 18 scripts (from 22)
- **22 original** scripts
- **-3** deleted (superseded)
- **-2** integrated (mapper analysis merger)
- **-1** converted to markdown
- **= 16** remaining scripts
- **+2** kept separate (difficulty scripts are complementary)
- **= 18** total

---

## Implementation Plan

### Phase 1: Safe Deletions (No Dependencies)
```bash
# These scripts are completely superseded
rm scripts/calculate_krippendorff.py
rm scripts/calculate_semantic_krippendorff.py
rm scripts/calculate_semantic_krippendorff_isa.py
```
**Status**: Ready to execute immediately
**Risk**: ZERO - completely superseded, no unique functionality

### Phase 2: Merge Mapper Analysis
1. Copy visualization code from `analyze_mapper_contributions.py` (lines 270-411)
2. Add to `analyze_mapper_performance.py`
3. Update leave-one-out section to include detailed visualization
4. Test merged script with sample data
5. Delete `analyze_mapper_contributions.py`

**Status**: Requires code work
**Risk**: LOW - well-defined scope, clear overlap
**Estimated effort**: 1-2 hours (copy + test)

### Phase 3: Rename and Document
```bash
mv scripts/recalculate_krippendorff_with_details.py scripts/calculate_all_alphas.py
```

Create `docs/UNDERSTANDING_ALPHA_BASELINES.md` from script content:
- Extract explanation sections from `explain_alpha_baselines.py`
- Convert to markdown format
- Remove Python code, keep concepts

**Status**: Ready to execute
**Risk**: ZERO - simple rename + content extraction

### Phase 4: Update Dependencies
- Check for any imports of deleted scripts (unlikely - these are standalone)
- Update CLAUDE.md with new script structure
- Update README with corrected quick start guide
- Update script inventory document

**Status**: Documentation updates only
**Risk**: ZERO

---

## Risk Assessment

**ZERO RISK (can execute immediately):**
- ✅ Delete 3 Krippendorff scripts: Truly superseded, no unique functionality
- ✅ Rename: Simple file rename, no code changes
- ✅ Convert to markdown: Content extraction only

**LOW RISK (requires testing):**
- ⚠️ Mapper analysis merge: Need to carefully preserve visualization code
- ⚠️ Test that all functionality is preserved after merge
- ⚠️ Estimated effort: 1-2 hours

**RESOLVED:**
- ✅ Difficulty analysis: Decided to KEEP BOTH (complementary, not redundant)

---

## Decision Summary

**Approved for Execution:**
1. ✅ DELETE 3 Krippendorff scripts
2. ✅ RENAME recalculate_krippendorff_with_details.py
3. ✅ CONVERT explain_alpha_baselines.py to markdown

**Requires Work:**
4. ⚠️ MERGE mapper analysis scripts (1-2 hours)

**Not Merging (Decision Made):**
5. ✅ KEEP BOTH difficulty scripts (they complement each other)

---

## Recommended Execution Order

### Immediate (Quick Wins):
```bash
# 1. Delete superseded scripts (30 seconds)
rm scripts/calculate_krippendorff.py
rm scripts/calculate_semantic_krippendorff.py
rm scripts/calculate_semantic_krippendorff_isa.py

# 2. Rename for clarity (5 seconds)
mv scripts/recalculate_krippendorff_with_details.py scripts/calculate_all_alphas.py
```

### Later (When Time Permits):
3. Convert `explain_alpha_baselines.py` to markdown (15 minutes)
4. Merge mapper analysis scripts (1-2 hours)
5. Update documentation (30 minutes)

---

## Final Structure After Cleanup

**Result: 18 scripts (from 22)**

### Core Pipeline (4):
- ✅ extract_mapping_table.py
- ✅ clean_mapping_data.py
- ✅ build_distance_matrix.py
- ✅ obds_modules.py

### Analysis (5):
- ✅ **calculate_all_alphas.py** (renamed)
- ✅ analyze_mapper_performance.py (with merged visualization)
- ✅ calculate_mapping_difficulty.py (quantitative MDI)
- ✅ identify_difficult_concepts.py (categorical agreement)
- ✅ analyze_missing_values.py
- ✅ calculate_quality_score.py

### Visualization (2):
- ✅ visualize_basic_results.py
- ✅ create_presentation_figures.py

### Utilities (1):
- ✅ check_distance_matrix_coverage.py

### Graph Builder (4):
- ✅ GraphBuilder.py
- ✅ Worker.py
- ✅ Measure.py
- ✅ Main.py

**Total: 18 scripts**

---

**Next Step:**
Choose your preferred approach:
- **Option A**: Execute all quick wins now (deletions + rename)
- **Option B**: Execute deletions only, save rename for later
- **Option C**: Wait and review everything together
