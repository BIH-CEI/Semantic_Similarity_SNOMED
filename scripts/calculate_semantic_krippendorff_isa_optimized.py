"""
Calculate Semantic Krippendorff's Alpha for oBDS SNOMED Mappings - OPTIMIZED VERSION

This script calculates semantic (taxonomic) Krippendorff's Alpha using
SNOMED CT distance matrices to weight disagreements.

OPTIMIZATIONS:
- Vectorized coincidence matrix building
- Pre-computed value-to-index mapping
- Numpy boolean indexing instead of nested loops

Based on the R implementation from:
https://github.com/LiU-IMT/semantic_kripp_alpha

Usage:
    python scripts/calculate_semantic_krippendorff_isa_optimized.py

Output:
    - results/semantic_krippendorff_isa_overall_YYYYMMDD.txt
    - results/semantic_krippendorff_isa_by_module_YYYYMMDD.csv
    - Console output with comparison to standard alpha
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
# Use IS-A only distance matrix for comparison
DISTANCE_MATRIX = PROJECT_ROOT / "data/processed/obds_distance_matrix_isa.csv"

# Mapper names - PSEUDONYMIZED for publication
MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']
MAPPER_PSEUDONYM_MAP = {
    'Nina': 'Mapper_A',
    'Sophie': 'Mapper_B',
    'Paul': 'Mapper_C',
    'Lotte': 'Mapper_D'
}

# Output directory
OUTPUT_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# OPTIMIZED SEMANTIC KRIPPENDORFF'S ALPHA IMPLEMENTATION
# ============================================================================

def calculate_semantic_krippendorff_alpha_optimized(reliability_data, distance_matrix, verbose=False):
    """
    Calculate semantic Krippendorff's Alpha using taxonomic distance matrix.

    OPTIMIZED VERSION with vectorized operations.

    Args:
        reliability_data: DataFrame where rows=items, columns=coders
        distance_matrix: DataFrame with SNOMED concept distances
        verbose: Print debugging information

    Returns:
        dict with 'value', 'n_concepts', 'n_coders', 'coverage_in_matrix'
    """
    # Get all unique values in the data (already strings from CSV load)
    all_values = []
    for col in reliability_data.columns:
        values = reliability_data[col].dropna().unique()
        all_values.extend([str(v) for v in values])

    all_values_unique = sorted(set(all_values))

    # Filter to only values that exist in distance matrix
    all_values_in_matrix = [v for v in all_values_unique if v in distance_matrix.index]
    nval = len(all_values_in_matrix)

    if verbose:
        print(f"  Total unique concepts: {len(all_values_unique)}")
        print(f"  Concepts in distance matrix: {nval}")
        missing = set(all_values_unique) - set(all_values_in_matrix)
        if missing:
            print(f"  Missing from distance matrix: {missing}")

    if nval < 2:
        return {
            'value': np.nan,
            'n_concepts': len(reliability_data),
            'n_coders': len(reliability_data.columns),
            'coverage_in_matrix': 0 if nval == 0 else 1
        }

    # Pre-compute value to index mapping for fast lookup
    val_to_idx = {val: idx for idx, val in enumerate(all_values_in_matrix)}

    # Initialize coincidence matrix
    cm = np.zeros((nval, nval))

    # Convert reliability data to array format
    data_array = reliability_data.values  # items × coders
    n_items, n_coders = data_array.shape

    # Build coincidence matrix - OPTIMIZED
    if verbose:
        print(f"  Building coincidence matrix for {n_items} items...")

    for item_idx in range(n_items):
        if verbose and item_idx % 100 == 0:
            print(f"    Progress: {item_idx}/{n_items}")

        item_ratings = data_array[item_idx, :]
        valid_ratings = [str(r) for r in item_ratings if pd.notna(r)]

        if len(valid_ratings) < 2:
            continue

        mc = len(valid_ratings) - 1  # pairable values

        # Convert valid ratings to indices
        valid_indices = [val_to_idx.get(r) for r in valid_ratings if r in val_to_idx]

        if len(valid_indices) < 2:
            continue

        # Count all pairs
        for i, idx1 in enumerate(valid_indices):
            for idx2 in valid_indices:
                if idx1 is None or idx2 is None:
                    continue
                r_idx = min(idx1, idx2)
                c_idx = max(idx1, idx2)
                cm[r_idx, c_idx] += 1.0 / mc

    # Symmetrize the matrix
    cm = cm + cm.T - np.diag(np.diag(cm))

    # Calculate observed disagreement
    nmv = np.sum(cm)
    nc = np.sum(cm, axis=1)

    if verbose:
        print(f"  Total coincidences (nmv): {nmv:.2f}")
        print(f"  Marginal counts (nc): min={nc.min():.2f}, max={nc.max():.2f}")
        print(f"  Calculating disagreements...")

    # Pre-extract distance submatrix for all values in matrix
    dist_submatrix = distance_matrix.loc[all_values_in_matrix, all_values_in_matrix].values

    # Vectorized calculation of disagreements
    # Only compute upper triangle (k > c)
    observed_disagreement = 0
    expected_disagreement = 0

    for k in range(1, nval):
        # Vectorized operations for all c < k
        dist_squared = dist_submatrix[:k, k] ** 2

        # Filter out non-finite values
        finite_mask = np.isfinite(dist_squared)

        observed_disagreement += np.sum(cm[:k, k][finite_mask] * dist_squared[finite_mask])
        expected_disagreement += np.sum(nc[:k][finite_mask] * nc[k] * dist_squared[finite_mask])

    if verbose:
        print(f"  Observed disagreement: {observed_disagreement:.4f}")
        print(f"  Expected disagreement: {expected_disagreement:.4f}")

    # Calculate alpha
    if expected_disagreement == 0:
        alpha = 1.0
    else:
        alpha = 1 - (nmv - 1) * observed_disagreement / expected_disagreement

    return {
        'value': alpha,
        'n_concepts': n_items,
        'n_coders': n_coders,
        'coverage_in_matrix': len(all_values_in_matrix) / len(all_values_unique) if len(all_values_unique) > 0 else 0
    }


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load mapping table and distance matrix."""
    print("=" * 70)
    print("Semantic Krippendorff's Alpha Calculation (IS-A Only) - OPTIMIZED")
    print("=" * 70)

    # Load mapping table with explicit string dtypes for mapper columns
    print(f"\n=== LOADING MAPPING DATA ===")
    print(f"File: {MAPPING_TABLE}")

    # Force mapper columns to be read as strings to prevent float conversion
    dtype_dict = {mapper: str for mapper in MAPPERS}
    df = pd.read_csv(MAPPING_TABLE, dtype=dtype_dict)

    # Pseudonymize if needed (data should already be pseudonymized)
    if 'Nina' in df.columns:
        df = df.rename(columns=MAPPER_PSEUDONYM_MAP)
        print("Mapper columns pseudonymized")

    print(f"Loaded {len(df)} concepts from {df['Module'].nunique()} modules")

    # Replace empty strings and 'nan' with NaN
    for mapper in MAPPERS:
        df[mapper] = df[mapper].replace(['', 'nan'], np.nan)

    # Load distance matrix
    print(f"\n=== LOADING DISTANCE MATRIX ===")
    print(f"File: {DISTANCE_MATRIX}")
    dist_matrix = pd.read_csv(DISTANCE_MATRIX, index_col=0)

    # Ensure indices and columns are strings for proper matching
    dist_matrix.index = dist_matrix.index.astype(str)
    dist_matrix.columns = dist_matrix.columns.astype(str)

    print(f"Matrix size: {dist_matrix.shape}")
    print(f"Concepts covered: {len(dist_matrix)}")
    print(f"Distance range: {dist_matrix.min().min():.0f} to {dist_matrix.max().max():.0f}")

    # Calculate statistics
    flat_distances = dist_matrix.values.flatten()
    finite_distances = flat_distances[np.isfinite(flat_distances)]
    print(f"Mean distance: {finite_distances.mean():.2f}")
    print(f"Median distance: {np.median(finite_distances):.2f}")

    return df, dist_matrix


