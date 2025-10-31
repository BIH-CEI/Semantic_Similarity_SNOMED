# PlantUML Diagrams: Krippendorff's Alpha Methods

This folder contains PlantUML diagrams explaining the differences between the three Krippendorff's Alpha methods used in the oBDS SNOMED mapping quality assessment.

## Files Created

1. **`krippendorff_graph_comparison.puml`**
   - Side-by-side comparison of IS-A vs Full Relations graphs
   - Shows how relationships create shortcuts in the full graph
   - Best for: Understanding why Full α is slightly higher

2. **`distance_calculation_example.puml`**
   - Step-by-step distance calculation examples
   - Shows concrete mapper disagreement scenarios
   - Best for: Understanding the technical details

3. **`krippendorff_methods_comparison.puml`**
   - Comprehensive comparison table of all three methods
   - Standard (0.76) vs IS-A (0.84) vs Full (0.84)
   - Best for: Presentation slides overview

4. **`graph_structure_visual.puml`**
   - Visual representation of SNOMED CT graph structures
   - Tree (IS-A only) vs Network (Full relations)
   - Best for: Conceptual understanding

## How to Render

### Option 1: Online (Quickest)
1. Go to http://www.plantuml.com/plantuml/uml/
2. Copy the contents of any `.puml` file
3. Paste into the text box
4. Click "Submit" to generate PNG/SVG

### Option 2: VS Code Extension
1. Install "PlantUML" extension by jebbs
2. Open any `.puml` file
3. Press `Alt+D` to preview
4. Right-click preview → Export to PNG/SVG

### Option 3: Command Line
```bash
# Install PlantUML
# On Windows with chocolatey:
choco install plantuml

# Or download from https://plantuml.com/download

# Render all diagrams
plantuml *.puml

# This creates PNG files in the same directory
```

### Option 4: Python (programmatic)
```bash
pip install plantuml

python -c "
from plantuml import PlantUML
server = PlantUML(url='http://www.plantuml.com/plantuml/img/')
with open('krippendorff_methods_comparison.puml', 'r') as f:
    uml = f.read()
    server.processes_file('krippendorff_methods_comparison.puml')
"
```

## Recommended Usage

**For your presentation:**
- **Slide 1 (Methods Overview)**: Use `krippendorff_methods_comparison.puml`
  - Shows all three methods side-by-side
  - Clear comparison table at bottom

- **Slide 2 (Why semantic matters)**: Use `graph_structure_visual.puml`
  - Visual tree vs network distinction
  - Shows "Finding site" shortcuts

- **Backup/Appendix**: Keep `distance_calculation_example.puml`
  - For technical questions during Q&A
  - Detailed step-by-step calculations

## Key Messages

1. **Standard α = 0.7634**: Binary agreement (identical vs different)
   - Treats all disagreements equally
   - Ignores clinical similarity

2. **IS-A α = 0.8380**: Hierarchical distance
   - Recognizes parent-child relationships
   - Rewards choosing related concepts

3. **Full α = 0.8424**: Network distance
   - Uses all SNOMED relationships
   - Captures full semantic similarity
   - Only 0.4% higher than IS-A (most disagreements are within same hierarchy)

## Why the small difference between IS-A and Full?

In your data, most mapper disagreements are:
- Parent-child relationships (e.g., "Cancer" vs "Lung Cancer")
- Same clinical branch (e.g., "SCLC" vs "NSCLC")

These are captured well by IS-A alone.

Full relations would show larger improvements if mappers chose:
- Cross-branch related codes (e.g., "Lung Cancer" + "Bronchoscopy")
- Codes related by anatomy, morphology, or causation

Your results suggest mappers are **consistently choosing within the same clinical domain** - which is excellent for data quality!

## Citation

Semantic Krippendorff's Alpha method based on:
- Solís-Labastida et al. (2023). "Semantic Krippendorff's Alpha for continuous word embeddings."
- Adapted for SNOMED CT graph distances using NetworkX shortest path algorithms.

---

**Created:** 2025-10-20
**Project:** oBDS SNOMED CT Mapping Quality Assessment
**For:** Presentation preparation
