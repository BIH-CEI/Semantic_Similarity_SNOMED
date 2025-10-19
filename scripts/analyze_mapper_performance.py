"""
Mapper Performance and Contribution Analysis

This script analyzes:
1. Completeness rate per mapper (% of concepts mapped)
2. Unique concept contribution (concepts only mapped by one mapper)
3. Agreement patterns (pairwise mapper agreement)
4. Leave-one-out Krippendorff's Alpha (impact of removing each mapper)
5. Mapping consistency (how often mapper agrees with consensus)
6. Multi-value mapping rate (complexity of mappings)

Usage:
    python scripts/analyze_mapper_performance.py

Output:
    - results/mapper_performance_YYYYMMDD.csv
    - results/mapper_pairwise_agreement_YYYYMMDD.csv
    - results/mapper_leave_one_out_YYYYMMDD.csv
    - results/mapper_analysis_figures/ (visualizations)
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import itertools
import krippendorff

# ============================================================================
# CONFIGURATION
# ============================================================================

CLEANED_DATA = "data/interim/obds_cleaned_data_20250804_150736.json"
DISTANCE_MATRIX = "data/raw/oBDS/Krippendorff Alpha/oBDS_distance_matrix.csv"

MAPPER_COLUMNS = {
    'Nina': 'SNOMED CT_Code_Nini ',
    'Sophie': 'SNOMED CT_Code_Sophie ',
    'Paul': 'SNOMED CT_Code_Paul ',
    'Lotte': 'SNOMED CT_Code_Lotte'
}

# Pseudonymization mapping for anonymity
MAPPER_PSEUDONYMS = {
    'Nina': 'M1',
    'Sophie': 'M2',
    'Paul': 'M3',
    'Lotte': 'M4'
}

OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_alpha_simple(reliability_data):
    """
    Calculate Krippendorff's Alpha using library for simple nominal data.

    Args:
        reliability_data: DataFrame where rows=items, columns=coders

    Returns:
        float: Krippendorff's Alpha value
    """
    # Convert string concepts to numeric codes
    all_values = []
    for col in reliability_data.columns:
        all_values.extend(reliability_data[col].dropna().unique())

    unique_concepts = sorted(set(all_values))
    concept_to_code = {concept: idx for idx, concept in enumerate(unique_concepts)}

    # Create numeric reliability matrix
    numeric_data = reliability_data.copy()
    for col in numeric_data.columns:
        numeric_data[col] = numeric_data[col].map(lambda x: concept_to_code.get(x, np.nan) if pd.notna(x) else np.nan)

    # Transpose to coders × items format for library
    data_array = numeric_data.T.values

    # Calculate alpha
    try:
        alpha = krippendorff.alpha(
            reliability_data=data_array,
            level_of_measurement='nominal'
        )
        return alpha
    except Exception as e:
        print(f"Warning: Could not calculate alpha: {e}")
        return np.nan


def load_cleaned_data(file_path):
    """Load cleaned oBDS data from JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def create_reliability_matrix(obds_data, mapper_columns, pseudonymize=True):
    """Create reliability matrix for Krippendorff's Alpha."""
    all_concepts = []

    for module_name, module_data in obds_data.items():
        for row in module_data:
            concept_dict = {
                'module': module_name,
                'obds_id': row.get('Identifier', ''),
                'obds_field': row.get('Feldbezeichnung', ''),
            }

            for mapper_name, col_name in mapper_columns.items():
                value = row.get(col_name)
                # Use pseudonym if requested
                output_name = MAPPER_PSEUDONYMS.get(mapper_name, mapper_name) if pseudonymize else mapper_name

                if pd.notna(value) and value != '' and value != 'nan':
                    concept_dict[output_name] = str(value)
                else:
                    concept_dict[output_name] = np.nan

            all_concepts.append(concept_dict)

    df = pd.DataFrame(all_concepts)

    # Create column list with pseudonyms
    if pseudonymize:
        reliability_matrix = df[[MAPPER_PSEUDONYMS[m] for m in mapper_columns.keys()]]
    else:
        reliability_matrix = df[list(mapper_columns.keys())]

    return df, reliability_matrix


