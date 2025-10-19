# oBDS SNOMED CT Mapping - Quality Assessment Presentation

**20 Slides | Quality Analysis of 4-Mapper SNOMED CT Coding for Oncology Registry Data**

---

## Slide 1: Title Slide
**SNOMED CT Mapping of oBDS for MII-Onko**
Quality Assessment Using Semantic Krippendorff's Alpha

- Project: oBDS → SNOMED CT for MII-Onko Module
- Timeline: Started Feb 2024
- Goal: Create validated SNOMED mappings for EHDS integration

---

## Slide 2: Project Context
**Background & Motivation**

- **oBDS**: Onkologischer Basisdatensatz (German Oncology Dataset)
- **Target**: MII-Onko module for Medical Informatics Initiative
- **Challenge**: Standardize 579 clinical concepts using SNOMED CT
- **Future**: EHDS (European Health Data Space) integration

---

## Slide 3: Study Design
**Mapping Methodology**

- **4 independent mappers** (pseudonymized: Mapper A-D)
- **579 oBDS concepts** across 19 modules
- **Tools used**:
  - SNOMED Browser
  - Basisdatensatz.de
  - Implementation guides
- **Focus**: Clinical data points (no administrative/reporting data)

---

## Slide 4: Mapping Scope
**Data Overview**

- **Total oBDS concepts**: 579 (across 19 modules)
- **Unique SNOMED concepts used**: 593
- **SNOMED CT version**: International Edition 2025-02-01
- **Coverage**: 371,737 concepts, 1.2M relationships

---

## Slide 5: Data Quality Challenge
**Excel & Pandas Precision Issues**

**Problem**: 18-digit SNOMED IDs → Scientific notation
- Example: `900000000000465000` → `9.00000000000465e+17`
- Float64 precision loss in last digits

**Solution**: Manual mapping + forced string dtype
- 10 scientific notation cases corrected
- All conversions validated against SNOMED CT

---

## Slide 6: Data Cleaning Pipeline
**7-Step Transformation Process**

1. Remove workflow comments (pilot module artifacts)
2. Convert dash placeholders to missing values
3. Fix pandas float conversion (`.0` endings)
4. Handle multi-value entries (extract first, log others)
5. Manual mapping for scientific notation
6. Fix data entry typos (missing digits)
7. Extract concept IDs from annotations

---

## Slide 7: Scientific Notation Corrections
**Critical Manual Mappings**

| Scientific Notation | Corrected SCTID | Description | Status |
|---------------------|-----------------|-------------|--------|
| 9.00...465e+17 | 900000000000465000 | String (metadata) | ✓ Active |
| 9.00...519e+17 | 900000000000519001 | Annotation value | ✓ Active |
| 9.11...004e+17 | 911753521000004108 | Precision lost | ✓ Active |

**Key Insight**: Foundation metadata concepts used for "Freitext" fields

---

## Slide 8: Data Validation Results
**SNOMED CT Coverage**

- **Total concepts**: 593
- **Valid in SNOMED graph**: 590 (99.5%)
- **Invalid/Missing**: 3 concepts
  - 2 inactive (valid at mapping time, later retired)
  - 1 US Extension concept (not in International Edition)

---

## Slide 9: Missing Value Patterns
**Mapper Completeness**

| Mapper | Valid Concepts | Missing | Completeness |
|--------|----------------|---------|--------------|
| Mapper A | 480 | 69 (12.6%) | 87.4% |
| Mapper B | 464 | 85 (15.5%) | 84.5% |
| Mapper C | 379 | 170 (31.0%) | 69.0% |
| Mapper D | 430 | 119 (21.7%) | 78.3% |

**Variation**: Reflects different clinical perspectives and expertise

---

## Slide 10: Agreement Metrics Overview
**Krippendorff's Alpha Approaches**

1. **Standard (Nominal) Alpha**
   - Binary: Same concept = 0, Different = 1
   - Identity-based agreement only

2. **Semantic (Taxonomic) Alpha**
   - Weighted by SNOMED path distance²
   - Recognizes partial agreement
   - Clinically meaningful similarity

---

## Slide 11: Semantic Similarity Infrastructure
**SNOMED CT Graph Construction**

**Two graph types created**:
- **IS-A only**: 371,737 nodes, 608K edges (hierarchy)
- **Full relations**: 371,737 nodes, 1.2M edges (all relationships)

**Distance calculation**:
- Shortest path via root concept (138875005)
- NetworkX directed graphs
- 593² = 351,649 pairwise distances computed

---

## Slide 12: Distance Matrix Statistics

