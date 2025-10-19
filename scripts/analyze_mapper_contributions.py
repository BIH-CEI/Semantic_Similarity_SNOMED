"""
Leave-One-Out Mapper Contribution Analysis

Performs jackknife resampling to assess individual mapper contributions
to inter-rater agreement metrics.

Research Questions:
1. How does each mapper's removal affect Krippendorff's Alpha?
2. Which mapper contributes most to consensus vs. diversity?
3. Are the findings robust across different mapper combinations?

Methodology:
- Calculate alpha with all 4 mappers (baseline)
- Calculate alpha with each 3-mapper combination (leave-one-out)
- Compare changes in agreement metrics
- Visualize mapper contributions

Usage:
    python scripts/analyze_mapper_contributions.py

Output:
    - Mapper contribution metrics (CSV)
    - Visualization comparing all combinations
    - Statistical summary
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from itertools import combinations

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
DISTANCE_MATRIX = PROJECT_ROOT / "data/processed/obds_distance_matrix.csv"
OUTPUT_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = OUTPUT_DIR / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']

# ============================================================================
# KRIPPENDORFF'S ALPHA CALCULATION
# ============================================================================

def krippendorff_alpha(data, distance_function=None):
    """
    Calculate Krippendorff's Alpha for nominal or metric data.

    Args:
        data: DataFrame with items as rows, raters as columns
        distance_function: Optional distance function (for semantic alpha)

    Returns:
        float: Krippendorff's Alpha value
    """
    # Convert to numpy array
    values = data.values
    n_items, n_raters = values.shape

    # Create coincidence matrix
    units = []
    for i in range(n_items):
        row_values = [v for v in values[i] if pd.notna(v)]
        if len(row_values) >= 2:  # Need at least 2 raters
            units.append(row_values)

    if len(units) == 0:
        return np.nan

    # Build pairable values
    all_values = []
    for unit in units:
        all_values.extend(unit)

    # Get unique categories
    categories = sorted(set(all_values))
    n_categories = len(categories)

    if n_categories <= 1:
        return np.nan

    # Coincidence matrix
    coincidence = np.zeros((n_categories, n_categories))

    for unit in units:
        n = len(unit)
        for i, v1 in enumerate(unit):
            for v2 in unit:
                if v1 != v2 or i == 0:  # Count all pairs
                    c1 = categories.index(v1)
                    c2 = categories.index(v2)
                    coincidence[c1, c2] += 1.0 / (n - 1) if n > 1 else 0

    # Nominal distance (or use custom distance function)
    if distance_function is None:
        # Nominal: distance = 1 if different, 0 if same
        distance_matrix = 1 - np.eye(n_categories)
    else:
        # Custom distance function
        distance_matrix = np.zeros((n_categories, n_categories))
        for i, c1 in enumerate(categories):
            for j, c2 in enumerate(categories):
                distance_matrix[i, j] = distance_function(c1, c2)

    # Calculate observed disagreement
    D_o = 0
    for i in range(n_categories):
        for j in range(n_categories):
            D_o += coincidence[i, j] * distance_matrix[i, j]

    # Calculate expected disagreement
    n_total = coincidence.sum()
    n_c = coincidence.sum(axis=1)

    D_e = 0
    for i in range(n_categories):
        for j in range(n_categories):
            if i != j:
                D_e += n_c[i] * n_c[j] * distance_matrix[i, j]

    D_e = D_e / (n_total - 1) if n_total > 1 else 0

    # Alpha = 1 - (D_o / D_e)
    if D_e == 0:
        return np.nan

    alpha = 1 - (D_o / D_e)
    return alpha


def calculate_alpha_for_mappers(df, mappers, semantic=False, distance_matrix=None):
    """
    Calculate Krippendorff's Alpha for a specific set of mappers.

    Args:
        df: DataFrame with mapping data
        mappers: List of mapper column names to include
        semantic: Whether to use semantic distances
        distance_matrix: SNOMED distance matrix for semantic calculation

    Returns:
        dict with alpha and metadata
    """
    # Select only specified mappers
    data = df[mappers].copy()

    # Count valid items (at least 2 mappers responded)
    valid_items = 0
    for _, row in data.iterrows():
        n_valid = row.notna().sum()
        if n_valid >= 2:
            valid_items += 1

    if valid_items < 2:
        return {
            'alpha': np.nan,
            'n_items': valid_items,
            'n_mappers': len(mappers),
            'mappers': mappers
        }

    # Calculate alpha
    if semantic and distance_matrix is not None:
        # Create distance function
        def dist_func(c1, c2):
            if c1 == c2:
                return 0.0
            c1_str = str(int(float(c1))) if pd.notna(c1) else str(c1)
            c2_str = str(int(float(c2))) if pd.notna(c2) else str(c2)

            if c1_str in distance_matrix.index and c2_str in distance_matrix.columns:
                d = distance_matrix.loc[c1_str, c2_str]
                if np.isfinite(d):
                    return d / 50.0  # Normalize to [0, 1]
            return 1.0  # Maximum distance if not found

        alpha = krippendorff_alpha(data, distance_function=dist_func)
    else:
        alpha = krippendorff_alpha(data)

    return {
        'alpha': alpha,
        'n_items': valid_items,
        'n_mappers': len(mappers),
        'mappers': mappers
    }


# ============================================================================
# LEAVE-ONE-OUT ANALYSIS
# ============================================================================

def perform_leave_one_out_analysis(df, distance_matrix=None):
    """
    Perform leave-one-out analysis for all mapper combinations.

    Returns:
        DataFrame with results for each combination
    """
    results = []

    # Baseline: All 4 mappers
    print("\nCalculating baseline (all 4 mappers)...")
    baseline_nominal = calculate_alpha_for_mappers(df, MAPPERS, semantic=False)
    baseline_semantic = calculate_alpha_for_mappers(df, MAPPERS, semantic=True, distance_matrix=distance_matrix)

    results.append({
        'combination': 'All 4 mappers',
        'mappers': ', '.join(MAPPERS),
        'n_mappers': 4,
        'removed': 'None',
        'alpha_nominal': baseline_nominal['alpha'],
        'alpha_semantic': baseline_semantic['alpha'],
        'n_items': baseline_nominal['n_items']
    })

    # Leave-one-out: Remove each mapper
    print("\nCalculating leave-one-out combinations...")
    for mapper_to_remove in MAPPERS:
        remaining_mappers = [m for m in MAPPERS if m != mapper_to_remove]
        print(f"  Removing {mapper_to_remove}...")

        nominal = calculate_alpha_for_mappers(df, remaining_mappers, semantic=False)
        semantic = calculate_alpha_for_mappers(df, remaining_mappers, semantic=True, distance_matrix=distance_matrix)

        results.append({
            'combination': f'Without {mapper_to_remove}',
            'mappers': ', '.join(remaining_mappers),
            'n_mappers': 3,
            'removed': mapper_to_remove,
            'alpha_nominal': nominal['alpha'],
            'alpha_semantic': semantic['alpha'],
            'n_items': nominal['n_items']
        })

    # Additional: All 3-mapper combinations (not just leave-one-out)
    print("\nCalculating all 3-mapper combinations...")
    for mapper_combo in combinations(MAPPERS, 3):
        mapper_list = list(mapper_combo)
        removed = [m for m in MAPPERS if m not in mapper_list][0]

        # Skip if already calculated in leave-one-out
        if removed in MAPPERS:
            continue

    results_df = pd.DataFrame(results)

    # Calculate deltas from baseline
    baseline_nom = results_df.iloc[0]['alpha_nominal']
    baseline_sem = results_df.iloc[0]['alpha_semantic']

    results_df['delta_nominal'] = results_df['alpha_nominal'] - baseline_nom
    results_df['delta_semantic'] = results_df['alpha_semantic'] - baseline_sem

    return results_df


# ============================================================================
# VISUALIZATION
# ============================================================================

def create_contribution_visualization(results_df):
    """
    Create comprehensive visualization of mapper contributions.
    """
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # Extract baseline and leave-one-out results
    baseline = results_df[results_df['removed'] == 'None'].iloc[0]
    loo_results = results_df[results_df['removed'] != 'None'].copy()

    # ========================================================================
    # SUBPLOT 1: Alpha values comparison
    # ========================================================================
    ax1 = fig.add_subplot(gs[0, :])

    x = np.arange(len(results_df))
    width = 0.35

    bars1 = ax1.bar(x - width/2, results_df['alpha_nominal'], width,
                    label='Standard Alpha', color='#3498db', alpha=0.8)
    bars2 = ax1.bar(x + width/2, results_df['alpha_semantic'], width,
                    label='Semantic Alpha (Full)', color='#27ae60', alpha=0.8)

    # Add baseline line
    ax1.axhline(y=baseline['alpha_nominal'], color='#3498db',
                linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (Nominal)')
    ax1.axhline(y=baseline['alpha_semantic'], color='#27ae60',
                linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (Semantic)')

    ax1.set_xlabel('Mapper Combination', fontweight='bold', fontsize=11)
    ax1.set_ylabel("Krippendorff's Alpha", fontweight='bold', fontsize=11)
    ax1.set_title("Leave-One-Out Analysis: Impact on Inter-Rater Agreement",
                  fontweight='bold', fontsize=13, pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(results_df['combination'], rotation=45, ha='right')
    ax1.legend(loc='lower right')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, 1.0)

    # ========================================================================
    # SUBPLOT 2: Delta from baseline (Nominal)
    # ========================================================================
    ax2 = fig.add_subplot(gs[1, 0])

    colors_nominal = ['#e74c3c' if d < 0 else '#27ae60' for d in loo_results['delta_nominal']]
    bars = ax2.barh(loo_results['removed'], loo_results['delta_nominal'],
                    color=colors_nominal, alpha=0.7, edgecolor='black')

    # Add value labels
    for i, (removed, delta) in enumerate(zip(loo_results['removed'], loo_results['delta_nominal'])):
        ax2.text(delta + 0.002 if delta >= 0 else delta - 0.002, i,
                f'{delta:+.4f}', va='center',
                ha='left' if delta >= 0 else 'right', fontsize=9)

    ax2.axvline(x=0, color='black', linewidth=1)
    ax2.set_xlabel('Δ Alpha (vs. baseline)', fontweight='bold', fontsize=10)
    ax2.set_ylabel('Removed Mapper', fontweight='bold', fontsize=10)
    ax2.set_title('Standard Alpha: Change from Baseline\n(Negative = mapper contributes to agreement)',
                  fontweight='bold', fontsize=11)
    ax2.grid(axis='x', alpha=0.3)

    # ========================================================================
    # SUBPLOT 3: Delta from baseline (Semantic)
    # ========================================================================
    ax3 = fig.add_subplot(gs[1, 1])

    colors_semantic = ['#e74c3c' if d < 0 else '#27ae60' for d in loo_results['delta_semantic']]
    bars = ax3.barh(loo_results['removed'], loo_results['delta_semantic'],
                    color=colors_semantic, alpha=0.7, edgecolor='black')

    # Add value labels
    for i, (removed, delta) in enumerate(zip(loo_results['removed'], loo_results['delta_semantic'])):
        ax3.text(delta + 0.002 if delta >= 0 else delta - 0.002, i,
                f'{delta:+.4f}', va='center',
                ha='left' if delta >= 0 else 'right', fontsize=9)

    ax3.axvline(x=0, color='black', linewidth=1)
    ax3.set_xlabel('Δ Alpha (vs. baseline)', fontweight='bold', fontsize=10)
    ax3.set_ylabel('Removed Mapper', fontweight='bold', fontsize=10)
    ax3.set_title('Semantic Alpha: Change from Baseline\n(Negative = mapper contributes to agreement)',
                  fontweight='bold', fontsize=11)
    ax3.grid(axis='x', alpha=0.3)

    # ========================================================================
    # SUBPLOT 4: Mapper contribution summary
    # ========================================================================
    ax4 = fig.add_subplot(gs[2, :])

    # Create summary table
    summary_data = []
    for _, row in loo_results.iterrows():
        summary_data.append([
            row['removed'],
            f"{row['alpha_nominal']:.4f}",
            f"{row['delta_nominal']:+.4f}",
            f"{row['alpha_semantic']:.4f}",
            f"{row['delta_semantic']:+.4f}",
            'Increases agreement' if row['delta_nominal'] < 0 and row['delta_semantic'] < 0 else
            'Decreases agreement' if row['delta_nominal'] > 0 and row['delta_semantic'] > 0 else
            'Mixed effect'
        ])

    ax4.axis('tight')
    ax4.axis('off')

    table = ax4.table(cellText=summary_data,
                     colLabels=['Removed\nMapper', 'Alpha\n(Nominal)', 'Δ Alpha\n(Nominal)',
                               'Alpha\n(Semantic)', 'Δ Alpha\n(Semantic)', 'Interpretation'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0.1, 0.2, 0.8, 0.6])

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    # Color code cells
    for i in range(1, len(summary_data) + 1):
        # Delta nominal
        if float(summary_data[i-1][2]) < 0:
            table[(i, 2)].set_facecolor('#ffcccc')
        else:
            table[(i, 2)].set_facecolor('#ccffcc')

        # Delta semantic
        if float(summary_data[i-1][4]) < 0:
            table[(i, 4)].set_facecolor('#ffcccc')
        else:
            table[(i, 4)].set_facecolor('#ccffcc')

    ax4.set_title('Mapper Contribution Summary\nRed = Removal decreases agreement (mapper contributes to consensus)\nGreen = Removal increases agreement (mapper adds diversity)',
                  fontweight='bold', fontsize=11, pad=20)

    # ========================================================================
    # Save figure
    # ========================================================================
    plt.tight_layout()
    output_file = FIGURES_DIR / "fig7_mapper_contributions.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n  Saved: {output_file}")
    plt.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("Leave-One-Out Mapper Contribution Analysis")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    df = pd.read_csv(MAPPING_TABLE)
    distance_matrix = pd.read_csv(DISTANCE_MATRIX, index_col=0)

    print(f"  Loaded {len(df)} items")
    print(f"  Distance matrix: {distance_matrix.shape[0]} concepts")

    # Perform analysis
    results_df = perform_leave_one_out_analysis(df, distance_matrix)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"mapper_contributions_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

    # Create visualization
    print("\nCreating visualization...")
    create_contribution_visualization(results_df)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    baseline = results_df[results_df['removed'] == 'None'].iloc[0]
    print(f"\nBaseline (all 4 mappers):")
    print(f"  Standard Alpha:  {baseline['alpha_nominal']:.4f}")
    print(f"  Semantic Alpha:  {baseline['alpha_semantic']:.4f}")

    print(f"\nLeave-one-out results:")
    for _, row in results_df[results_df['removed'] != 'None'].iterrows():
        print(f"\n  Without {row['removed']}:")
        print(f"    Standard Alpha:  {row['alpha_nominal']:.4f} ({row['delta_nominal']:+.4f})")
        print(f"    Semantic Alpha:  {row['alpha_semantic']:.4f} ({row['delta_semantic']:+.4f})")

        if row['delta_nominal'] < 0 and row['delta_semantic'] < 0:
            print(f"    → Removing this mapper DECREASES agreement (contributes to consensus)")
        elif row['delta_nominal'] > 0 and row['delta_semantic'] > 0:
            print(f"    → Removing this mapper INCREASES agreement (adds diversity)")
        else:
            print(f"    → Mixed effect")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