# ============================================================================
# MAPPER PERFORMANCE METRICS
# ============================================================================

def calculate_completeness_rate(reliability_matrix):
    """Calculate completeness rate for each mapper."""
    print("\n=== COMPLETENESS ANALYSIS ===")

    total_concepts = len(reliability_matrix)
    completeness = {}

    for mapper in reliability_matrix.columns:
        mapped = reliability_matrix[mapper].notna().sum()
        rate = (mapped / total_concepts) * 100
        completeness[mapper] = {
            'concepts_mapped': mapped,
            'total_concepts': total_concepts,
            'completeness_rate_%': rate
        }
        print(f"{mapper}: {mapped}/{total_concepts} ({rate:.1f}%)")

    return pd.DataFrame(completeness).T


def calculate_unique_contributions(reliability_matrix):
    """Calculate how many concepts were uniquely mapped by each mapper."""
    print("\n=== UNIQUE CONTRIBUTION ANALYSIS ===")

    unique_contributions = {}

    for mapper in reliability_matrix.columns:
        # Count concepts where only this mapper provided a mapping
        unique_count = 0

        for idx, row in reliability_matrix.iterrows():
            mappers_who_mapped = row.notna().sum()
            if mappers_who_mapped == 1 and pd.notna(row[mapper]):
                unique_count += 1

        unique_contributions[mapper] = unique_count
        print(f"{mapper}: {unique_count} unique mappings")

    return pd.Series(unique_contributions)


def calculate_concept_diversity(reliability_matrix):
    """Calculate how many unique SNOMED concepts each mapper used."""
    print("\n=== CONCEPT DIVERSITY ANALYSIS ===")

    diversity = {}

    for mapper in reliability_matrix.columns:
        unique_concepts = reliability_matrix[mapper].dropna().nunique()
        total_mappings = reliability_matrix[mapper].notna().sum()

        # Find most frequently used concept
        if total_mappings > 0:
            concept_counts = reliability_matrix[mapper].value_counts()
            most_frequent_concept = concept_counts.index[0]
            most_frequent_count = concept_counts.iloc[0]
            most_frequent_pct = (most_frequent_count / total_mappings) * 100
        else:
            most_frequent_concept = None
            most_frequent_count = 0
            most_frequent_pct = 0

        diversity[mapper] = {
            'unique_concepts': unique_concepts,
            'total_mappings': total_mappings,
            'diversity_ratio': unique_concepts / total_mappings if total_mappings > 0 else 0,
            'most_frequent_concept': most_frequent_concept,
            'most_frequent_count': most_frequent_count,
            'most_frequent_%': most_frequent_pct
        }

        print(f"{mapper}: {unique_concepts} unique concepts in {total_mappings} mappings (ratio: {diversity[mapper]['diversity_ratio']:.3f})")
        if most_frequent_concept:
            print(f"  Most frequent: {most_frequent_concept} ({most_frequent_count}×, {most_frequent_pct:.1f}%)")

    return pd.DataFrame(diversity).T


