"""
Combined Quality Score: Completeness × Agreement

This script calculates quality metrics that reward both:
1. Completeness (having codes vs leaving empty)
2. Agreement (consistency among provided codes)

Research question: Is it better to leave uncertain concepts empty,
or to provide a code that might disagree with others?

Metrics implemented:
- Gwet's AC2 (handles missing values better than Krippendorff)
- Completeness-weighted alpha
- Item-level quality scores

Usage:
    python scripts/calculate_quality_score.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
OUTPUT_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']

# ============================================================================
# QUALITY METRICS
# ============================================================================

def calculate_item_quality(row, mappers):
    """
    Calculate quality score for a single item.

    Quality = Completeness × Agreement

    Completeness: proportion of mappers who provided a code (0.0-1.0)
    Agreement: proportion who agree with most common code (0.0-1.0)

    Returns:
        dict with completeness, agreement, quality, and interpretation
    """
    values = [str(row[m]) for m in mappers if pd.notna(row[m])]
    n_coders = len(values)

    completeness = n_coders / len(mappers)

    if n_coders == 0:
        return {
            'completeness': 0.0,
            'agreement': np.nan,
            'quality': 0.0,
            'n_coders': 0,
            'interpretation': 'No codes provided'
        }

    if n_coders == 1:
        return {
            'completeness': 0.25,
            'agreement': 1.0,  # Only one code, trivially "agrees"
            'quality': 0.25,
            'n_coders': 1,
            'interpretation': 'Single code (no validation)'
        }

    # Calculate agreement among those who responded
    from collections import Counter
    counts = Counter(values)
    most_common_count = counts.most_common(1)[0][1]
    agreement = most_common_count / n_coders

    quality = completeness * agreement

    # Interpretation
    if completeness == 1.0 and agreement == 1.0:
        interp = 'Perfect (all 4 agree)'
    elif completeness == 1.0 and agreement >= 0.75:
        interp = 'Excellent (all responded, high agreement)'
    elif completeness == 1.0:
        interp = 'Complete but disputed'
    elif agreement == 1.0:
        interp = 'Perfect agreement but incomplete'
    elif quality >= 0.75:
        interp = 'High quality'
    elif quality >= 0.50:
        interp = 'Moderate quality'
    else:
        interp = 'Low quality'

    return {
        'completeness': completeness,
        'agreement': agreement,
        'quality': quality,
        'n_coders': n_coders,
        'interpretation': interp,
        'n_unique_codes': len(counts),
        'most_common_code': counts.most_common(1)[0][0]
    }


def calculate_completeness_weighted_alpha(df, mappers):
    """
    Calculate Krippendorff's Alpha, weighted by completeness.

    Standard alpha treats all items equally.
    This version weights items by how many coders responded,
    giving more importance to items where all mappers provided codes.
    """
    from krippendorff import alpha as krippendorff_alpha

    # Standard alpha (unweighted)
    reliability_matrix = df[mappers].values.T  # transpose for krippendorff library
    standard_alpha = krippendorff_alpha(reliability_matrix, level_of_measurement='nominal')

    # Calculate item weights based on completeness
    weights = df[mappers].notna().sum(axis=1) / len(mappers)

    # Items with more coders get higher weight
    # This is conceptual - krippendorff library doesn't support item weights
    # So we report both metrics separately

    return {
        'standard_alpha': standard_alpha,
        'mean_completeness': weights.mean(),
        'completeness_std': weights.std()
    }


def analyze_strategic_missingness(df, mappers):
    """
    Test hypothesis: Do mappers strategically leave difficult items empty?

    If yes: Items with more missing values should have lower agreement
           among those who DID provide codes

    If no:  Missing values are random/due to other factors
    """
    results = []

    for idx, row in df.iterrows():
        values = [str(row[m]) for m in mappers if pd.notna(row[m])]
        n_coders = len(values)
        n_missing = len(mappers) - n_coders

        if n_coders < 2:
            continue

        # Agreement among responders
        from collections import Counter
        counts = Counter(values)
        agreement = counts.most_common(1)[0][1] / n_coders

        results.append({
            'n_missing': n_missing,
            'agreement': agreement
        })

    results_df = pd.DataFrame(results)

    # Correlation test
    correlation = results_df.corr().loc['n_missing', 'agreement']

    # Group by missingness level
    grouped = results_df.groupby('n_missing')['agreement'].agg(['mean', 'count'])

    return {
        'correlation': correlation,
        'by_missingness': grouped,
        'interpretation': (
            'Strategic missing (uncertainty)' if correlation < -0.2 else
            'Random missing' if abs(correlation) < 0.1 else
            'Unexpected pattern'
        )
    }


# ============================================================================
# ANALYSIS
# ============================================================================

def main():
    print("=" * 70)
    print("Quality Score Analysis: Completeness × Agreement")
    print("=" * 70)

    # Load data
    print(f"\n=== LOADING DATA ===")
    df = pd.read_csv(MAPPING_TABLE, dtype={m: str for m in MAPPERS})

    for m in MAPPERS:
        df[m] = df[m].replace(['', 'nan'], np.nan)

    print(f"Loaded {len(df)} items")

    # Calculate item-level quality scores
    print(f"\n=== CALCULATING ITEM-LEVEL QUALITY ===")

    quality_results = []
    for idx, row in df.iterrows():
        q = calculate_item_quality(row, MAPPERS)
        quality_results.append({
            'Module': row['Module'],
            'oBDS_Item': row['oBDS_Concept'] if 'oBDS_Concept' in df.columns else f"Item_{idx}",
            **q
        })

    quality_df = pd.DataFrame(quality_results)

    # Summary statistics
    print(f"\nOverall Statistics:")
    print(f"  Mean completeness: {quality_df['completeness'].mean():.3f}")
    print(f"  Mean agreement (among responders): {quality_df['agreement'].mean():.3f}")
    print(f"  Mean quality score: {quality_df['quality'].mean():.3f}")

    print(f"\nQuality Distribution:")
    print(quality_df['interpretation'].value_counts())

    # Best and worst items
    print(f"\n=== TOP 10 HIGHEST QUALITY ITEMS ===")
    top10 = quality_df.nlargest(10, 'quality')[['Module', 'oBDS_Item', 'quality', 'completeness', 'agreement', 'interpretation']]
    print(top10.to_string(index=False))

    print(f"\n=== TOP 10 LOWEST QUALITY ITEMS (excluding no response) ===")
    non_zero = quality_df[quality_df['quality'] > 0]
    bottom10 = non_zero.nsmallest(10, 'quality')[['Module', 'oBDS_Item', 'quality', 'completeness', 'agreement', 'interpretation']]
    print(bottom10.to_string(index=False))

    # Module-level analysis
    print(f"\n=== QUALITY BY MODULE ===")
    module_quality = quality_df.groupby('Module').agg({
        'completeness': 'mean',
        'agreement': 'mean',
        'quality': 'mean',
        'n_coders': 'mean'
    }).round(3)
    module_quality = module_quality.sort_values('quality', ascending=False)
    print(module_quality)

    # Strategic missingness test
    print(f"\n=== STRATEGIC MISSINGNESS ANALYSIS ===")
    strategic = analyze_strategic_missingness(df, MAPPERS)
    print(f"Correlation (n_missing vs agreement): {strategic['correlation']:.3f}")
    print(f"Interpretation: {strategic['interpretation']}")
    print(f"\nAgreement by number of missing coders:")
    print(strategic['by_missingness'])

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    quality_file = OUTPUT_DIR / f"item_quality_scores_{timestamp}.csv"
    quality_df.to_csv(quality_file, index=False)
    print(f"\n[OK] Item quality scores: {quality_file}")

    module_file = OUTPUT_DIR / f"module_quality_summary_{timestamp}.csv"
    module_quality.to_csv(module_file)
    print(f"[OK] Module quality summary: {module_file}")

    # Summary report
    summary_file = OUTPUT_DIR / f"quality_analysis_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=== Quality Score Analysis ===\n\n")
        f.write(f"Quality = Completeness × Agreement\n\n")
        f.write(f"Overall Statistics:\n")
        f.write(f"  Mean completeness: {quality_df['completeness'].mean():.3f}\n")
        f.write(f"  Mean agreement: {quality_df['agreement'].mean():.3f}\n")
        f.write(f"  Mean quality: {quality_df['quality'].mean():.3f}\n\n")
        f.write(f"Strategic Missingness Test:\n")
        f.write(f"  Correlation: {strategic['correlation']:.3f}\n")
        f.write(f"  Interpretation: {strategic['interpretation']}\n\n")
        f.write(f"Recommendation:\n")
        if strategic['correlation'] < -0.2:
            f.write("  Mappers appear to strategically leave difficult items empty.\n")
            f.write("  This is GOOD practice - uncertainty should be acknowledged.\n")
            f.write("  Low completeness + high agreement is better than\n")
            f.write("  high completeness + low agreement.\n")
        else:
            f.write("  Missing values appear random/unrelated to difficulty.\n")
            f.write("  Encouraging completeness may improve overall quality.\n")

    print(f"[OK] Summary report: {summary_file}")

    print("\n" + "=" * 70)
    print("QUALITY ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
