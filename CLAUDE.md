# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project focuses on mapping oncological registry data (oBDS - Onkologischer Basisdatensatz) to SNOMED CT for use in the MII-Onko module and later integration into EHDS. The project involves quality assessment of mappings created by 4 independent mappers using various agreement metrics including Krippendorff's Alpha.

**Project Timeline**: Started ~02.2024, ongoing
**Key Goal**: Create SNOMED mapping of oBDS for direct use in MII-Onko module

## Project Components

### 1. Semantic Similarity Infrastructure
Based on adapted code from https://github.com/skfit-uni-luebeck/semantic-similarity

**Core Files:**
- `GraphBuilder.py`: Creates NetworkX graphs from SNOMED CT RF2 files
- `Main.py`: Entry point for similarity calculations  
- `Measure.py`: Implements 7 semantic similarity algorithms
- `Worker.py`: Graph utility functions (paths, LCA, information content)
- `BuildOBDSMatrix.ipynb`: Creates distance matrices for oBDS concepts

### 2. oBDS Mapping Project Structure

**Mapping Process:**
- 4 independent mappers (Nina, Sophie, Paul, Lotte)
- Tools used: SNOMED Browser, Basisdatensatz.de, implementation guides  
- Focus: Clinical data points relevant to MII Onko (no personal/reporting data)
- **Data Structure**: 19 modules with 579 total oBDS concepts to map

**Key Data Files (when downloaded):**
- `oBDS_Module_alle_neu.xlsx`: Final consolidated mapping file
- `oBDS_Mapping_IDs_only.xlsx`: Raw mapping IDs for Krippendorff analysis
- `Mapping_IDs_NewFormat.csv`: Transposed mapping data
- `oBDS_distance_matrix.csv`: Semantic distance matrix
- `K-Alpha-Tables_keine_Platzhalter.xlsx`: Krippendorff results by module

**File Structure in Excel:**
- Columns A-C: Original oBDS fields
- Columns D-E, G-H, J-K, M-N, Q-R: Mapper results (SCTID, FSN, ISO-Score)
- Column S: Code usage frequency (1-4 based on mapper agreement)
- Column T: Total unique codes count
- Column U: Code ratio
- Column V: ISO mismatch annotations (!sCdR, !DcSr)
- Column Z/W: Mean ISO scores across mappers

### 3. Quality Assessment Methods

**Krippendorff's Alpha Analysis:**
- **Standard Alpha**: Identity-based agreement between mappers
- **Semantic Alpha**: Uses SNOMED CT taxonomic distances for weighting
- **Pairwise Analysis**: Heatmap visualization of mapper agreement

**R Scripts (when available):**
- `Krippendorff-Alpha-Code.R`: Basic Krippendorff calculation
- `PaarweiseÜbereinstimmungHM.R`: Pairwise agreement heatmaps
- `Kripp_Taxonomy*.R`: Semantic Krippendorff with taxonomic weighting
- Based on Swedish implementation: https://github.com/LiU-IMT/semantic_kripp_alpha

## Data Requirements

### SNOMED CT Files (in `data/` directory):
- `sct2_Concept_Snapshot_INT_xxxxxxxx.txt`
- `sct2_Relationship_Snapshot_INT_xxxxxxxx.txt`  
- `sct2_RelationshipConcreteValues_Snapshot_INT_xxxxxxxx.txt`

**Current/Planned Versions:**
- German Release: 20241115 (semantic analysis)
- International: 202404, 202505 (comparison planned)
- Working version: 20250401

## Common Commands

### Graph Generation
```python
python GraphBuilder.py
```
Creates both IS-A only and full relation graphs, saves as pickle files.

### Distance Matrix Creation
```python
jupyter notebook BuildOBDSMatrix.ipynb
```
Generates semantic distance matrices for oBDS concept lists.

### Similarity Calculations
```python
python Main.py
```
Calculates semantic similarity between concept pairs.

**Available Measures:**
- WuPalmer, ChoiKim, LeacockChodorow
- BatetSanchezValls, Resnik, Lin, JiangConrathDissimilarity

### Quality Analysis (R)
```r
source("Krippendorff-Alpha-Code.R")  # Basic agreement
source("Kripp_Taxonomy_functioncall.R")  # Semantic agreement
```

## Architecture Notes

**Graph Types:**
- IS-A graph: Hierarchical relationships only (116680003)
- Full relation graph: All SNOMED CT relationships
- Root concept: 138875005

**Key Design Decisions:**
- NetworkX directed graphs with concepts → general concepts
- Pickle serialization for large graphs
- String-based SNOMED CT IDs
- Tab-separated RF2 file parsing

## Data Quality and Processing

### Known Data Quality Issues
**Excel/Pandas Import Issues:**
- **Float conversion**: SNOMED IDs converted to floats (e.g., `439401001.0`) due to pandas treating columns with NaN as float64
- **Scientific notation**: Large concept IDs shown as `9.00000000000465e+17` 
- **Multi-value cells**: Multiple SNOMED IDs in single cells separated by line breaks
- **Non-breaking spaces**: Unicode character 160 at start of concept IDs
- **SNOMED annotations**: Concepts with system codes like `439401001 (SCT)`
- **Full expressions**: Complete SNOMED expressions like `16633941000119101 | Description |`

### Data Cleaning Pipeline
1. **Remove workflow comments** from Modul 11 (pilot module contained project notes)
2. **Convert dash placeholders** (`-`) to missing values  
3. **Fix pandas float conversion** by removing `.0` endings from valid integers
4. **Handle multi-value entries** by extracting first concept, logging others for gap analysis
5. **Manual mapping for scientific notation** (Excel scientific notation cases)
6. **Fix data entry typos** (e.g., missing first digit in concept IDs)
7. **Extract concept IDs** from annotations and full expressions
8. **Clean Unicode whitespace** issues

### Scientific Notation and Typo Corrections
**Critical Issue**: Excel scientific notation (`9.00000000000465e+17`) cannot be reliably converted using float precision. Manual mapping required:

- `9.00000000000465e+17` → `20558004` (valid at mapping time, inactivated 2024-07-01)
- `9.00000000000519e+17` → `394617004` (valid at mapping time, inactivated 2024-05-01)  
- `9.11753521000004e+17` → `444025001` (typo - lost first digit)
- `44025001` → `444025001` (typo correction - missing first digit)

**Lesson**: Float conversion loses precision for 18-digit numbers. Always use manual mapping for scientific notation in research data.

### Current Data State
- **579 total oBDS concepts** across 19 modules after cleaning
- **600 unique SNOMED concepts** used by 4 mappers after corrections
- **99.2% validation success** against SNOMED CT 2025-02-01 release (595/600 valid)
- **Missing value patterns** vary significantly by mapper and module

## Scientific Standards Required

### Code Quality Requirements
- **Reproducible workflows**: Every data transformation documented with exact counts
- **Proper variable management**: No lost variables or undefined names
- **Traceable changes**: Complete audit trail of all data modifications
- **Validated steps**: Each processing step verified before proceeding
- **Precise documentation**: Scientific language, not vague "fixed errors"

### Research Outputs Required
1. **Mapper agreement analysis** using Krippendorff's Alpha (standard and semantic)
2. **Gap analysis** for BfArM submission of missing SNOMED concepts
3. **Multi-value case analysis** where mappers selected multiple concepts
4. **Module-specific quality metrics** and agreement patterns

## Results Summary

**Current Status**: Data cleaning and validation completed
**Next Steps**: Krippendorff Alpha calculation and gap analysis
**Quality Standards**: Must meet rigorous scientific computing standards