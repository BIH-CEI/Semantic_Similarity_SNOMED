"""
Recalculate Krippendorff's Alpha with Full Transparency

This script recalculates ALL Krippendorff's Alpha values from scratch and
outputs intermediate calculation tables for verification.

Outputs:
1. Standard (nominal) Krippendorff's Alpha
2. Semantic Krippendorff's Alpha (IS-A only)
3. Semantic Krippendorff's Alpha (full relations)
4. Pairwise mapper comparison matrices (M1_M2, M1_M3, etc.)
5. Coincidence matrices
6. Distance matrices used

Usage:
    python scripts/recalculate_krippendorff_with_details.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter
import pickle

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
GRAPH_ISA = PROJECT_ROOT / "data/processed/snomed-20250201_dag_is-a.pkl"
GRAPH_FULL = PROJECT_ROOT / "data/processed/snomed-20250201_dag_rel.pkl"
OUTPUT_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']
SNOMED_ROOT = '138875005'  # SNOMED CT root concept

# Import Worker module for LCA-based distance calculation
import sys
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "graphbuilder"))
import Worker

# ============================================================================
# GRAPH-BASED DISTANCE CALCULATION
# ============================================================================

def shortest_path_distance(graph, concept1, concept2):
    """
    Calculate shortest path distance between two concepts in SNOMED graph.

    Uses LCA-based method to handle directed graphs correctly.
    Ensures symmetry by taking minimum of both directions.

    Returns:
        int: Number of hops between concepts, or None if no path exists
    """
    if concept1 == concept2:
        return 0

    try:
        # Use Worker.py's LCA-based method (handles directed graphs)
        dist_ab = Worker.length_of_shortest_path(graph, SNOMED_ROOT, concept1, concept2)
        dist_ba = Worker.length_of_shortest_path(graph, SNOMED_ROOT, concept2, concept1)

        # Ensure symmetry: use minimum distance
        distance = min(dist_ab, dist_ba)

        return distance
    except Exception as e:
        # If LCA method fails, return None
        return None


def calculate_pairwise_distances_from_graph(concepts, graph, graph_name=""):
    """
    Calculate all pairwise distances between concepts using graph.

    Returns:
        DataFrame: Distance matrix
    """
    print(f"\nCalculating pairwise distances using {graph_name} graph...")

    n = len(concepts)
    distance_matrix = pd.DataFrame(
        np.zeros((n, n)),
        index=concepts,
        columns=concepts
    )

    # Calculate distances
    total_pairs = (n * (n - 1)) // 2
    calculated = 0
    missing = 0

    for i, c1 in enumerate(concepts):
        for j, c2 in enumerate(concepts):
            if i <= j:
                if i == j:
                    distance_matrix.loc[c1, c2] = 0
                else:
                    dist = shortest_path_distance(graph, c1, c2)
                    if dist is not None:
                        distance_matrix.loc[c1, c2] = dist
                        distance_matrix.loc[c2, c1] = dist
                        calculated += 1
                    else:
                        # No path found - use maximum distance
                        distance_matrix.loc[c1, c2] = 50
                        distance_matrix.loc[c2, c1] = 50
                        missing += 1
                        print(f"  WARNING: No path between {c1} and {c2}")

    print(f"  Calculated {calculated} distances")
    print(f"  Missing paths: {missing} (set to max distance 50)")

    return distance_matrix


# ============================================================================
# KRIPPENDORFF'S ALPHA - TRANSPARENT IMPLEMENTATION
# ============================================================================

def calculate_krippendorff_alpha_detailed(data, distance_matrix=None, metric_name="nominal"):
    """
    Calculate Krippendorff's Alpha with detailed intermediate outputs.

    Args:
        data: DataFrame with items (rows) and raters (columns)
        distance_matrix: Optional DataFrame with pairwise distances between categories
        metric_name: Name for this calculation (for logging)

    Returns:
        dict with alpha, coincidence matrix, and other details
    """
    print(f"\n{'=' * 70}")
    print(f"Calculating Krippendorff's Alpha: {metric_name}")
    print(f"{'=' * 70}")

    # Convert to numpy
    values = data.values
    n_items, n_raters = values.shape

    print(f"Total items: {n_items}")
    print(f"Total raters: {n_raters}")

    # Build pairable units (items with at least 2 ratings)
    units = []
    for i in range(n_items):
        row_values = [v for v in values[i] if pd.notna(v)]
        if len(row_values) >= 2:
            units.append(row_values)

    print(f"Items with >=2 ratings: {len(units)}")

    if len(units) == 0:
        print("ERROR: No items with multiple ratings!")
        return None

    # Get all unique categories
    all_values = []
    for unit in units:
        all_values.extend(unit)

    categories = sorted(set(all_values))
    n_categories = len(categories)

    print(f"Unique categories: {n_categories}")

    if n_categories <= 1:
        print("ERROR: Need at least 2 different categories!")
        return None

    # Build coincidence matrix
    print("\nBuilding coincidence matrix...")
    coincidence = np.zeros((n_categories, n_categories))

    for unit in units:
        m_u = len(unit)  # Number of ratings for this unit
        if m_u > 1:
            for c in unit:
                for k in unit:
                    c_idx = categories.index(c)
                    k_idx = categories.index(k)
                    coincidence[c_idx, k_idx] += 1.0 / (m_u - 1)

    # Create coincidence DataFrame for output
    coincidence_df = pd.DataFrame(
        coincidence,
        index=categories,
        columns=categories
    )

    print(f"Coincidence matrix sum: {coincidence.sum():.2f}")

    # Build distance matrix
    if distance_matrix is None:
        # Nominal distance: 0 if same, 1 if different
        print("Using nominal distance (0 if same, 1 if different)")
        delta = 1 - np.eye(n_categories)
    else:
        # Custom distance from provided matrix
        print("Using semantic distance from SNOMED graph")
        delta = np.zeros((n_categories, n_categories))
        for i, c1 in enumerate(categories):
            for j, c2 in enumerate(categories):
                if str(c1) in distance_matrix.index and str(c2) in distance_matrix.columns:
                    delta[i, j] = distance_matrix.loc[str(c1), str(c2)]
                else:
                    # Concept not in graph - use nominal
                    delta[i, j] = 0 if i == j else 1

    # Calculate observed disagreement
    D_o = 0
    for c in range(n_categories):
        for k in range(n_categories):
            D_o += coincidence[c, k] * delta[c, k]

    # Calculate expected disagreement
    n_total = coincidence.sum()
    n_c = coincidence.sum(axis=1)  # Marginal frequencies

    D_e = 0
    for c in range(n_categories):
        for k in range(n_categories):
            if c != k:
                D_e += n_c[c] * n_c[k] * delta[c, k]

    D_e = D_e / (n_total - 1) if n_total > 1 else 0

    # Calculate alpha
    if D_e == 0:
        alpha = np.nan
        print("\nWARNING: Expected disagreement is 0!")
    else:
        alpha = 1 - (D_o / D_e)

    print(f"\nResults:")
    print(f"  Observed disagreement (D_o): {D_o:.4f}")
    print(f"  Expected disagreement (D_e): {D_e:.4f}")
    print(f"  Krippendorff's Alpha: {alpha:.4f}")

    return {
        'alpha': alpha,
        'D_o': D_o,
        'D_e': D_e,
        'n_units': len(units),
        'n_categories': n_categories,
        'coincidence_matrix': coincidence_df,
        'categories': categories
    }


# ============================================================================
# PAIRWISE MAPPER COMPARISONS
# ============================================================================

def calculate_pairwise_mapper_agreement(data):
    """
    Calculate pairwise agreement between each pair of mappers.

    Returns:
        DataFrame with all pairwise comparisons
    """
    print(f"\n{'=' * 70}")
    print("Pairwise Mapper Agreement Analysis")
    print(f"{'=' * 70}")

    from itertools import combinations

    results = []

    for m1, m2 in combinations(MAPPERS, 2):
        print(f"\nComparing {m1} vs {m2}...")

        # Count items where both responded
        both_responded = 0
        agreements = 0
        disagreements = 0

        for idx, row in data.iterrows():
            v1 = row[m1]
            v2 = row[m2]

            if pd.notna(v1) and pd.notna(v2):
                both_responded += 1
                if v1 == v2:
                    agreements += 1
                else:
                    disagreements += 1

        pct_agreement = agreements / both_responded * 100 if both_responded > 0 else 0

        print(f"  Items both responded: {both_responded}")
        print(f"  Agreements: {agreements} ({pct_agreement:.1f}%)")
        print(f"  Disagreements: {disagreements}")

        results.append({
            'mapper1': m1,
            'mapper2': m2,
            'both_responded': both_responded,
            'agreements': agreements,
            'disagreements': disagreements,
            'percent_agreement': pct_agreement
        })

    return pd.DataFrame(results)


# ============================================================================
# MAIN CALCULATION
# ============================================================================

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("KRIPPENDORFF'S ALPHA RECALCULATION WITH FULL DETAILS")
    print("=" * 70)
    print(f"Timestamp: {timestamp}\n")

    # Load mapping data
    print("Loading data...")
    df = pd.read_csv(MAPPING_TABLE)
    print(f"  Loaded {len(df)} items")
    print(f"  Mappers: {MAPPERS}")

    # Get all unique concepts across all mappers
    all_concepts = set()
    for mapper in MAPPERS:
        concepts = df[mapper].dropna().astype(str)
        # Convert floats to ints
        concepts = [str(int(float(c))) if '.' in str(c) else str(c) for c in concepts]
        all_concepts.update(concepts)

    all_concepts = sorted(list(all_concepts))
    print(f"\nUnique SNOMED concepts used: {len(all_concepts)}")

    # Clean data - convert to strings
    for mapper in MAPPERS:
        df[mapper] = df[mapper].apply(
            lambda x: str(int(float(x))) if pd.notna(x) and str(x) != 'nan' else np.nan
        )

    # ========================================================================
    # 1. PAIRWISE MAPPER COMPARISONS
    # ========================================================================

    pairwise_df = calculate_pairwise_mapper_agreement(df)
    pairwise_file = OUTPUT_DIR / f"pairwise_mapper_agreement_{timestamp}.csv"
    pairwise_df.to_csv(pairwise_file, index=False)
    print(f"\nSaved pairwise comparisons: {pairwise_file}")

    # ========================================================================
    # 2. STANDARD (NOMINAL) KRIPPENDORFF'S ALPHA
    # ========================================================================

    result_nominal = calculate_krippendorff_alpha_detailed(
        df[MAPPERS],
        distance_matrix=None,
        metric_name="Standard (Nominal)"
    )

    # Save coincidence matrix
    if result_nominal:
        coincidence_file = OUTPUT_DIR / f"coincidence_matrix_nominal_{timestamp}.csv"
        result_nominal['coincidence_matrix'].to_csv(coincidence_file)
        print(f"Saved coincidence matrix: {coincidence_file}")

    # ========================================================================
    # 3. SEMANTIC KRIPPENDORFF'S ALPHA (IS-A ONLY)
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Loading SNOMED CT IS-A graph...")
    print(f"{'=' * 70}")

    if GRAPH_ISA.exists():
        with open(GRAPH_ISA, 'rb') as f:
            graph_isa = pickle.load(f)

        print(f"  Nodes: {graph_isa.number_of_nodes()}")
        print(f"  Edges: {graph_isa.number_of_edges()}")

        # Calculate distance matrix from graph
        distance_matrix_isa = calculate_pairwise_distances_from_graph(
            all_concepts,
            graph_isa,
            "IS-A"
        )

        # Save distance matrix
        dist_isa_file = OUTPUT_DIR / f"distance_matrix_isa_detailed_{timestamp}.csv"
        distance_matrix_isa.to_csv(dist_isa_file)
        print(f"Saved IS-A distance matrix: {dist_isa_file}")

        # Calculate semantic alpha
        result_isa = calculate_krippendorff_alpha_detailed(
            df[MAPPERS],
            distance_matrix=distance_matrix_isa,
            metric_name="Semantic (IS-A only)"
        )

        if result_isa:
            coincidence_file = OUTPUT_DIR / f"coincidence_matrix_isa_{timestamp}.csv"
            result_isa['coincidence_matrix'].to_csv(coincidence_file)
            print(f"Saved coincidence matrix: {coincidence_file}")
    else:
        print(f"ERROR: IS-A graph not found at {GRAPH_ISA}")
        result_isa = None

    # ========================================================================
    # 4. SEMANTIC KRIPPENDORFF'S ALPHA (FULL RELATIONS)
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Loading SNOMED CT Full Relations graph...")
    print(f"{'=' * 70}")

    if GRAPH_FULL.exists():
        with open(GRAPH_FULL, 'rb') as f:
            graph_full = pickle.load(f)

        print(f"  Nodes: {graph_full.number_of_nodes()}")
        print(f"  Edges: {graph_full.number_of_edges()}")

        # Calculate distance matrix from graph
        distance_matrix_full = calculate_pairwise_distances_from_graph(
            all_concepts,
            graph_full,
            "Full Relations"
        )

        # Save distance matrix
        dist_full_file = OUTPUT_DIR / f"distance_matrix_full_detailed_{timestamp}.csv"
        distance_matrix_full.to_csv(dist_full_file)
        print(f"Saved full relations distance matrix: {dist_full_file}")

        # Calculate semantic alpha
        result_full = calculate_krippendorff_alpha_detailed(
            df[MAPPERS],
            distance_matrix=distance_matrix_full,
            metric_name="Semantic (Full Relations)"
        )

        if result_full:
            coincidence_file = OUTPUT_DIR / f"coincidence_matrix_full_{timestamp}.csv"
            result_full['coincidence_matrix'].to_csv(coincidence_file)
            print(f"Saved coincidence matrix: {coincidence_file}")
    else:
        print(f"ERROR: Full graph not found at {GRAPH_FULL}")
        result_full = None

    # ========================================================================
    # 5. SUMMARY RESULTS
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("SUMMARY OF RESULTS")
    print(f"{'=' * 70}")

    summary = []

    if result_nominal:
        summary.append({
            'method': 'Standard (Nominal)',
            'alpha': result_nominal['alpha'],
            'D_o': result_nominal['D_o'],
            'D_e': result_nominal['D_e'],
            'n_units': result_nominal['n_units'],
            'n_categories': result_nominal['n_categories']
        })
        print(f"\nStandard Alpha: {result_nominal['alpha']:.4f}")

    if result_isa:
        summary.append({
            'method': 'Semantic (IS-A only)',
            'alpha': result_isa['alpha'],
            'D_o': result_isa['D_o'],
            'D_e': result_isa['D_e'],
            'n_units': result_isa['n_units'],
            'n_categories': result_isa['n_categories']
        })
        print(f"Semantic IS-A Alpha: {result_isa['alpha']:.4f}")
        if result_nominal:
            improvement = result_isa['alpha'] - result_nominal['alpha']
            print(f"  Improvement: +{improvement:.4f} ({improvement/result_nominal['alpha']*100:.1f}%)")

    if result_full:
        summary.append({
            'method': 'Semantic (Full Relations)',
            'alpha': result_full['alpha'],
            'D_o': result_full['D_o'],
            'D_e': result_full['D_e'],
            'n_units': result_full['n_units'],
            'n_categories': result_full['n_categories']
        })
        print(f"Semantic Full Alpha: {result_full['alpha']:.4f}")
        if result_nominal:
            improvement = result_full['alpha'] - result_nominal['alpha']
            print(f"  Improvement: +{improvement:.4f} ({improvement/result_nominal['alpha']*100:.1f}%)")

    summary_df = pd.DataFrame(summary)
    summary_file = OUTPUT_DIR / f"krippendorff_summary_{timestamp}.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"\nSaved summary: {summary_file}")

    print(f"\n{'=' * 70}")
    print("RECALCULATION COMPLETE")
    print(f"{'=' * 70}")
    print(f"\nAll results saved with timestamp: {timestamp}")
    print("\nFiles created:")
    print(f"  - {pairwise_file.name}")
    print(f"  - {summary_file.name}")
    print(f"  - Coincidence matrices (3 files)")
    print(f"  - Distance matrices (2 files)")


if __name__ == '__main__':
    main()