# ============================================================================
# ANALYSIS
# ============================================================================

def calculate_overall_semantic_alpha(df, dist_matrix):
    """Calculate overall semantic alpha."""
    print("\n=== OVERALL SEMANTIC ALPHA (IS-A ONLY) ===")

    reliability_matrix = df[MAPPERS].copy()

    result = calculate_semantic_krippendorff_alpha_optimized(
        reliability_matrix,
        dist_matrix,
        verbose=True
    )

    print(f"\nSemantic Krippendorff's Alpha (IS-A): {result['value']:.4f}")
    print(f"Coverage in distance matrix: {result['coverage_in_matrix']*100:.1f}%")

    return result


def calculate_per_module_semantic_alpha(df, dist_matrix):
    """Calculate semantic alpha per module."""
    print("\n=== PER-MODULE SEMANTIC ALPHA (IS-A ONLY) ===")

    module_results = []

    for module in sorted(df['Module'].unique()):
        module_mask = df['Module'] == module
        module_df = df[module_mask]
        module_matrix = module_df[MAPPERS].copy()

        if len(module_matrix) == 0:
            continue

        result = calculate_semantic_krippendorff_alpha_optimized(
            module_matrix,
            dist_matrix,
            verbose=False
        )

        module_results.append({
            'module': module,
            'n_concepts': result['n_concepts'],
            'alpha_semantic_isa': result['value'],
            'coverage_pct': result['coverage_in_matrix'] * 100
        })

        print(f"  {module}: alpha={result['value']:.4f}, coverage={result['coverage_in_matrix']*100:.0f}% (n={len(module_matrix)})")

    return pd.DataFrame(module_results)


