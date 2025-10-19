"""
Build SNOMED CT Distance Matrix for oBDS Mapping Concepts

This script extracts all unique SNOMED concepts from the cleaned mapping
table and builds a distance matrix using the SNOMED CT graph.

Based on notebooks/BuildOBDSMatrix.ipynb

Usage:
    python scripts/build_distance_matrix.py

Output:
    - data/processed/obds_distance_matrix.csv
    - data/processed/obds_unique_concepts.txt
"""

import pandas as pd
import sys
import pickle
from pathlib import Path

# Add graphbuilder to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts/graphbuilder"))

from Worker import length_of_shortest_path

def load_graph(filepath):
    """Load a pickled graph from file."""
    with open(filepath, 'rb') as f:
        return pickle.load(f)

# ============================================================================
# CONFIGURATION
# ============================================================================

MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
GRAPH_FILE = PROJECT_ROOT / "data/processed/snomed-20250201_dag_is-a.pkl"
OUTPUT_MATRIX = PROJECT_ROOT / "data/processed/obds_distance_matrix_isa.csv"
OUTPUT_CONCEPTS = PROJECT_ROOT / "data/processed/obds_unique_concepts.txt"

SNOMED_ROOT = '138875005'  # SNOMED CT root concept
MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']

# ============================================================================
# EXTRACT UNIQUE CONCEPTS
# ============================================================================

def extract_unique_concepts():
    """Extract all unique SNOMED concepts from the mapping table."""
    print("=" * 70)
    print("Building SNOMED CT Distance Matrix")
    print("=" * 70)

    print(f"\n=== EXTRACTING UNIQUE CONCEPTS ===")
    print(f"Loading: {MAPPING_TABLE}")

    # Force mapper columns to be read as strings to prevent float conversion
    # of large 18-digit SNOMED IDs (which causes scientific notation)
    dtype_dict = {mapper: str for mapper in MAPPERS}
    df = pd.read_csv(MAPPING_TABLE, dtype=dtype_dict)
    print(f"Loaded {len(df)} rows")

    # Collect all non-empty concept IDs
    all_concepts = set()
    for mapper in MAPPERS:
        concepts = df[mapper].dropna().astype(str)
        concepts = concepts[concepts != '']
        # Remove any .0 endings
        concepts = concepts.apply(lambda x: x[:-2] if x.endswith('.0') else x)
        all_concepts.update(concepts)

    concept_list = sorted(all_concepts)
    print(f"\nFound {len(concept_list)} unique SNOMED concepts")

    # Save concept list
    with open(OUTPUT_CONCEPTS, 'w') as f:
        for concept in concept_list:
            f.write(f"{concept}\n")
    print(f"Saved concept list to: {OUTPUT_CONCEPTS}")

    return concept_list


# ============================================================================
# BUILD DISTANCE MATRIX
# ============================================================================

def build_distance_matrix(concept_list):
    """Build distance matrix using SNOMED CT graph."""
    print(f"\n=== LOADING SNOMED CT GRAPH ===")
    print(f"Graph file: {GRAPH_FILE}")

    if not GRAPH_FILE.exists():
        print(f"ERROR: Graph file not found: {GRAPH_FILE}")
        print("Please run GraphBuilder.py first to generate the SNOMED graph")
        return None

    snomed_graph = load_graph(str(GRAPH_FILE))
    print(f"Loaded graph with {len(snomed_graph.nodes())} nodes")

    print(f"\n=== BUILDING DISTANCE MATRIX ===")
    print(f"Computing {len(concept_list)}² = {len(concept_list)**2} distances")
    print("This may take several minutes...")

    # Create empty matrix
    matrix = pd.DataFrame(index=concept_list, columns=concept_list, dtype=float)

    # Calculate distances
    total_pairs = len(concept_list) ** 2
    completed = 0

    for i, concept1 in enumerate(concept_list):
        if i % 50 == 0:
            print(f"  Progress: {completed}/{total_pairs} ({completed/total_pairs*100:.1f}%)")

        for j, concept2 in enumerate(concept_list):
            try:
                distance = length_of_shortest_path(snomed_graph, SNOMED_ROOT, concept1, concept2)
                matrix.loc[concept1, concept2] = distance
            except Exception as e:
                print(f"  Warning: Could not calculate distance for {concept1} <-> {concept2}: {e}")
                matrix.loc[concept1, concept2] = float('inf')

            completed += 1

    print(f"  Progress: {completed}/{total_pairs} (100.0%)")
    print("Distance calculation complete!")

    return matrix


# ============================================================================
# EXPORT
# ============================================================================

def export_matrix(matrix):
    """Export distance matrix to CSV."""
    print(f"\n=== EXPORTING DISTANCE MATRIX ===")

    OUTPUT_MATRIX.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(OUTPUT_MATRIX)

    print(f"Saved distance matrix to: {OUTPUT_MATRIX}")
    print(f"Matrix shape: {matrix.shape}")
    print(f"Distance range: {matrix.min().min():.0f} to {matrix.max().max():.0f}")

    # Summary statistics
    print(f"\nDistance distribution:")
    flat_distances = matrix.values.flatten()
    finite_distances = flat_distances[~pd.isna(flat_distances) & (flat_distances != float('inf'))]
    print(f"  Mean: {finite_distances.mean():.2f}")
    print(f"  Median: {pd.Series(finite_distances).median():.2f}")
    print(f"  Min: {finite_distances.min():.0f}")
    print(f"  Max: {finite_distances.max():.0f}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    # Extract unique concepts
    concept_list = extract_unique_concepts()

    # Build distance matrix
    matrix = build_distance_matrix(concept_list)

    if matrix is not None:
        # Export results
        export_matrix(matrix)

        print("\n" + "=" * 70)
        print("DISTANCE MATRIX BUILD COMPLETE")
        print("=" * 70)
        print(f"\nYou can now run:")
        print(f"  python scripts/calculate_semantic_krippendorff.py")
    else:
        print("\n" + "=" * 70)
        print("BUILD FAILED - Please check errors above")
        print("=" * 70)


if __name__ == '__main__':
    main()
