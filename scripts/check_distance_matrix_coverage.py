"""
Check Distance Matrix Coverage

Compares unique concepts in the cleaned mapping table with those
in the existing distance matrix to assess coverage.

Usage:
    python scripts/check_distance_matrix_coverage.py
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_TABLE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"
DISTANCE_MATRIX = PROJECT_ROOT / "data/raw/oBDS/Krippendorff Alpha/oBDS_distance_matrix.csv"

MAPPERS = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']

print("=" * 70)
print("Distance Matrix Coverage Check")
print("=" * 70)

# Extract unique concepts from mapping (force string dtype to avoid float conversion)
print(f"\n=== EXTRACTING UNIQUE CONCEPTS FROM MAPPING ===")
dtype_dict = {mapper: str for mapper in MAPPERS}
df = pd.read_csv(MAPPING_TABLE, dtype=dtype_dict)

all_concepts = set()
for mapper in MAPPERS:
    concepts = df[mapper].dropna()
    concepts = concepts[concepts != '']
    concepts = concepts[concepts != 'nan']  # Remove string 'nan'
    all_concepts.update(concepts)

mapping_concepts = sorted(all_concepts)
print(f"Found {len(mapping_concepts)} unique concepts in mapping")

# Load distance matrix
print(f"\n=== LOADING DISTANCE MATRIX ===")
dist_matrix = pd.read_csv(DISTANCE_MATRIX, index_col=0)
dist_matrix.index = dist_matrix.index.astype(str)
dist_matrix.columns = dist_matrix.columns.astype(str)

matrix_concepts = sorted(dist_matrix.index.tolist())
print(f"Found {len(matrix_concepts)} concepts in distance matrix")

# Compare
print(f"\n=== COVERAGE ANALYSIS ===")
mapping_set = set(mapping_concepts)
matrix_set = set(matrix_concepts)

in_both = mapping_set & matrix_set
only_in_mapping = mapping_set - matrix_set
only_in_matrix = matrix_set - mapping_set

print(f"Concepts in both: {len(in_both)} ({len(in_both)/len(mapping_concepts)*100:.1f}% of mapping)")
print(f"Only in mapping (missing from matrix): {len(only_in_mapping)}")
print(f"Only in matrix (not used in mapping): {len(only_in_matrix)}")

if only_in_mapping:
    print(f"\n=== MISSING CONCEPTS ===")
    print("The following concepts are in the mapping but NOT in the distance matrix:")
    for concept in sorted(only_in_mapping)[:20]:  # Show first 20
        print(f"  {concept}")
    if len(only_in_mapping) > 20:
        print(f"  ... and {len(only_in_mapping) - 20} more")

print(f"\n=== RECOMMENDATION ===")
if len(only_in_mapping) == 0:
    print("OK: Perfect coverage! All mapping concepts are in the distance matrix.")
    print("  You can proceed with semantic Krippendorff's Alpha calculation.")
else:
    coverage_pct = len(in_both) / len(mapping_concepts) * 100
    print(f"WARNING: {coverage_pct:.1f}% coverage - {len(only_in_mapping)} concepts missing")
    if coverage_pct >= 95:
        print("  Coverage is acceptable. Semantic alpha will work but ignore missing concepts.")
    else:
        print("  Low coverage! You may need to rebuild the distance matrix.")
        print("  See: notebooks/BuildOBDSMatrix.ipynb")

print("=" * 70)
