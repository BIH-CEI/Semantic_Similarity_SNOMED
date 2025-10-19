"""
Explain the Different Baselines for Agreement Metrics

Demonstrates why semantic alpha addresses the issue of inappropriate
comparison baselines in hierarchical taxonomies.

The Problem with Standard Alpha for SNOMED CT:
- Treats all used codes as equally valid alternatives
- Doesn't account for semantic appropriateness
- Comparing diagnosis codes to body structure codes makes no sense

The Solution: Semantic Alpha
- Uses graph distance to weight disagreements
- Codes from different branches = maximum distance
- Codes from same branch = partial credit
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Load graph
graph_file = PROJECT_ROOT / "data/processed/snomed-20250201_dag_is-a.pkl"
with open(graph_file, 'rb') as f:
    graph = pickle.load(f)

total_snomed = graph.number_of_nodes()

print("=" * 70)
print("THREE DIFFERENT BASELINES FOR AGREEMENT")
print("=" * 70)
print()

print("BASELINE 1: Traditional Krippendorff (what we calculated)")
print("-" * 70)
print("Question: How much better than random assignment of the 576")
print("          codes mappers actually used?")
print()
print(f"Used codes: 576")
print(f"Random match prob: ~1/576 = 0.0017 (0.17%)")
print(f"Result: Alpha = 0.7634")
print()
print("PROBLEM: Assumes all 576 codes are valid for all items!")
print("  → Diagnosis codes vs Body structure codes")
print("  → This makes NO semantic sense")
print()

print("BASELINE 2: Full SNOMED CT (what you're suggesting)")
print("-" * 70)
print("Question: How much better than random selection from ALL")
print("          371,737 SNOMED concepts?")
print()
print(f"Total SNOMED codes: {total_snomed:,}")
print(f"Random match prob: 1/{total_snomed:,} ≈ 0.0000027 (0.00027%)")
print()
print("With this baseline, observed agreement of 76.5% is:")
print(f"  (0.765 - 0.0000027) / (1 - 0.0000027) ≈ 0.765")
print("  → Alpha would be ~0.765 (slightly higher)")
print()
print("PROBLEM: This still doesn't account for WHICH codes are")
print("appropriate for WHICH items!")
print()

print("BASELINE 3: Semantic Alpha (the CORRECT approach)")
print("-" * 70)
print("Question: When mappers disagree, how semantically distant")
print("          are their choices?")
print()
print("Key insight:")
print("  - If disagreement is SEMANTICALLY CLOSE → partial credit")
print("  - If disagreement is SEMANTICALLY FAR → full penalty")
print()
print("Examples:")
print("  Disagree on 'Primary neoplasm' vs 'Malignant neoplasm'")
print("    → Distance: 2-3 hops (semantically close)")
print("    → Partial penalty")
print()
print("  Disagree on 'Lung structure' vs 'Malignant neoplasm'")
print("    → Distance: 20+ hops (completely different branches)")
print("    → Full penalty (like nominal)")
print()
print("This AUTOMATICALLY accounts for:")
print("  ✓ Different semantic domains")
print("  ✓ Appropriate vs inappropriate code choices")
print("  ✓ The full SNOMED hierarchy")
print()

print("=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print()
print("For SNOMED CT mapping quality, you should report:")
print()
print("1. NOMINAL alpha (0.7634)")
print("   → Shows raw agreement rate")
print()
print("2. SEMANTIC alpha (to be calculated)")
print("   → Shows agreement accounting for semantic similarity")
print("   → This is the PRIMARY metric for SNOMED CT!")
print()
print("3. The DIFFERENCE between them")
print("   → Shows how much partial credit matters")
print("   → Demonstrates value of using semantic distance")
print()
print("The semantic alpha addresses your concern because:")
print("  - Inappropriate codes (different domains) = large distance")
print("  - Similar codes (same domain) = small distance")
print("  - It implicitly uses the FULL SNOMED structure")