def calculate_pairwise_agreement(reliability_matrix):
    """Calculate pairwise agreement between all mapper pairs."""
    print("\n=== PAIRWISE AGREEMENT ANALYSIS ===")

    mappers = list(reliability_matrix.columns)
    pairwise_results = []

    for mapper1, mapper2 in itertools.combinations(mappers, 2):
        # Create matrix with only these two mappers
        pair_matrix = reliability_matrix[[mapper1, mapper2]]

        # Calculate agreement
        alpha = calculate_alpha_simple(pair_matrix)

        # Calculate simple percent agreement (for comparison)
        both_mapped = pair_matrix.dropna()
        if len(both_mapped) > 0:
            exact_matches = (both_mapped[mapper1] == both_mapped[mapper2]).sum()
            percent_agreement = (exact_matches / len(both_mapped)) * 100
        else:
            percent_agreement = np.nan

        pairwise_results.append({
            'mapper_1': mapper1,
            'mapper_2': mapper2,
            'krippendorff_alpha': alpha,
            'percent_agreement': percent_agreement,
            'n_both_mapped': len(both_mapped)
        })

        print(f"{mapper1} <-> {mapper2}: α={alpha:.4f}, exact={percent_agreement:.1f}% (n={len(both_mapped)})")

    return pd.DataFrame(pairwise_results)


def calculate_leave_one_out_alpha(reliability_matrix, distance_matrix=None):
    """Calculate Krippendorff's Alpha with each mapper removed (leave-one-out)."""
    print("\n=== LEAVE-ONE-OUT ANALYSIS ===")

    mappers = list(reliability_matrix.columns)

    # Baseline: all mappers
    baseline_alpha = calculate_alpha_simple(reliability_matrix)
    print(f"Baseline (all mappers): α={baseline_alpha:.4f}")

    loo_results = []

    for mapper in mappers:
        # Remove this mapper
        remaining_mappers = [m for m in mappers if m != mapper]
        loo_matrix = reliability_matrix[remaining_mappers]

        # Calculate alpha without this mapper
        alpha_without = calculate_alpha_simple(loo_matrix)
        delta_alpha = alpha_without - baseline_alpha

        result = {
            'mapper_removed': mapper,
            'alpha_without': alpha_without,
            'alpha_baseline': baseline_alpha,
            'delta_alpha': delta_alpha,
            'impact': 'Improves' if delta_alpha > 0 else 'Decreases'
        }

        loo_results.append(result)

        print(f"Without {mapper}: α={alpha_without:.4f} (Δ={delta_alpha:+.4f}) - {result['impact']}")

    return pd.DataFrame(loo_results)


def calculate_consensus_agreement(df, reliability_matrix):
    """
    Calculate how often each mapper agrees with the majority/consensus.

    For each concept, find the most common mapping (mode).
    Then calculate how often each mapper selected that consensus mapping.
    """
    print("\n=== CONSENSUS AGREEMENT ANALYSIS ===")

    consensus_scores = {}

    for mapper in reliability_matrix.columns:
        agrees_with_consensus = 0
        total_mapped = 0

        for idx, row in reliability_matrix.iterrows():
            mapper_value = row[mapper]

            if pd.isna(mapper_value):
                continue

            total_mapped += 1

            # Find consensus (mode) among all mappers for this concept
            values = row.dropna().values
            if len(values) == 0:
                continue

            # Get most common value
            unique, counts = np.unique(values, return_counts=True)
            consensus_value = unique[counts.argmax()]

            # Check if mapper agrees with consensus
            if mapper_value == consensus_value:
                agrees_with_consensus += 1

        consensus_rate = (agrees_with_consensus / total_mapped * 100) if total_mapped > 0 else 0

        consensus_scores[mapper] = {
            'agrees_with_consensus': agrees_with_consensus,
            'total_mapped': total_mapped,
            'consensus_agreement_%': consensus_rate
        }

        print(f"{mapper}: {agrees_with_consensus}/{total_mapped} ({consensus_rate:.1f}%) agree with consensus")

    return pd.DataFrame(consensus_scores).T


# ============================================================================
# MODULE-SPECIFIC MAPPER PERFORMANCE
# ============================================================================

