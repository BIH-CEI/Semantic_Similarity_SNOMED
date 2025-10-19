"""
Identify Difficult-to-Map oBDS Concepts

Without ground truth, we identify concepts that are:
1. High agreement (easy/clear mapping targets)
2. Low agreement (ambiguous/difficult mapping targets)
3. Complete disagreement (possible terminology gaps)

This analysis helps identify where:
- SNOMED coverage is good (high agreement)
- Terminology gaps exist (no agreement)
- Mapper training is needed (inconsistent agreement)

Usage:
    python scripts/identify_difficult_concepts.py

Output:
    - results/difficult_concepts_YYYYMMDD.csv
    - results/easy_concepts_YYYYMMDD.csv
    - results/concept_agreement_distribution.csv
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

CLEANED_DATA = "data/interim/obds_cleaned_data_20250804_150736.json"

MAPPER_COLUMNS = {
    'Nina': 'SNOMED CT_Code_Nini ',
    'Sophie': 'SNOMED CT_Code_Sophie ',
    'Paul': 'SNOMED CT_Code_Paul ',
    'Lotte': 'SNOMED CT_Code_Lotte'
}

MAPPER_PSEUDONYMS = {
    'Nina': 'M1',
    'Sophie': 'M2',
    'Paul': 'M3',
    'Lotte': 'M4'
}

OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# FUNCTIONS
# ============================================================================

def load_cleaned_data(file_path):
    """Load cleaned oBDS data from JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def create_concept_agreement_matrix(obds_data, mapper_columns):
    """Create per-concept agreement metrics."""

    all_concepts = []

    for module_name, module_data in obds_data.items():
        for row in module_data:
            concept_dict = {
                'module': module_name,
                'obds_id': row.get('Identifier', ''),
                'obds_field': row.get('Feldbezeichnung', ''),
                'obds_values': row.get('Ausprägungen', ''),
            }

            # Extract all mapper assignments
            mapper_values = []
            for mapper_name, col_name in mapper_columns.items():
                value = row.get(col_name)
                if pd.notna(value) and value != '' and value != 'nan':
                    mapper_values.append(str(value))
                    concept_dict[MAPPER_PSEUDONYMS[mapper_name]] = str(value)
                else:
                    concept_dict[MAPPER_PSEUDONYMS[mapper_name]] = None

            # Calculate agreement metrics for this concept
            n_mapped = len(mapper_values)

            if n_mapped == 0:
                # No mapper mapped this concept
                concept_dict['agreement_type'] = 'unmapped'
                concept_dict['n_mappers'] = 0
                concept_dict['n_unique_concepts'] = 0
                concept_dict['agreement_rate'] = 0.0
            elif n_mapped == 1:
                # Only one mapper
                concept_dict['agreement_type'] = 'single_mapper'
                concept_dict['n_mappers'] = 1
                concept_dict['n_unique_concepts'] = 1
                concept_dict['agreement_rate'] = np.nan
            else:
                # Multiple mappers - calculate agreement
                unique_concepts = set(mapper_values)
                n_unique = len(unique_concepts)

                # Find most common concept
                concept_counts = pd.Series(mapper_values).value_counts()
                most_common_concept = concept_counts.index[0]
                most_common_count = concept_counts.iloc[0]

                # Agreement rate = proportion agreeing with most common
                agreement_rate = most_common_count / n_mapped

                concept_dict['most_common_concept'] = most_common_concept
                concept_dict['most_common_count'] = most_common_count
                concept_dict['n_mappers'] = n_mapped
                concept_dict['n_unique_concepts'] = n_unique
                concept_dict['agreement_rate'] = agreement_rate

                # Classify agreement
                if agreement_rate == 1.0:
                    concept_dict['agreement_type'] = 'perfect_agreement'
                elif agreement_rate >= 0.75:
                    concept_dict['agreement_type'] = 'high_agreement'
                elif agreement_rate >= 0.5:
                    concept_dict['agreement_type'] = 'moderate_agreement'
                elif n_unique == n_mapped:
                    concept_dict['agreement_type'] = 'complete_disagreement'
                else:
                    concept_dict['agreement_type'] = 'low_agreement'

            all_concepts.append(concept_dict)

    return pd.DataFrame(all_concepts)


def summarize_agreement_patterns(df):
    """Summarize agreement patterns across all concepts."""

    print("\n=== AGREEMENT PATTERN SUMMARY ===")

    # Count by agreement type
    agreement_counts = df['agreement_type'].value_counts()
    total = len(df)

    print("\nAgreement Distribution:")
    for agreement_type, count in agreement_counts.items():
        pct = (count / total) * 100
        print(f"  {agreement_type}: {count} ({pct:.1f}%)")

    # Concepts with mappers (exclude unmapped)
    mapped_df = df[df['n_mappers'] > 1]

    if len(mapped_df) > 0:
        print(f"\nFor {len(mapped_df)} concepts mapped by 2+ mappers:")
        print(f"  Mean agreement rate: {mapped_df['agreement_rate'].mean():.3f}")
        print(f"  Median agreement rate: {mapped_df['agreement_rate'].median():.3f}")

        # Distribution of unique concepts per oBDS concept
        print(f"\nUnique SNOMED concepts per oBDS concept:")
        unique_dist = mapped_df['n_unique_concepts'].value_counts().sort_index()
        for n_unique, count in unique_dist.items():
            print(f"  {n_unique} concepts: {count} oBDS items")

    return agreement_counts


