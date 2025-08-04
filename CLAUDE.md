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
- 4 independent mappers (Nina, Sophie, Paul, Lotte, Thomas MII Onko)
- Tools used: SNOMED Browser, Basisdatensatz.de, implementation guides
- Focus: Clinical data points relevant to MII Onko (no personal/reporting data)

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

**Data Quality Considerations:**
- ~10 validation errors in concept lists (Excel scientific notation, invalid codes)
- Missing value handling in Krippendorff: pairwise deletion recommended
- Distance matrix infinity values cause issues in semantic weighting

## Results Summary

**Overall Krippendorff's Alpha**: 0.382 (standard, no placeholders)
**Module-specific**: Varies significantly across oBDS modules
**Semantic weighting**: Implementation completed but requires distance matrix validation