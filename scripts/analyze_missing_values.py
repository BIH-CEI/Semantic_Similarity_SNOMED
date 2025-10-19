"""
Analyze missing value patterns in oBDS mapping data.

This script analyzes how missing values (unmapped concepts) affect
Krippendorff's Alpha calculations and provides context for interpreting
agreement statistics.

Usage:
    python scripts/analyze_missing_values.py

Output:
    - Console report on missing value patterns
    - results/missing_values_analysis_YYYYMMDD.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
OUTPUT_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Mapper names - PSEUDONYMIZED for publication
# Original mapping: Nina -> Mapper_A, Sophie -> Mapper_B, Paul -> Mapper_C, Lotte -> Mapper_D
MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']
MAPPER_PSEUDONYM_MAP = {
    'Nina': 'Mapper_A',
    'Sophie': 'Mapper_B',
    'Paul': 'Mapper_C',
    'Lotte': 'Mapper_D'
}


def analyze_missing_patterns(df):
    """Analyze missing value patterns across mappers."""
    print("=" * 70)
    print("MISSING VALUE ANALYSIS")
    print("=" * 70)

    # Replace empty strings with NaN
    for mapper in MAPPERS:
        df[mapper] = df[mapper].replace('', np.nan)

    # Overall statistics
    print("\n=== OVERALL MISSING VALUES ===")
    n_total = len(df)
    for mapper in MAPPERS:
        missing = df[mapper].isna().sum()
        pct = missing / n_total * 100
        present = n_total - missing
        print(f"{mapper:8s}: {present:3d} present, {missing:3d} missing ({pct:5.1f}%)")

    # Agreement patterns
    print("\n=== MAPPER COVERAGE PATTERNS ===")
    coverage = df[MAPPERS].notna().sum(axis=1)

    all_4 = (coverage == 4).sum()
    exactly_3 = (coverage == 3).sum()
    exactly_2 = (coverage == 2).sum()
    exactly_1 = (coverage == 1).sum()
    none_0 = (coverage == 0).sum()

    print(f"All 4 mappers:     {all_4:3d} concepts ({all_4/n_total*100:5.1f}%)")
    print(f"Exactly 3 mappers: {exactly_3:3d} concepts ({exactly_3/n_total*100:5.1f}%)")
    print(f"Exactly 2 mappers: {exactly_2:3d} concepts ({exactly_2/n_total*100:5.1f}%)")
    print(f"Exactly 1 mapper:  {exactly_1:3d} concepts ({exactly_1/n_total*100:5.1f}%)")
    print(f"No mappers:        {none_0:3d} concepts ({none_0/n_total*100:5.1f}%)")

    # Per-module analysis
    print("\n=== MISSING VALUES BY MODULE ===")
    print(f"{'Module':<15} {'N':>5} {'Mapper_A%':>10} {'Mapper_B%':>10} {'Mapper_C%':>10} {'Mapper_D%':>10} {'AnyMiss':>8}")
    print("-" * 80)

    module_stats = []
    for module in df['Module'].unique():
        module_df = df[df['Module'] == module]
        n = len(module_df)

        stats = {
            'Module': module,
            'N': n,
        }

        for mapper in MAPPERS:
            missing = module_df[mapper].isna().sum()
            pct = missing / n * 100
            stats[f'{mapper}_missing'] = missing
            stats[f'{mapper}_pct'] = pct

        # At least one mapper missing
        any_missing = module_df[MAPPERS].isna().any(axis=1).sum()
        stats['any_missing'] = any_missing
        stats['any_missing_pct'] = any_missing / n * 100

        module_stats.append(stats)

        print(f"{module:<15} {n:>5d} {stats['Mapper_A_pct']:>9.1f}% {stats['Mapper_B_pct']:>9.1f}% "
              f"{stats['Mapper_C_pct']:>9.1f}% {stats['Mapper_D_pct']:>9.1f}% {stats['any_missing_pct']:>7.1f}%")

    return pd.DataFrame(module_stats)


def analyze_disagreement_with_missing(df):
    """Analyze relationship between missing values and disagreement."""
    print("\n=== DISAGREEMENT PATTERNS ===")

    # Replace empty with NaN
    for mapper in MAPPERS:
        df[mapper] = df[mapper].replace('', np.nan)

    # Perfect agreement (all non-missing values are identical)
    def check_agreement(row):
        values = [row[m] for m in MAPPERS if pd.notna(row[m])]
        if len(values) < 2:
            return 'insufficient'  # Can't assess agreement with <2 mappers
        elif len(set(values)) == 1:
            return 'perfect'
        else:
            return 'disagreement'

    df['agreement_status'] = df.apply(check_agreement, axis=1)

    print("\nAgreement status across all concepts:")
    for status in ['perfect', 'disagreement', 'insufficient']:
        count = (df['agreement_status'] == status).sum()
        pct = count / len(df) * 100
        print(f"  {status:15s}: {count:3d} ({pct:5.1f}%)")

    # Break down by mapper coverage
    print("\nAgreement by mapper coverage:")
    coverage = df[MAPPERS].notna().sum(axis=1)

    for n_mappers in [4, 3, 2]:
        subset = df[coverage == n_mappers]
        if len(subset) == 0:
            continue

        perfect = (subset['agreement_status'] == 'perfect').sum()
        disagree = (subset['agreement_status'] == 'disagreement').sum()

        print(f"  {n_mappers} mappers ({len(subset):3d} concepts): "
              f"{perfect:3d} perfect ({perfect/len(subset)*100:5.1f}%), "
              f"{disagree:3d} disagree ({disagree/len(subset)*100:5.1f}%)")


def main():
    print("=" * 70)
    print("Missing Value Analysis for oBDS Mapping Data")
    print("=" * 70)

    # Load data
    print(f"\nLoading: {MAPPING_TABLE}")
    df = pd.read_csv(MAPPING_TABLE)

    # Pseudonymize mapper column names
    df = df.rename(columns=MAPPER_PSEUDONYM_MAP)

    print(f"Loaded {len(df)} concepts from {df['Module'].nunique()} modules")
    print(f"Mapper names pseudonymized for publication")

    # Analyze missing patterns
    module_stats = analyze_missing_patterns(df.copy())

    # Analyze disagreement patterns
    analyze_disagreement_with_missing(df.copy())

    # Export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"missing_values_analysis_{timestamp}.csv"
    module_stats.to_csv(output_file, index=False)

    print(f"\n=== OUTPUT ===")
    print(f"Detailed statistics saved to: {output_file}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nKEY INTERPRETATION POINTS:")
    print("- Missing values reduce effective sample size for agreement calculation")
    print("- Krippendorff's Alpha handles missing data but agreement is only")
    print("  calculated between mappers who both provided a code")
    print("- Low coverage (many missing) = less reliable Alpha estimates")
    print("- Disagreement can only occur when 2+ mappers provided codes")
    print("=" * 70)


if __name__ == '__main__':
    main()