def analyze_mapper_by_module(df, reliability_matrix):
    """Analyze mapper performance broken down by module."""
    print("\n=== MAPPER PERFORMANCE BY MODULE ===")

    module_performance = []

    for module in df['module'].unique():
        module_mask = df['module'] == module
        module_matrix = reliability_matrix[module_mask]

        n_concepts = len(module_matrix)

        for mapper in module_matrix.columns:
            mapped = module_matrix[mapper].notna().sum()
            rate = (mapped / n_concepts) * 100

            module_performance.append({
                'module': module,
                'mapper': mapper,
                'concepts_mapped': mapped,
                'total_concepts': n_concepts,
                'completeness_%': rate
            })

    df_module_perf = pd.DataFrame(module_performance)

    # Show summary
    print("\nCompleteness rate by module (average across mappers):")
    module_summary = df_module_perf.groupby('module')['completeness_%'].mean().sort_values(ascending=False)
    for module, avg_rate in module_summary.items():
        print(f"  {module}: {avg_rate:.1f}%")

    return df_module_perf


# ============================================================================
# EXPORT AND VISUALIZATION
# ============================================================================

def export_all_results(results_dict):
    """Export all analysis results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    files_created = []

    # Export each result type
    for name, data in results_dict.items():
        if data is not None and not data.empty:
            filename = OUTPUT_DIR / f"mapper_{name}_{timestamp}.csv"
            data.to_csv(filename)
            files_created.append(filename)
            print(f"✓ Exported: {filename}")

    return files_created


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    print("=" * 70)
    print("Mapper Performance and Contribution Analysis")
    print("=" * 70)

    # Load data
    print("\n=== LOADING DATA ===")
    obds_data = load_cleaned_data(CLEANED_DATA)
    df, reliability_matrix = create_reliability_matrix(obds_data, MAPPER_COLUMNS, pseudonymize=True)
    print(f"Loaded {len(reliability_matrix)} concepts from {len(obds_data)} modules")
    print(f"Using pseudonymized mapper names: {list(reliability_matrix.columns)}")

    # Load distance matrix (optional)
    try:
        distance_matrix = pd.read_csv(DISTANCE_MATRIX, index_col=0)
        print(f"Loaded distance matrix: {distance_matrix.shape}")
    except Exception as e:
        print(f"WARNING: Could not load distance matrix: {e}")
        distance_matrix = None

    # Run all analyses
    results = {}

    results['completeness'] = calculate_completeness_rate(reliability_matrix)
    results['unique_contributions'] = calculate_unique_contributions(reliability_matrix)
    results['concept_diversity'] = calculate_concept_diversity(reliability_matrix)
    results['pairwise_agreement'] = calculate_pairwise_agreement(reliability_matrix)
    results['leave_one_out'] = calculate_leave_one_out_alpha(reliability_matrix, distance_matrix)
    results['consensus_agreement'] = calculate_consensus_agreement(df, reliability_matrix)
    results['performance_by_module'] = analyze_mapper_by_module(df, reliability_matrix)

    # Export
    print("\n=== EXPORTING RESULTS ===")
    files = export_all_results(results)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print(f"Created {len(files)} output files in {OUTPUT_DIR}/")
    print("=" * 70)

    # Summary for talk
    print("\n" + "=" * 70)
    print("SUMMARY FOR CONFERENCE TALK")
    print("=" * 70)

    print("\n1. COMPLETENESS:")
    print(results['completeness'][['completeness_rate_%']].to_string())

    print("\n2. UNIQUE CONTRIBUTIONS:")
    print(results['unique_contributions'].to_string())

    print("\n3. PAIRWISE AGREEMENT (Krippendorff's Alpha):")
    for _, row in results['pairwise_agreement'].iterrows():
        print(f"   {row['mapper_1']} <-> {row['mapper_2']}: α={row['krippendorff_alpha']:.3f}")

    print("\n4. LEAVE-ONE-OUT IMPACT:")
    print(results['leave_one_out'][['mapper_removed', 'delta_alpha', 'impact']].to_string(index=False))

    print("\n5. CONSENSUS AGREEMENT:")
    print(results['consensus_agreement'][['consensus_agreement_%']].to_string())


if __name__ == '__main__':
    main()
