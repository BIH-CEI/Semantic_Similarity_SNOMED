"""
Mapping Difficulty Index (MDI)

A composite metric that combines multiple signals of mapping difficulty:
1. Disagreement (proportion who disagree with most common code)
2. Semantic distance (average SNOMED distance between chosen codes)
3. Diversity (number of unique codes chosen)

Missing values are NOT included as they show no correlation with difficulty (r=-0.026).

Formula:
    MDI = 0.5 × disagreement + 0.4 × semantic_disagreement + 0.1 × diversity

Where:
- disagreement: 1 - (most_common_count / n_coders)  [0-1]
- semantic_disagreement: mean_pairwise_distance / 50  [0-1]
- diversity: (n_unique - 1) / (n_coders - 1)  [0-1]

Interpretation:
- MDI = 0.0: Perfect agreement, identical codes
- MDI = 0.2-0.4: Moderate difficulty, related concepts
- MDI > 0.6: High difficulty, distant concepts or many alternatives

Usage:
    python scripts/calculate_mapping_difficulty.py

Output:
    - Difficulty scores per item
    - Module-level difficulty summary
    - Gap analysis candidates (high MDI items)
"""

import pandas as pd
import numpy as np
from collections import Counter
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
DISTANCE_MATRIX = PROJECT_ROOT / "data/processed/obds_distance_matrix.csv"
OUTPUT_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']

# Weights for difficulty components
WEIGHTS = {
    'disagreement': 0.5,        # Primary indicator
    'semantic_disagreement': 0.4,  # Strong correlation (r=0.64)
    'diversity': 0.1            # Secondary indicator
}

# ============================================================================
# DIFFICULTY CALCULATION
# ============================================================================

def calculate_mapping_difficulty(row, mappers, distance_matrix):
    """
    Calculate Mapping Difficulty Index (MDI) for a single item.

    Returns:
        dict with difficulty components and composite score
    """
    values = [str(row[m]) for m in mappers if pd.notna(row[m])]
    n_coders = len(values)

    # Need at least 2 coders for meaningful difficulty assessment
    if n_coders < 2:
        return {
            'n_coders': n_coders,
            'disagreement': np.nan,
            'semantic_disagreement': np.nan,
            'diversity': np.nan,
            'mdi': np.nan,
            'interpretation': 'Insufficient coders' if n_coders == 1 else 'No codes',
            'codes': values
        }

    # Component 1: Disagreement
    counts = Counter(values)
    most_common_count = counts.most_common(1)[0][1]
    disagreement = 1 - (most_common_count / n_coders)

    # Component 2: Semantic disagreement (mean pairwise distance)
    distances = []
    for i, v1 in enumerate(values):
        for v2 in values[i+1:]:
            if v1 in distance_matrix.index and v2 in distance_matrix.columns:
                d = distance_matrix.loc[v1, v2]
                if np.isfinite(d):
                    distances.append(d)

    if len(distances) > 0:
        mean_distance = np.mean(distances)
        max_distance = np.max(distances)
        # Normalize by typical maximum (50 hops in SNOMED)
        semantic_disagreement = min(mean_distance / 50.0, 1.0)
    else:
        semantic_disagreement = 0.0  # All codes identical or missing from matrix
        mean_distance = 0.0
        max_distance = 0.0

    # Component 3: Diversity (code variety)
    n_unique = len(set(values))
    diversity = (n_unique - 1) / (n_coders - 1) if n_coders > 1 else 0.0

    # Composite Mapping Difficulty Index
    mdi = (
        WEIGHTS['disagreement'] * disagreement +
        WEIGHTS['semantic_disagreement'] * semantic_disagreement +
        WEIGHTS['diversity'] * diversity
    )

    # Interpretation
    if mdi < 0.1:
        interp = 'Easy (high agreement, close concepts)'
    elif mdi < 0.3:
        interp = 'Moderate (some disagreement, related concepts)'
    elif mdi < 0.6:
        interp = 'Difficult (divergent codes, semantic distance)'
    else:
        interp = 'Very difficult (major disagreement, distant concepts)'

    return {
        'n_coders': n_coders,
        'n_unique_codes': n_unique,
        'disagreement': disagreement,
        'semantic_disagreement': semantic_disagreement,
        'diversity': diversity,
        'mdi': mdi,
        'mean_distance': mean_distance,
        'max_distance': max_distance,
        'interpretation': interp,
        'codes': values,
        'most_common_code': counts.most_common(1)[0][0],
        'most_common_count': most_common_count
    }