**Full Relations Graph** (used for main analysis):
- Distance range: 0-49 hops
- Mean distance: 22.36
- Median distance: 23.00

**IS-A Only Graph** (comparison):
- Distance range: 0-54 hops
- Mean distance: 28.60 (+28% longer paths)
- Median distance: 30.00

---

## Slide 13: Standard Krippendorff's Alpha
**Identity-Based Agreement Results**

**Overall: α = 0.6680** (moderate-good agreement)

**Top 3 modules**:
- Modul 19: α = 0.93 (excellent)
- Modul 20: α = 0.91 (excellent)
- Modul 18: α = 0.86 (good)

**Bottom 3 modules**:
- Modul 21: α = 0.00 (no agreement)
- Modul 10: α = 0.05 (poor)
- Modul 12: α = 0.40 (fair)

---

## Slide 14: Semantic Krippendorff's Alpha
**Taxonomy-Weighted Agreement Results**

**Overall: α = 0.8494** (excellent!)

**Improvement: +0.18** over standard alpha (+27%)

**Why higher?**
- Recognizes semantically similar concepts as partial agreement
- Example: "Malignant tumor" vs "Neoplasm" = close in hierarchy
- Clinically meaningful measure

---

## Slide 15: Algorithm Explanation
**Semantic Weighting Formula**

Standard: Disagreement = 1 (if different)

Semantic: Disagreement = (SNOMED distance)²

**Krippendorff's Alpha**:
```
α = 1 - (observed disagreement / expected disagreement)
```

**Distance² weighting**:
- Close concepts (3 hops): weight = 9
- Far concepts (30 hops): weight = 900
- Reflects clinical semantic difference

---

## Slide 16: Module-Level Comparison
**Standard vs Semantic Alpha by Module**

**Biggest improvements** (semantic - standard):
- Modul 11: +0.22 (0.35 → 0.58)
- Modul 14: +0.21 (0.69 → 0.89)
- Modul 23: +0.19 (0.54 → 0.73)

**Similar results**:
- Modul 17: +0.01 (0.50 → 0.51)
- Modul 25: -0.01 (0.43 → 0.42)

**Interpretation**: Large improvements = mappers chose similar but not identical concepts

---

## Slide 17: IS-A vs Full Relations
**Graph Type Comparison** (preliminary results)

| Metric | IS-A Only | Full Relations | Difference |
|--------|-----------|----------------|------------|
| Edges | 608K | 1.2M | +97% |
| Mean distance | 28.60 | 22.36 | -22% |
| Semantic Alpha | [calculating] | 0.8494 | TBD |

**Hypothesis**: Full relations provide richer semantic context

---

## Slide 18: Clinical Implications
**What Semantic Alpha Tells Us**

**High agreement (α > 0.80)**:
- Well-defined clinical concepts
- Clear SNOMED mapping paths
- Ready for implementation

**Moderate agreement (0.60-0.80)**:
- Multiple valid interpretations
- May need consensus process
- Document mapping rationale

**Low agreement (α < 0.40)**:
- Ambiguous oBDS definitions
- Multiple clinical perspectives
- Candidate for BfArM gap analysis

---

## Slide 19: Lessons Learned
**Data Quality Best Practices**

1. **Never trust Excel with large integers**
   - Always use string dtype for IDs
   - Validate all scientific notation

2. **Document every transformation**
   - Scientific notation mappings
   - Typo corrections
   - Multi-value handling

3. **Semantic metrics > Identity metrics**
   - Better reflects clinical reality
   - Captures partial agreement
   - Clinically interpretable

---

## Slide 20: Next Steps & Deliverables
**Project Outcomes**

**Completed**:
- ✓ 579 oBDS concepts mapped by 4 independent mappers
- ✓ Data quality pipeline with full traceability
- ✓ Semantic similarity infrastructure
- ✓ Agreement metrics (standard & semantic)

**Next**:
- Gap analysis for BfArM submission
- Multi-value case analysis
- Consensus resolution for low-agreement modules
- Integration into MII-Onko FHIR profiles

---

## Appendix: Technical Details

**Software & Tools**:
- Python 3.x (pandas, numpy, networkx, krippendorff)
- SNOMED CT International Edition 2025-02-01
- R (comparison with Swedish semantic alpha implementation)

**Code Repository**: [Location if applicable]

**Data Availability**: Pseudonymized for publication

**References**:
- LiU-IMT/semantic_kripp_alpha (GitHub)
- Krippendorff, K. (2013). Content Analysis
- SNOMED International RF2 Specification
