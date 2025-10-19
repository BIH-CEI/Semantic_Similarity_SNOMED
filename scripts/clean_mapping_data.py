"""
Clean raw oBDS mapping data.

Reads raw mapping table from data/interim/ and applies data cleaning
based on logic from notebooks/oBDS_Data_Import.ipynb cell 18.

Cleaning operations:
1. Remove .0 endings from pandas float conversion
2. Handle scientific notation (manual mapping)
3. Remove SNOMED annotations like "(SCT)"
4. Extract concept IDs from pipe expressions
5. Handle multi-value entries (take first)
6. Remove non-breaking spaces
7. Fix known typos
8. Replace dashes with empty values

Usage:
    python scripts/clean_mapping_data.py

Input:
    data/interim/obds_mapping_table_raw.csv

Output:
    data/processed/obds_mapping_table.csv
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "data/interim/obds_mapping_table_raw.csv"
OUTPUT_FILE = PROJECT_ROOT / "data/processed/obds_mapping_table.csv"

# Mapper names - original (in raw data) and pseudonymized (for output)
MAPPERS_RAW = ['Nina', 'Sophie', 'Paul', 'Lotte']
MAPPER_PSEUDONYM_MAP = {
    'Nina': 'Mapper_A',
    'Sophie': 'Mapper_B',
    'Paul': 'Mapper_C',
    'Lotte': 'Mapper_D'
}
MAPPERS = MAPPERS_RAW  # Used for processing

# ============================================================================
# CLEANING FUNCTIONS (from notebooks/oBDS_Data_Import.ipynb cell 18)
# ============================================================================

def clean_snomed_value(value, stats):
    """
    Clean a SNOMED CT concept ID from various Excel formatting issues.

    Based on cleaning logic from notebooks/oBDS_Data_Import.ipynb cell 18.

    Args:
        value: Raw value from Excel
        stats: Dictionary to track cleaning operations

    Returns:
        Cleaned SNOMED ID string, or None if invalid/empty
    """
    # Handle NaN, None, empty
    if pd.isna(value) or value == '' or str(value) == 'nan':
        return None

    original = str(value).strip()
    cleaned = original

    # Handle dash placeholder
    if cleaned == '-':
        stats['dash_removed'] += 1
        return None

    # Scientific notation mapping (corrected after validation)
    # Excel displays 18-digit SNOMED IDs in scientific notation, losing precision
    scientific_notation_map = {
        '9.00000000000465e+17': '900000000000465000',  # String (foundation metadata concept)
        '9.00000000000519e+17': '900000000000519001',  # Annotation value (foundation metadata concept)
        '9.11753521000004e+17': '911753521000004108'   # Precision lost in last digits
    }

    if 'e+' in cleaned.lower() or 'e-' in cleaned.lower():
        if cleaned in scientific_notation_map:
            cleaned = scientific_notation_map[cleaned]
            stats['scientific_notation'] += 1
        else:
            stats['unmapped_scientific'] += 1
            return None

    # Remove SNOMED CT system annotations: "439401001 (SCT)" -> "439401001"
    elif '(' in cleaned and ')' in cleaned:
        cleaned = cleaned.split('(')[0].strip()
        stats['annotations'] += 1

    # Extract from pipe expressions: "16633941000119101 | Description |" -> "16633941000119101"
    elif '|' in cleaned:
        cleaned = cleaned.split('|')[0].strip()
        stats['pipe_expressions'] += 1

    # Handle multi-value entries (take first concept)
    if '\n' in cleaned:
        parts = [p.strip() for p in cleaned.split('\n') if p.strip()]
        if parts:
            cleaned = parts[0]
            stats['multivalue'] += 1
        else:
            return None

    # Remove .0 endings from float conversion
    if cleaned.endswith('.0'):
        # Check if it's a simple float (not scientific notation)
        if 'e' not in cleaned.lower():
            try:
                if cleaned[:-2].isdigit():
                    cleaned = cleaned[:-2]
                    stats['float_cleaned'] += 1
            except:
                pass

    # Remove non-breaking spaces (Unicode 160)
    if '\xa0' in cleaned or '\u00a0' in cleaned:
        cleaned = cleaned.replace('\xa0', '').replace('\u00a0', '')
        stats['non_breaking_space'] += 1

    # Fix known typo
    if cleaned == '44025001':
        cleaned = '444025001'
        stats['typo_fixed'] += 1

    # Final validation
    snomed_pattern = re.compile(r'^\d{6,18}$')
    if snomed_pattern.match(cleaned):
        return cleaned

    # Invalid format
    if cleaned and cleaned != original:
        stats['invalid_format'] += 1

    return None


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("Clean oBDS Mapping Data")
    print("=" * 70)

    # Load raw data
    print(f"\nLoading raw data: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        print("Run extract_mapping_table.py first to generate raw data.")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows from {df['Module'].nunique()} modules")

    # Initialize cleaning statistics
    cleaning_stats = {
        'float_cleaned': 0,
        'scientific_notation': 0,
        'unmapped_scientific': 0,
        'annotations': 0,
        'pipe_expressions': 0,
        'multivalue': 0,
        'dash_removed': 0,
        'non_breaking_space': 0,
        'typo_fixed': 0,
        'invalid_format': 0
    }

    # Apply cleaning to mapper columns
    print("\n=== CLEANING MAPPER COLUMNS ===")
    for mapper in MAPPERS:
        print(f"Cleaning {mapper}...")
        df[mapper] = df[mapper].apply(lambda x: clean_snomed_value(x, cleaning_stats))

    # Replace None with empty string for CSV
    df = df.fillna('')

    # Pseudonymize mapper columns before saving
    print("\n=== PSEUDONYMIZING MAPPER NAMES ===")
    df = df.rename(columns=MAPPER_PSEUDONYM_MAP)
    print("Mapper columns renamed for publication:")
    for old, new in MAPPER_PSEUDONYM_MAP.items():
        print(f"  {old} -> {new}")

    # Save cleaned data
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    # Report
    print(f"\n=== CLEANING STATISTICS ===")
    for operation, count in cleaning_stats.items():
        if count > 0:
            print(f"{operation:25s}: {count:5d}")

    print(f"\n=== CLEANED DATA STATISTICS ===")
    for pseudonym in MAPPER_PSEUDONYM_MAP.values():
        non_empty = (df[pseudonym] != '').sum()
        pct = non_empty / len(df) * 100
        print(f"{pseudonym:10s}: {non_empty:3d} valid concepts ({pct:5.1f}%)")

    print(f"\n=== OUTPUT ===")
    print(f"Cleaned data saved to: {OUTPUT_FILE}")
    print(f"Total rows: {len(df)}")
    print(f"Modules: {df['Module'].nunique()}")

    print("\n" + "=" * 70)
    print("CLEANING COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