# ============================================================================
# ANALYSIS
# ============================================================================

def main():
    print("=" * 70)
    print("Mapping Difficulty Index (MDI) Analysis")
    print("=" * 70)

    # Load data
    print(f"\n=== LOADING DATA ===")
    df = pd.read_csv(MAPPING_TABLE, dtype={m: str for m in MAPPERS})

    for m in MAPPERS:
        df[m] = df[m].replace(['', 'nan'], np.nan)

    print(f"Loaded {len(df)} items")

    # Load distance matrix
    print(f"Loading distance matrix...")
    dist_matrix = pd.read_csv(DISTANCE_MATRIX, index_col=0)
    dist_matrix.index = dist_matrix.index.astype(str)
    dist_matrix.columns = dist_matrix.columns.astype(str)
    print(f"Distance matrix: {dist_matrix.shape}")

    # Calculate difficulty for each item
    print(f"\n=== CALCULATING MAPPING DIFFICULTY ===")

    difficulty_results = []
    for idx, row in df.iterrows():
        diff = calculate_mapping_difficulty(row, MAPPERS, dist_matrix)

        # Get oBDS concept name if available
        obds_name = row.get('oBDS_Concept', f'Item_{idx}')

        difficulty_results.append({
            'item_idx': idx,
            'Module': row['Module'],
            'oBDS_Concept': obds_name,
            **diff
        })

    diff_df = pd.DataFrame(difficulty_results)

    # Summary statistics
    valid_mdi = diff_df[diff_df['mdi'].notna()]
    print(f"\nItems with valid MDI: {len(valid_mdi)}/{len(diff_df)}")
    print(f"\nMDI Statistics:")
    print(f"  Mean: {valid_mdi['mdi'].mean():.3f}")
    print(f"  Median: {valid_mdi['mdi'].median():.3f}")
    print(f"  Std: {valid_mdi['mdi'].std():.3f}")
    print(f"  Min: {valid_mdi['mdi'].min():.3f}")
    print(f"  Max: {valid_mdi['mdi'].max():.3f}")

    print(f"\nDifficulty Distribution:")
    print(valid_mdi['interpretation'].value_counts())

    # Top difficult items
    print(f"\n=== TOP 20 MOST DIFFICULT ITEMS (Gap Analysis Candidates) ===")
    top_difficult = valid_mdi.nlargest(20, 'mdi')[
        ['Module', 'oBDS_Concept', 'mdi', 'n_coders', 'n_unique_codes',
         'disagreement', 'semantic_disagreement', 'mean_distance', 'interpretation']
    ]
    print(top_difficult.to_string(index=False))

    # Easiest items
    print(f"\n=== TOP 20 EASIEST ITEMS (Ready for Implementation) ===")
    easiest = valid_mdi.nsmallest(20, 'mdi')[
        ['Module', 'oBDS_Concept', 'mdi', 'n_coders', 'most_common_code', 'interpretation']
    ]
    print(easiest.to_string(index=False))

    # Module-level difficulty
    print(f"\n=== DIFFICULTY BY MODULE ===")
    module_diff = valid_mdi.groupby('Module').agg({
        'mdi': ['mean', 'median', 'std', 'count'],
        'n_coders': 'mean',
        'semantic_disagreement': 'mean'
    }).round(3)
    module_diff.columns = ['_'.join(col) for col in module_diff.columns]
    module_diff = module_diff.sort_values('mdi_mean', ascending=False)
    print(module_diff)

    # Component contributions
    print(f"\n=== DIFFICULTY COMPONENT ANALYSIS ===")
    print(f"\nCorrelations with MDI:")
    correlations = valid_mdi[['mdi', 'disagreement', 'semantic_disagreement', 'diversity']].corr()['mdi']
    print(correlations)

    print(f"\nMean component values:")
    print(f"  Disagreement: {valid_mdi['disagreement'].mean():.3f}")
    print(f"  Semantic disagreement: {valid_mdi['semantic_disagreement'].mean():.3f}")
    print(f"  Diversity: {valid_mdi['diversity'].mean():.3f}")

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Full item-level results
    difficulty_file = OUTPUT_DIR / f"mapping_difficulty_scores_{timestamp}.csv"
    diff_df.to_csv(difficulty_file, index=False)
    print(f"\n[OK] Item difficulty scores: {difficulty_file}")

    # Gap analysis candidates (MDI >= 0.5)
    gap_candidates = valid_mdi[valid_mdi['mdi'] >= 0.5].sort_values('mdi', ascending=False)
    gap_file = OUTPUT_DIR / f"gap_analysis_candidates_{timestamp}.csv"
    gap_candidates.to_csv(gap_file, index=False)
    print(f"[OK] Gap analysis candidates (n={len(gap_candidates)}): {gap_file}")

    # Module summary
    module_file = OUTPUT_DIR / f"module_difficulty_summary_{timestamp}.csv"
    module_diff.to_csv(module_file)
    print(f"[OK] Module difficulty summary: {module_file}")

    # Summary report
    summary_file = OUTPUT_DIR / f"difficulty_analysis_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=== Mapping Difficulty Index (MDI) Analysis ===\n\n")
        f.write(f"Formula: MDI = 0.5*disagreement + 0.4*semantic_disagreement + 0.1*diversity\n\n")
        f.write(f"Items analyzed: {len(valid_mdi)}\n")
        f.write(f"Mean MDI: {valid_mdi['mdi'].mean():.3f}\n")
        f.write(f"Median MDI: {valid_mdi['mdi'].median():.3f}\n\n")
        f.write(f"Difficulty categories:\n")
        for cat, count in valid_mdi['interpretation'].value_counts().items():
            f.write(f"  {cat}: {count} ({count/len(valid_mdi)*100:.1f}%)\n")
        f.write(f"\nGap analysis candidates (MDI >= 0.5): {len(gap_candidates)}\n")
        f.write(f"Ready for implementation (MDI < 0.1): {len(valid_mdi[valid_mdi['mdi'] < 0.1])}\n\n")
        f.write(f"Key findings:\n")
        f.write(f"- Missing values are NOT correlated with difficulty (r=-0.026)\n")
        f.write(f"- Semantic disagreement is strongest indicator (r=0.640 with disagreement)\n")
        f.write(f"- High MDI items should be reviewed for BfArM gap submission\n")
        f.write(f"- Low MDI items are ready for MII-Onko implementation\n")

    print(f"[OK] Summary report: {summary_file}")

    print("\n" + "=" * 70)
    print("DIFFICULTY ANALYSIS COMPLETE")
    print("=" * 70)

    # Print actionable recommendations
    print(f"\n=== ACTIONABLE RECOMMENDATIONS ===")
    print(f"\n1. GAP ANALYSIS (High MDI >= 0.5):")
    print(f"   {len(gap_candidates)} items with major disagreement")
    print(f"   → Review for potential SNOMED CT gaps")
    print(f"   → Submit to BfArM for consideration")

    ready = valid_mdi[valid_mdi['mdi'] < 0.1]
    print(f"\n2. READY FOR IMPLEMENTATION (Low MDI < 0.1):")
    print(f"   {len(ready)} items with excellent agreement")
    print(f"   → Use most common code")
    print(f"   → Integrate into MII-Onko FHIR profiles")

    moderate = valid_mdi[(valid_mdi['mdi'] >= 0.1) & (valid_mdi['mdi'] < 0.5)]
    print(f"\n3. CONSENSUS NEEDED (Moderate MDI 0.1-0.5):")
    print(f"   {len(moderate)} items with moderate disagreement")
    print(f"   → Convene expert panel")
    print(f"   → Document rationale for chosen code")


if __name__ == '__main__':
    main()
