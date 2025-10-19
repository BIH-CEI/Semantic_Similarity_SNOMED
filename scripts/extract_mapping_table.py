"""
Extract raw mapping table from Excel file.

Creates a RAW (uncleaned) CSV with:
- Module: Module name (e.g., "Modul 5")
- oBDS_ID: oBDS concept identifier (e.g., "5.0")
- oBDS_Field: Field description
- Nina: Raw SNOMED CT ID from Nina (uncleaned)
- Sophie: Raw SNOMED CT ID from Sophie (uncleaned)
- Paul: Raw SNOMED CT ID from Paul (uncleaned)
- Lotte: Raw SNOMED CT ID from Lotte (uncleaned)

Usage:
    python scripts/extract_mapping_table.py

Output:
    data/interim/obds_mapping_table_raw.csv

NOTE: Uses Excel column positions (D=3, G=6, J=9, M=12) instead of column names
      because column names are inconsistent across modules.

      This extracts RAW data without cleaning. Run clean_mapping_data.py to
      clean the data and produce the final table in data/processed/.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "data/raw/oBDS/oBDS_Module_alle_neu.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "data/interim/obds_mapping_table_raw.csv"

# Mapper column positions in Excel (0-indexed)
# D=3 (Nina), G=6 (Sophie), J=9 (Paul), M=12 (Lotte)
MAPPER_POSITIONS = {
    'Nina': 3,
    'Sophie': 6,
    'Paul': 9,
    'Lotte': 12
}

def main():
    print("=" * 70)
    print("Extract RAW oBDS Mapping Table (No Cleaning)")
    print("=" * 70)

    # Load Excel directly (all sheets) - NO dtype specified to get raw values
    print(f"\nLoading: {INPUT_FILE}")
    excel_data = pd.read_excel(INPUT_FILE, sheet_name=None)

    print(f"Loaded {len(excel_data)} modules")

    # Extract rows using positional indices - NO CLEANING
    rows = []
    for module_name, df in excel_data.items():
        for idx, row in df.iterrows():
            # Get oBDS metadata from columns A, B, C
            obds_id = row.iloc[0]  # Column A: Identifier
            obds_field = row.iloc[1] if len(row) > 1 else ''  # Column B: Feldbezeichnung

            # Skip if no identifier
            if pd.isna(obds_id):
                continue

            # Build output row
            output_row = {
                'Module': module_name,
                'oBDS_ID': obds_id,
                'oBDS_Field': obds_field,
            }

            # Add mapper SNOMED IDs from positions D, G, J, M (RAW, NO CLEANING)
            for mapper_name, col_idx in MAPPER_POSITIONS.items():
                if col_idx < len(row):
                    value = row.iloc[col_idx]
                    # Store raw value as-is, convert to string
                    if pd.notna(value):
                        output_row[mapper_name] = str(value)
                    else:
                        output_row[mapper_name] = ''
                else:
                    output_row[mapper_name] = ''

            rows.append(output_row)

    # Create DataFrame
    df = pd.DataFrame(rows)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    # Report
    print(f"\n=== RAW EXTRACTION COMPLETE ===")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Total rows: {len(df)}")
    print(f"Modules: {df['Module'].nunique()}")

    print(f"\n=== RAW DATA STATISTICS (Non-Empty Cells) ===")
    for mapper in ['Nina', 'Sophie', 'Paul', 'Lotte']:
        non_empty = (df[mapper] != '').sum()
        pct = non_empty / len(df) * 100
        print(f"{mapper:8s}: {non_empty:3d} mappings ({pct:5.1f}%)")

    print(f"\n=== SAMPLE RAW ROWS ===")
    print(df.head(10).to_string())

    print("\n" + "=" * 70)
    print("RAW EXTRACTION COMPLETE")
    print(f"Next step: Run clean_mapping_data.py to clean this data")
    print("=" * 70)


if __name__ == '__main__':
    main()
