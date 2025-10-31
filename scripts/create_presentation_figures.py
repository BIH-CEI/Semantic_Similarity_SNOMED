"""
Create Figures for Presentation

Generates publication-quality figures for the oBDS SNOMED mapping
quality assessment presentation.

Figures created:
1. Agreement metrics progression (Standard -> IS-A -> Full Relations)
2. Module-level quality heatmap
3. Mapping difficulty distribution
4. Gap analysis candidates visualization

Usage:
    python scripts/create_presentation_figures.py

Output:
    - results/figures/ directory with PNG files
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from obds_modules import MODULE_NAMES_SHORT

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "results" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Set publication style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("colorblind")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# FIGURE 1: AGREEMENT METRICS PROGRESSION
# ============================================================================

def create_alpha_progression_figure():
    """
    Create bar chart showing progression from Standard to IS-A to Full Relations alpha.
    """
    print("Creating Figure 1: Alpha Progression...")

    # Data from results (krippendorff_summary_20251019_180709.csv)
    methods = ['Standard\n(Nominal)', 'Semantic\n(IS-A only)', 'Semantic\n(Full Relations)']
    alphas = [0.7634, 0.8380, 0.8424]
    colors = ['#e74c3c', '#f39c12', '#27ae60']

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(methods, alphas, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels on bars
    for i, (bar, alpha) in enumerate(zip(bars, alphas)):
        height = bar.get_height()
        improvement = ""
        if i > 0:
            diff = alpha - alphas[i-1]
            improvement = f"\n(+{diff:.4f})"
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{alpha:.4f}{improvement}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel("Krippendorff's Alpha", fontsize=12, fontweight='bold')
    ax.set_xlabel("Agreement Metric", fontsize=12, fontweight='bold')
    ax.set_title("Progression of Agreement Metrics\noBDS SNOMED CT Mapping Quality Assessment",
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_ylim(0, 1.0)

    # Add interpretation zones
    ax.axhspan(0.8, 1.0, alpha=0.1, color='green', label='Excellent agreement')
    ax.axhspan(0.667, 0.8, alpha=0.1, color='yellow', label='Good agreement')
    ax.axhspan(0, 0.667, alpha=0.1, color='red', label='Moderate agreement')

    # Add grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Add legend
    ax.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    output_file = OUTPUT_DIR / "fig1_alpha_progression.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


# ============================================================================
# FIGURE 2: MODULE-LEVEL HEATMAP
# ============================================================================

def create_module_heatmap():
    """
    Create heatmap showing Standard, IS-A, and Full Relations alpha by module.
    """
    print("Creating Figure 2: Module-level Quality Heatmap...")

    # Load comparison data
    comparison_file = sorted(PROJECT_ROOT.glob("results/alpha_comparison_all_methods_*.csv"))[-1]
    df = pd.read_csv(comparison_file)

    # Add readable module names (using shared module reference)
    df['module_label'] = df['module'].map(MODULE_NAMES_SHORT)

    # Prepare data for heatmap
    modules = df['module_label'].values
    data = df[['alpha_nominal', 'alpha_semantic_isa', 'alpha_semantic_full']].values.T

    fig, ax = plt.subplots(figsize=(16, 6))

    # Create heatmap using pcolormesh (better for gridlines)
    im = ax.pcolormesh(data, cmap='RdYlGn', vmin=0, vmax=1, edgecolors='white', linewidth=2)

    # Set ticks - center them in cells
    ax.set_xticks(np.arange(len(modules)) + 0.5)
    ax.set_yticks(np.arange(3) + 0.5)
    ax.set_xticklabels(modules, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(['Standard\n(Nominal)', 'Semantic\n(IS-A only)', 'Semantic\n(Full Relations)'],
                       fontsize=10, fontweight='bold')

    # Add values to cells - offset to center of cells
    for i in range(3):
        for j in range(len(modules)):
            if not np.isnan(data[i, j]):
                # Determine text color based on background
                text_color = 'white' if data[i, j] < 0.5 else 'black'
                text = ax.text(j + 0.5, i + 0.5, f'{data[i, j]:.3f}',
                             ha="center", va="center", color=text_color,
                             fontsize=8, fontweight='bold')

    ax.set_title("Krippendorff's Alpha by Module and Method\n480 oBDS Items (with 2+ Mappers), 4 Independent Mappers",
                 fontsize=14, fontweight='bold', pad=20)

    # Set axis limits to show grid properly
    ax.set_xlim(0, len(modules))
    ax.set_ylim(0, 3)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Krippendorff's Alpha", rotation=270, labelpad=20, fontsize=11, fontweight='bold')

    # Add interpretation zones to colorbar
    cbar.ax.axhline(y=0.8, color='black', linestyle='--', linewidth=1, alpha=0.5)
    cbar.ax.axhline(y=0.667, color='black', linestyle='--', linewidth=1, alpha=0.5)
    cbar.ax.text(1.5, 0.9, 'Excellent', fontsize=8, va='center')
    cbar.ax.text(1.5, 0.73, 'Good', fontsize=8, va='center')
    cbar.ax.text(1.5, 0.33, 'Moderate', fontsize=8, va='center')

    plt.tight_layout()
    output_file = OUTPUT_DIR / "fig2_module_heatmap.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


# ============================================================================
# FIGURE 3: MAPPING DIFFICULTY DISTRIBUTION
# ============================================================================

def create_difficulty_distribution():
    """
    Create histogram showing distribution of Mapping Difficulty Index (MDI).
    """
    print("Creating Figure 3: Difficulty Distribution...")

    # Load difficulty scores
    diff_file = sorted(PROJECT_ROOT.glob("results/mapping_difficulty_scores_*.csv"))[-1]
    df = pd.read_csv(diff_file)

    # Load module-level summary
    module_file = sorted(PROJECT_ROOT.glob("results/module_difficulty_summary_*.csv"))[-1]
    module_df = pd.read_csv(module_file, index_col=0)

    # Add module labels
    module_df['label'] = module_df.index.map(MODULE_NAMES_SHORT)
    module_df = module_df.sort_values('mdi_mean', ascending=False)

    # Filter to valid MDI
    valid_mdi = df[df['mdi'].notna()]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))

    # Subplot 1: Histogram
    ax1.hist(valid_mdi['mdi'], bins=30, color='steelblue', alpha=0.7, edgecolor='black')
    ax1.axvline(valid_mdi['mdi'].mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {valid_mdi["mdi"].mean():.3f}')
    ax1.axvline(valid_mdi['mdi'].median(), color='orange', linestyle='--', linewidth=2,
                label=f'Median: {valid_mdi["mdi"].median():.3f}')

    ax1.set_xlabel('Mapping Difficulty Index (MDI)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Number of Items', fontsize=11, fontweight='bold')
    ax1.set_title('Distribution of Mapping Difficulty\n(n=480 items with 2+ coders)',
                  fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Subplot 2: Category counts
    categories = valid_mdi['interpretation'].value_counts()
    colors_cat = {'Easy (high agreement, close concepts)': '#27ae60',
                  'Moderate (some disagreement, related concepts)': '#f39c12',
                  'Difficult (divergent codes, semantic distance)': '#e74c3c'}

    category_order = [
        'Easy (high agreement, close concepts)',
        'Moderate (some disagreement, related concepts)',
        'Difficult (divergent codes, semantic distance)'
    ]

    counts = [categories.get(cat, 0) for cat in category_order]
    bar_colors = [colors_cat.get(cat, 'gray') for cat in category_order]

    bars = ax2.bar(range(len(category_order)), counts, color=bar_colors, alpha=0.8, edgecolor='black')

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{int(height)}\n({height/len(valid_mdi)*100:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax2.set_xticks(range(len(category_order)))
    ax2.set_xticklabels(['Easy\n(MDI < 0.3)', 'Moderate\n(0.3 ≤ MDI < 0.6)', 'Difficult\n(MDI ≥ 0.6)'],
                        fontsize=10)
    ax2.set_ylabel('Number of Items', fontsize=11, fontweight='bold')
    ax2.set_title('Difficulty Categories', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # Subplot 3: Module-level means with error bars
    # Color by difficulty
    colors_module = []
    for mdi in module_df['mdi_mean']:
        if mdi < 0.1:
            colors_module.append('#27ae60')
        elif mdi < 0.3:
            colors_module.append('#f39c12')
        else:
            colors_module.append('#e74c3c')

    y_pos = range(len(module_df))
    ax3.barh(y_pos, module_df['mdi_mean'], xerr=module_df['mdi_std'],
             color=colors_module, alpha=0.7, edgecolor='black', linewidth=1,
             capsize=4, error_kw={'linewidth': 1.5, 'elinewidth': 1.5})

    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(module_df['label'], fontsize=9)
    ax3.set_xlabel('Mean MDI ± SD', fontsize=11, fontweight='bold')
    ax3.set_title('Mean Difficulty by Module\n(with standard deviation)', fontsize=12, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)
    ax3.axvline(x=0.1, color='green', linestyle='--', alpha=0.5, linewidth=1)
    ax3.axvline(x=0.3, color='orange', linestyle='--', alpha=0.5, linewidth=1)

    # Add sample size annotations
    for i, (idx, row) in enumerate(module_df.iterrows()):
        ax3.text(row['mdi_mean'] + row['mdi_std'] + 0.01, i,
                f"n={int(row['mdi_count'])}",
                va='center', fontsize=8, style='italic')

    plt.tight_layout()
    output_file = OUTPUT_DIR / "fig3_difficulty_distribution.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


# ============================================================================
# FIGURE 4: GAP ANALYSIS CANDIDATES
# ============================================================================

def create_gap_analysis_figure():
    """
    Create scatter plot showing gap analysis candidates with MDI vs semantic distance.
    """
    print("Creating Figure 4: Gap Analysis Visualization...")

    # Load difficulty scores
    diff_file = sorted(PROJECT_ROOT.glob("results/mapping_difficulty_scores_*.csv"))[-1]
    df = pd.read_csv(diff_file)

    valid_df = df[df['mdi'].notna()].copy()

    # Create categories
    valid_df['category'] = pd.cut(valid_df['mdi'],
                                   bins=[-np.inf, 0.3, 0.5, np.inf],
                                   labels=['Ready for implementation', 'Consensus needed', 'Gap analysis'])

    fig, ax = plt.subplots(figsize=(12, 8))

    # Color map
    colors = {'Ready for implementation': '#27ae60',
              'Consensus needed': '#f39c12',
              'Gap analysis': '#e74c3c'}

    for category in ['Ready for implementation', 'Consensus needed', 'Gap analysis']:
        subset = valid_df[valid_df['category'] == category]
        ax.scatter(subset['semantic_disagreement'], subset['mdi'],
                  c=colors[category], label=category, alpha=0.6, s=100, edgecolors='black', linewidth=0.5)

    # Highlight top 5 gap candidates
    top_gap = valid_df.nlargest(5, 'mdi')
    ax.scatter(top_gap['semantic_disagreement'], top_gap['mdi'],
              c='red', marker='*', s=500, edgecolors='black', linewidth=1.5,
              label='Top 5 gap candidates', zorder=10)

    # Add reference lines
    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, linewidth=1.5, label='Gap threshold (MDI=0.5)')
    ax.axhline(y=0.3, color='orange', linestyle='--', alpha=0.5, linewidth=1.5, label='Consensus threshold (MDI=0.3)')

    ax.set_xlabel('Semantic Disagreement\n(Mean SNOMED distance, normalized)',
                  fontsize=12, fontweight='bold')
    ax.set_ylabel('Mapping Difficulty Index (MDI)', fontsize=12, fontweight='bold')
    ax.set_title('Mapping Difficulty vs Semantic Distance\nIdentifying Gap Analysis Candidates',
                 fontsize=14, fontweight='bold', pad=20)

    ax.legend(loc='upper left', fontsize=9)
    ax.grid(alpha=0.3)

    # Add text annotations
    ax.text(0.95, 0.05, f'n = {len(valid_df)} items\nGap candidates: {len(valid_df[valid_df["mdi"] >= 0.5])}',
            transform=ax.transAxes, fontsize=10, verticalalignment='bottom',
            horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    output_file = OUTPUT_DIR / "fig4_gap_analysis.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


# ============================================================================
# FIGURE 5: COMPLETENESS VS AGREEMENT
# ============================================================================

def create_quality_scatter():
    """
    Create scatter plot showing Quality = Completeness x Agreement.
    Uses jitter and bubble sizes to show overlapping points.
    """
    print("Creating Figure 5: Quality Score Visualization...")

    # Load quality scores
    quality_file = sorted(PROJECT_ROOT.glob("results/item_quality_scores_*.csv"))[-1]
    df = pd.read_csv(quality_file)

    # Remove items with no codes (NaN agreement)
    df_plot = df[df['agreement'].notna()].copy()

    fig, ax = plt.subplots(figsize=(12, 9))

    # Color by interpretation
    color_map = {
        'Perfect (all 4 agree)': '#27ae60',
        'Excellent (all responded, high agreement)': '#2ecc71',
        'Perfect agreement but incomplete': '#3498db',
        'Complete but disputed': '#e74c3c',
        'Moderate quality': '#f39c12',
        'Low quality': '#c0392b',
        'Single code (no validation)': '#95a5a6',
        'No codes provided': '#7f8c8d'
    }

    # Plot with consistent marker size, using alpha to show density
    for interp in color_map.keys():
        subset = df_plot[df_plot['interpretation'] == interp]
        if len(subset) > 0:
            ax.scatter(subset['completeness'], subset['agreement'],
                      c=color_map[interp],
                      label=f"{interp} (n={len(subset)})",
                      alpha=0.4, s=150, edgecolors='black', linewidth=0.5)

    # Add text annotations showing counts at each unique position
    position_counts = df_plot.groupby(['completeness', 'agreement']).size().reset_index(name='count')
    for _, row in position_counts.iterrows():
        if row['count'] > 10:  # Only annotate positions with many items
            ax.text(row['completeness'], row['agreement'],
                   f"{int(row['count'])}",
                   fontsize=9, fontweight='bold',
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

    # Add diagonal lines (quality score)
    for q in [0.25, 0.5, 0.75, 1.0]:
        x = np.linspace(0, 1, 100)
        y = q / x
        y[y > 1] = np.nan
        ax.plot(x, y, 'k--', alpha=0.2, linewidth=1)
        # Label
        if q < 1.0:
            ax.text(q + 0.02, 0.98, f'Q={q:.2f}', fontsize=8, alpha=0.5, rotation=-45)

    ax.set_xlabel('Completeness (proportion of mappers who provided code)',
                  fontsize=11, fontweight='bold')
    ax.set_ylabel('Agreement (proportion agreeing with most common code)',
                  fontsize=11, fontweight='bold')
    ax.set_title('Quality = Completeness × Agreement\n519 oBDS Items (counts shown for positions with >10 items)',
                 fontsize=14, fontweight='bold', pad=20)

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

    ax.legend(loc='lower left', fontsize=8, ncol=2, framealpha=0.9)
    ax.grid(alpha=0.3)

    # Add quadrant labels
    ax.text(0.75, 0.25, 'Complete\nBUT\nDisputed', ha='center', va='center',
            fontsize=10, alpha=0.3, fontweight='bold', style='italic')
    ax.text(0.25, 0.75, 'Agreement\nBUT\nIncomplete', ha='center', va='center',
            fontsize=10, alpha=0.3, fontweight='bold', style='italic')
    ax.text(0.75, 0.75, 'HIGH\nQUALITY', ha='center', va='center',
            fontsize=12, alpha=0.4, fontweight='bold', color='green')

    plt.tight_layout()
    output_file = OUTPUT_DIR / "fig5_quality_scatter.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


# ============================================================================
# FIGURE 6: MODULE DIFFICULTY RANKING
# ============================================================================

def create_module_difficulty_ranking():
    """
    Create horizontal bar chart ranking modules by difficulty.
    """
    print("Creating Figure 6: Module Difficulty Ranking...")

    # Load module difficulty
    module_file = sorted(PROJECT_ROOT.glob("results/module_difficulty_summary_*.csv"))[-1]
    df = pd.read_csv(module_file, index_col=0)

    # Add extended labels
    df['label'] = df.index.map(MODULE_NAMES_SHORT)

    # Sort by mean MDI
    df_sorted = df.sort_values('mdi_mean', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Color bars by difficulty level
    colors = []
    for mdi in df_sorted['mdi_mean']:
        if mdi < 0.1:
            colors.append('#27ae60')
        elif mdi < 0.3:
            colors.append('#f39c12')
        else:
            colors.append('#e74c3c')

    bars = ax.barh(range(len(df_sorted)), df_sorted['mdi_mean'], color=colors,
                   alpha=0.7, edgecolor='black', linewidth=1)

    # Set y-axis labels to extended module names
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted['label'], fontsize=10)

    # Add value labels
    for i, (idx, row) in enumerate(df_sorted.iterrows()):
        ax.text(row['mdi_mean'] + 0.01, i,
                f"{row['mdi_mean']:.3f} (n={int(row['mdi_count'])})",
                va='center', fontsize=9)

    ax.set_xlabel('Mean Mapping Difficulty Index (MDI)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Module', fontsize=11, fontweight='bold')
    ax.set_title('Module-Level Difficulty Ranking\nLower = Easier to Map',
                 fontsize=14, fontweight='bold', pad=20)

    # Add reference lines
    ax.axvline(x=0.1, color='green', linestyle='--', alpha=0.5, linewidth=1.5, label='Easy threshold')
    ax.axvline(x=0.3, color='orange', linestyle='--', alpha=0.5, linewidth=1.5, label='Moderate threshold')

    ax.legend(loc='lower right')
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    output_file = OUTPUT_DIR / "fig6_module_ranking.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("Creating Presentation Figures")
    print("=" * 70)
    print(f"\nOutput directory: {OUTPUT_DIR}\n")

    create_alpha_progression_figure()
    create_module_heatmap()

    # NOTE: Figures 3-6 disabled due to MDI metric issues:
    # - High multicollinearity (disagreement r=0.95 with diversity)
    # - Disagreement alone explains 98.8% of MDI variance
    # - Error bars exceed means (CV > 100% for many modules)
    # Keeping only robust Krippendorff Alpha analyses (Figures 1-2)

    # create_difficulty_distribution()
    # create_gap_analysis_figure()
    # create_quality_scatter()
    # create_module_difficulty_ranking()

    print("\n" + "=" * 70)
    print("FIGURE CREATION COMPLETE")
    print("=" * 70)
    print(f"\nAll figures saved to: {OUTPUT_DIR}")
    print("\nFigures created:")
    print("  1. fig1_alpha_progression.png - Agreement metrics comparison")
    print("  2. fig2_module_heatmap.png - Module-level quality by method")
    print("\n  [Figures 3-6 disabled - MDI metric has statistical issues]")


if __name__ == '__main__':
    main()