# ============================================================================
# COMPARISON WITH FULL RELATIONS AND STANDARD ALPHA
# ============================================================================

def compare_with_other_results(semantic_isa_results):
    """Load and compare with full relations semantic and standard alpha results."""
    print("\n=== COMPARISON: STANDARD vs SEMANTIC (FULL) vs SEMANTIC (IS-A) ===")

    # Find most recent results
    standard_files = sorted(OUTPUT_DIR.glob("krippendorff_by_module_*.csv"))
    semantic_files = sorted(OUTPUT_DIR.glob("semantic_krippendorff_by_module_2*.csv"))

    if not standard_files or not semantic_files:
        print("Missing comparison files")
        return None

    standard_file = standard_files[-1]
    semantic_file = semantic_files[-1]

    print(f"Standard alpha: {standard_file.name}")
    print(f"Semantic (full): {semantic_file.name}")

    standard_df = pd.read_csv(standard_file)
    semantic_full_df = pd.read_csv(semantic_file)

    # Merge all results
    comparison = semantic_isa_results.merge(
        standard_df[['module', 'alpha_nominal']],
        on='module',
        how='left'
    ).merge(
        semantic_full_df[['module', 'alpha_semantic']],
        on='module',
        how='left',
        suffixes=('', '_full')
    )

    comparison = comparison.rename(columns={'alpha_semantic': 'alpha_semantic_full'})
    comparison['diff_isa_vs_standard'] = comparison['alpha_semantic_isa'] - comparison['alpha_nominal']
    comparison['diff_isa_vs_full'] = comparison['alpha_semantic_isa'] - comparison['alpha_semantic_full']

    print(f"\n{'Module':<15} {'Standard':>10} {'Sem(Full)':>10} {'Sem(IS-A)':>10} {'Diff(ISA-Std)':>14} {'Diff(ISA-Full)':>14}")
    print("-" * 90)
    for _, row in comparison.iterrows():
        print(f"{row['module']:<15} {row['alpha_nominal']:>10.4f} {row['alpha_semantic_full']:>10.4f} {row['alpha_semantic_isa']:>10.4f} {row['diff_isa_vs_standard']:>+14.4f} {row['diff_isa_vs_full']:>+14.4f}")

    return comparison


# ============================================================================
# EXPORT
# ============================================================================

def export_results(overall_result, module_results, comparison=None):
    """Export results to files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export module results
    module_file = OUTPUT_DIR / f"semantic_krippendorff_isa_by_module_{timestamp}.csv"
    module_results.to_csv(module_file, index=False)
    print(f"\n[OK] Module results (IS-A only): {module_file}")

    # Export overall results
    overall_file = OUTPUT_DIR / f"semantic_krippendorff_isa_overall_{timestamp}.txt"
    with open(overall_file, 'w') as f:
        f.write("=== Semantic Krippendorff's Alpha Results (IS-A Only) ===\n\n")
        f.write(f"Semantic (Taxonomic, IS-A only): {overall_result['value']:.4f}\n")
        f.write(f"Coverage in distance matrix: {overall_result['coverage_in_matrix']*100:.1f}%\n")
        f.write(f"Number of concepts: {overall_result['n_concepts']}\n")
        f.write(f"Number of coders: {overall_result['n_coders']}\n")
    print(f"[OK] Overall results: {overall_file}")

    # Export comparison if available
    if comparison is not None:
        comparison_file = OUTPUT_DIR / f"alpha_comparison_all_methods_{timestamp}.csv"
        comparison.to_csv(comparison_file, index=False)
        print(f"[OK] Comparison (all methods): {comparison_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    # Load data
    df, dist_matrix = load_data()

    # Calculate overall semantic alpha
    overall_result = calculate_overall_semantic_alpha(df, dist_matrix)

    # Calculate per-module semantic alpha
    module_results = calculate_per_module_semantic_alpha(df, dist_matrix)

    # Compare with other results
    comparison = compare_with_other_results(module_results)

    # Export results
    export_results(overall_result, module_results, comparison)

    print("\n" + "=" * 70)
    print("SEMANTIC ANALYSIS COMPLETE (IS-A ONLY)")
    print("=" * 70)


if __name__ == '__main__':
    main()