def identify_problem_areas(df):
    """Identify specific problem areas needing attention."""

    print("\n=== PROBLEM AREAS ===")

    # 1. Complete disagreement (all different)
    complete_disagreement = df[df['agreement_type'] == 'complete_disagreement']
    print(f"\n1. Complete Disagreement ({len(complete_disagreement)} concepts):")
    print("   All mappers chose different SNOMED concepts")
    if len(complete_disagreement) > 0:
        print("   Top examples:")
        for idx, row in complete_disagreement.head(5).iterrows():
            print(f"     - {row['obds_id']}: {row['obds_field']}")
            print(f"       Mappers: M1={row['M1']}, M2={row['M2']}, M3={row['M3']}, M4={row['M4']}")

    # 2. Unmapped concepts
    unmapped = df[df['agreement_type'] == 'unmapped']
    print(f"\n2. Unmapped ({len(unmapped)} concepts):")
    print("   No mapper provided a SNOMED code")
    if len(unmapped) > 0:
        print("   Examples:")
        for idx, row in unmapped.head(5).iterrows():
            print(f"     - {row['obds_id']}: {row['obds_field']} ({row['obds_values']})")

    # 3. Low agreement (< 50%)
    low_agreement = df[df['agreement_type'] == 'low_agreement']
    print(f"\n3. Low Agreement ({len(low_agreement)} concepts):")
    print("   Mappers chose different concepts, < 50% agreement")
    if len(low_agreement) > 0:
        print("   Top examples:")
        for idx, row in low_agreement.head(5).iterrows():
            print(f"     - {row['obds_id']}: {row['obds_field']}")
            print(f"       Agreement: {row['agreement_rate']:.1%}, {row['n_unique_concepts']} unique concepts")

    # 4. Single mapper only
    single_mapper = df[df['agreement_type'] == 'single_mapper']
    print(f"\n4. Single Mapper Only ({len(single_mapper)} concepts):")
    print("   Only one mapper provided a code")

    return {
        'complete_disagreement': complete_disagreement,
        'unmapped': unmapped,
        'low_agreement': low_agreement,
        'single_mapper': single_mapper
    }


def identify_strengths(df):
    """Identify areas of high agreement (strengths)."""

    print("\n=== STRENGTHS (High Agreement Areas) ===")

    # Perfect agreement
    perfect = df[df['agreement_type'] == 'perfect_agreement']
    print(f"\n1. Perfect Agreement ({len(perfect)} concepts, {len(perfect)/len(df)*100:.1f}%):")
    print("   All mappers chose the same SNOMED concept")

    # High agreement
    high = df[df['agreement_type'] == 'high_agreement']
    print(f"\n2. High Agreement ({len(high)} concepts, {len(high)/len(df)*100:.1f}%):")
    print("   ≥75% of mappers agreed")

    # Most commonly agreed-upon concepts
    if len(perfect) > 0:
        print("\n3. Most Frequently Perfectly Agreed Concepts:")
        agreed_concepts = perfect['most_common_concept'].value_counts().head(10)
        for concept_id, count in agreed_concepts.items():
            print(f"     {concept_id}: {count} oBDS items")

    return {
        'perfect': perfect,
        'high': high
    }


def export_results(df, problem_areas, strengths):
    """Export results for further analysis."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export full concept agreement matrix
    full_file = OUTPUT_DIR / f"concept_agreement_all_{timestamp}.csv"
    df.to_csv(full_file, index=False)
    print(f"\n✓ Exported full concept agreement: {full_file}")

    # Export problem areas
    for name, data in problem_areas.items():
        if len(data) > 0:
            file_path = OUTPUT_DIR / f"problem_{name}_{timestamp}.csv"
            data.to_csv(file_path, index=False)
            print(f"✓ Exported {name}: {file_path}")

    # Export strengths
    for name, data in strengths.items():
        if len(data) > 0:
            file_path = OUTPUT_DIR / f"strength_{name}_{timestamp}.csv"
            data.to_csv(file_path, index=False)
            print(f"✓ Exported {name}: {file_path}")

    # Create summary statistics
    summary = {
        'total_concepts': len(df),
        'perfect_agreement': len(strengths['perfect']),
        'high_agreement': len(strengths['high']),
        'moderate_agreement': len(df[df['agreement_type'] == 'moderate_agreement']),
        'low_agreement': len(problem_areas['low_agreement']),
        'complete_disagreement': len(problem_areas['complete_disagreement']),
        'single_mapper': len(problem_areas['single_mapper']),
        'unmapped': len(problem_areas['unmapped']),
    }

    summary_file = OUTPUT_DIR / f"agreement_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Exported summary: {summary_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    print("=" * 70)
    print("Difficult Concept Identification (Without Ground Truth)")
    print("=" * 70)

    # Load data
    print("\n=== LOADING DATA ===")
    obds_data = load_cleaned_data(CLEANED_DATA)

    # Create per-concept agreement metrics
    df = create_concept_agreement_matrix(obds_data, MAPPER_COLUMNS)
    print(f"Analyzed {len(df)} oBDS concepts across {len(obds_data)} modules")

    # Summarize patterns
    agreement_counts = summarize_agreement_patterns(df)

    # Identify problems
    problem_areas = identify_problem_areas(df)

    # Identify strengths
    strengths = identify_strengths(df)

    # Export
    print("\n=== EXPORTING RESULTS ===")
    export_results(df, problem_areas, strengths)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    print("\n=== KEY TAKEAWAYS FOR CONFERENCE ===")
    print(f"1. {len(strengths['perfect'])} concepts ({len(strengths['perfect'])/len(df)*100:.1f}%) have perfect mapper agreement")
    print(f"2. {len(problem_areas['complete_disagreement'])} concepts show complete disagreement → potential terminology gaps")
    print(f"3. {len(problem_areas['unmapped'])} concepts unmapped → out of scope or missing from SNOMED")
    print(f"4. Without ground truth, agreement level indicates mapping clarity, not accuracy")


if __name__ == '__main__':
    main()
