"""
Visualize Krippendorff's Alpha Results

Creates publication-ready visualizations of inter-rater agreement analysis
with German module labels from basisdatensatz.de.

Usage:
    python scripts/visualize_results.py

Output:
    - results/figures/alpha_by_module_sorted.png
    - results/figures/mapper_coverage.png
    - results/figures/missing_patterns.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from obds_modules import MODULE_NAMES

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Find most recent results files
krippendorff_files = sorted(RESULTS_DIR.glob("krippendorff_by_module_*.csv"))
missing_files = sorted(RESULTS_DIR.glob("missing_values_analysis_*.csv"))

if not krippendorff_files:
    raise FileNotFoundError("No Krippendorff results found")
if not missing_files:
    raise FileNotFoundError("No missing values analysis found")

KRIPPENDORFF_FILE = krippendorff_files[-1]
MISSING_FILE = missing_files[-1]

# Use shared module reference
MODULE_LABELS = MODULE_NAMES

# Color scheme
COLORS = {
    'primary': '#2E86AB',     # Blue
    'secondary': '#A23B72',   # Purple
    'accent': '#F18F01',      # Orange
    'good': '#06A77D',        # Green
    'poor': '#D62246',        # Red
    'neutral': '#6C757D'      # Gray
}

# ============================================================================
# VISUALIZATION 1: SORTED ALPHA BY MODULE
# ============================================================================

def plot_alpha_by_module():
    """Create sorted bar chart of Krippendorff's Alpha by module."""
    print("Creating sorted alpha by module chart...")

    # Load data
    df = pd.read_csv(KRIPPENDORFF_FILE)

    # Filter out modules with NaN or zero alpha
    df = df[df['alpha_nominal'].notna()]
    df = df[df['alpha_nominal'] != 0.0]

    # Add German labels
    df['label'] = df['module'].map(MODULE_LABELS)

    # Sort by alpha value
    df = df.sort_values('alpha_nominal', ascending=True)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Color bars based on alpha value
    colors = []
    for alpha in df['alpha_nominal']:
        if alpha >= 0.8:
            colors.append(COLORS['good'])
        elif alpha >= 0.667:
            colors.append(COLORS['primary'])
        elif alpha >= 0.4:
            colors.append(COLORS['accent'])
        else:
            colors.append(COLORS['poor'])

    # Create horizontal bar chart
    bars = ax.barh(range(len(df)), df['alpha_nominal'], color=colors, alpha=0.8)

    # Add value labels on bars
    for i, (alpha, n) in enumerate(zip(df['alpha_nominal'], df['n_concepts'])):
        ax.text(alpha + 0.02, i, f'{alpha:.3f}',
                va='center', ha='left', fontsize=9, fontweight='bold')
        ax.text(0.01, i, f'(n={n})',
                va='center', ha='left', fontsize=7, color='white', fontweight='bold')

    # Set labels
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df['label'], fontsize=10)
    ax.set_xlabel("Krippendorff's Alpha (κ)", fontsize=11, fontweight='bold')
    ax.set_title("Inter-Rater Reliability by oBDS Module\n(sorted by κ value)",
                 fontsize=13, fontweight='bold', pad=20)

    # Add reference lines
    ax.axvline(x=0.667, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='κ = 0.667 (Tentative)')
    ax.axvline(x=0.8, color='green', linestyle='--', linewidth=1, alpha=0.5, label='κ = 0.800 (Good)')

    # Styling
    ax.set_xlim(0, 1.0)
    ax.grid(axis='x', alpha=0.3, linestyle=':')
    ax.legend(loc='lower right', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add overall alpha as text
    overall_alpha = df['alpha_nominal'].mean()
    fig.text(0.99, 0.01, f'Overall κ: {overall_alpha:.3f}',
             ha='right', fontsize=10, style='italic', color='gray')

    plt.tight_layout()
    output_file = FIGURES_DIR / "alpha_by_module_sorted.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


# ============================================================================
# VISUALIZATION 2: MAPPER COVERAGE
# ============================================================================

def plot_mapper_coverage():
    """Create bar chart showing mapper coverage percentages."""
    print("Creating mapper coverage chart...")

    # Load data
    df = pd.read_csv(MISSING_FILE)

    # Calculate overall coverage for each mapper
    total_concepts = df['N'].sum()
    mappers = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']

    coverage_data = []
    for mapper in mappers:
        present = total_concepts - df[f'{mapper}_missing'].sum()
        pct = present / total_concepts * 100
        coverage_data.append({'Mapper': mapper, 'Coverage': pct, 'Present': int(present), 'Total': int(total_concepts)})

    coverage_df = pd.DataFrame(coverage_data)

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    # Create bar chart
    x = range(len(coverage_df))
    bars = ax.bar(x, coverage_df['Coverage'], color=COLORS['primary'], alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels
    for i, (pct, present, total) in enumerate(zip(coverage_df['Coverage'],
                                                    coverage_df['Present'],
                                                    coverage_df['Total'])):
        ax.text(i, pct + 1, f'{pct:.1f}%\n({present}/{total})',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Set labels
    ax.set_xticks(x)
    ax.set_xticklabels(coverage_df['Mapper'], fontsize=11)
    ax.set_ylabel('Coverage (%)', fontsize=11, fontweight='bold')
    ax.set_title('Mapper Coverage Across All Modules',
                 fontsize=13, fontweight='bold', pad=15)

    # Styling
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3, linestyle=':')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_file = FIGURES_DIR / "mapper_coverage.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


# ============================================================================
# VISUALIZATION 3: MISSING PATTERNS HEATMAP
# ============================================================================

def plot_missing_patterns():
    """Create heatmap showing missing value patterns by module and mapper."""
    print("Creating missing patterns heatmap...")

    # Load data
    df = pd.read_csv(MISSING_FILE)

    # Add German labels
    df['label'] = df['Module'].map(MODULE_LABELS)

    # Create matrix of missing percentages
    mappers = ['Mapper_A', 'Mapper_B', 'Mapper_C', 'Mapper_D']
    matrix = []
    labels = []

    for _, row in df.iterrows():
        if pd.isna(row['label']):
            continue
        values = [row[f'{mapper}_pct'] for mapper in mappers]
        matrix.append(values)
        labels.append(f"{row['label']} (n={int(row['N'])})")

    matrix = np.array(matrix)

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 10))

    # Create heatmap
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=100)

    # Set ticks
    ax.set_xticks(range(len(mappers)))
    ax.set_xticklabels(mappers, fontsize=10)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)

    # Add values as text
    for i in range(len(labels)):
        for j in range(len(mappers)):
            value = matrix[i, j]
            color = 'white' if value > 50 else 'black'
            ax.text(j, i, f'{value:.0f}%',
                   ha='center', va='center', fontsize=8, color=color, fontweight='bold')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Missing Values (%)', fontsize=10, fontweight='bold')

    # Title
    ax.set_title('Missing Values by Module and Mapper',
                 fontsize=13, fontweight='bold', pad=15)

    plt.tight_layout()
    output_file = FIGURES_DIR / "missing_patterns.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Generate all visualizations."""
    print("=" * 70)
    print("Generating Visualizations")
    print("=" * 70)
    print(f"\nKrippendorff results: {KRIPPENDORFF_FILE.name}")
    print(f"Missing values: {MISSING_FILE.name}")
    print(f"Output directory: {FIGURES_DIR}")

    # Generate visualizations
    plot_alpha_by_module()
    plot_mapper_coverage()
    plot_missing_patterns()

    print("\n" + "=" * 70)
    print("VISUALIZATION COMPLETE")
    print("=" * 70)
    print(f"\nGenerated {len(list(FIGURES_DIR.glob('*.png')))} figures in: {FIGURES_DIR}")


if __name__ == '__main__':
    main()
