# Enhanced Depth Explorer User Guide

**URL**: http://127.0.0.1:8051/

**Purpose**: Interactive visualization for exploring depth distributions, variance patterns, and basin mass relationships discovered in the depth distribution analysis.

---

## Features

### Tab 1: Depth Distributions

**Single N View** (default):
- Shows histogram of convergence depths for selected N value
- Overlays mean (red), median (green), and 90th percentile (orange) as vertical lines
- Statistics box displays: mean, median, std dev, variance, skewness, max, path count

**Comparison Mode** (toggle "Show all N values side-by-side"):
- Displays all 5 N values (3, 4, 5, 6, 7) in stacked panels
- Shows mean and median lines for each N
- Height: 2000px (requires scrolling)
- Perfect for seeing bimodal pattern at N=5 vs unimodal at N=4

**Key Things to Explore**:
1. **N=5 bimodal pattern**: Look for two peaks/phases
   - Sharp peak at depth=6-12 (rapid local convergence)
   - Broad plateau at depth=40-100 (exploratory tail)
2. **N=4 vs N=5 contrast**: Compare sharp peak (N=4) to broad distribution (N=5)
3. **Skewness visualization**: See how N=5 has longest right tail
4. **Variance impact**: Notice N=5 histogram is "spread out" compared to N=4/N=6

---

### Tab 2: Basin Mass Analysis

**Interactive scatter plot**: Basin mass vs max depth
- Each point is a (cycle, N) combination
- Color-coded by N value
- Black dashed line: Power-law prediction (Mass ∝ Depth^2.5)
- Hover over points to see cycle name, depth, and mass

**Controls**:
- **Filter Cycles**: Select which cycles to display (multiselect dropdown)
- **Log scale toggle**: Switch between linear and log-log scale
  - Log scale recommended: reveals power-law as straight line

**Key Things to Explore**:
1. **Power-law validation**: In log scale, points should align with black dashed line
2. **N=5 depth dominance**: Look for N=5 points (specific color) at highest depths
3. **Cycle variation**: See how Massachusetts (highest mass) vs Latvia (lowest mass) differ
4. **Entry breadth irrelevance**: Points don't cluster by entry breadth, only depth

---

### Tab 3: Variance & Skewness

**Four-panel visualization**:
1. **Variance vs N** (top-left): Shows σ² explosion at N=5
2. **Standard Deviation vs N** (top-right): Shows σ pattern
3. **Skewness vs N** (bottom-left): Shows right-skew peak at N=5
4. **Coefficient of Variation vs N** (bottom-right): Normalized variance (σ/μ)

**Annotations**:
- N=5 variance annotated: "σ²=473 (4× higher than N=4)"
- N=5 skewness annotated: "1.88 (most right-skewed)"
- Reference line at skewness=0 (symmetric distribution)

**Key Things to Explore**:
1. **Variance spike**: N=5 and N=7 have variance ~450, N=4/N=6 have ~100-120
2. **CV pattern**: N=5 has highest CV (1.12), indicating most relative spread
3. **Skewness alternation**: Odd N (3,5,7) tend toward higher skewness
4. **N=3 symmetry**: Skewness≈0.5, nearly normal distribution

---

### Tab 4: Statistics Table

**Full statistics table** with columns:
- n, mean, median, p10, p25, p50, p75, p90, p95, p99, max, std, variance, skewness

**Highlighted**: N=5 row in green (highest variance, skewness)

**Key Insights box** below table summarizes:
- N=5 variance and skewness dominance
- Depth increase ratios
- Tail strength metrics
- N=7 highest mean depth

**Key Things to Explore**:
1. **Compare N=4 and N=5 rows**: See 4× variance increase, 1.43× mean depth increase
2. **p90/median ratios**: Calculate tail strength (N=5: 64/12=5.3×)
3. **N=7 vs N=5**: N=7 has higher mean (24.7 vs 19.4) but similar variance
4. **Percentile progression**: Watch how p90, p95, p99 diverge at N=5

---

## Left Sidebar Controls

### N Selector
Dropdown to choose N value for distribution histogram (Tab 1)
- Options: N=3, 4, 5, 6, 7
- Default: N=5 (most interesting)

### Comparison Mode
Toggle switch to show all N values side-by-side
- Useful for cross-N comparison
- Requires scrolling (2000px tall)

### Filter Cycles
Multiselect dropdown for basin mass plot (Tab 2)
- Options: All 6 cycles (Massachusetts, Sea_salt, Mountain, Autumn, Kingdom, Latvia)
- Default: All selected
- Deselect cycles to reduce clutter

### Plot Options
Log scale toggle for basin mass plot
- Checked (default): Log-log scale (power-law as straight line)
- Unchecked: Linear scale (harder to see pattern)

### Quick Stats Panel
Shows summary for selected N:
- Mean, median, 90th percentile, max depth
- Variance and skewness
- Tail ratio (p90/median)
- Updates when N selector changes

---

## Usage Scenarios

### Scenario 1: Understanding N=5 Variance Explosion

1. **Tab 1**: Select N=5, observe bimodal-like histogram
   - Note sharp peak at depth=12 (median)
   - Note broad tail extending to depth=100
2. **Tab 3**: See variance spike at N=5 (σ²=473)
3. **Tab 1**: Toggle comparison mode
   - Compare N=4 (narrow, σ²=121) to N=5 (broad, σ²=473)
   - See visual width difference
4. **Tab 4**: Check statistics table
   - Confirm variance: N=4 (121) vs N=5 (473) = 3.9× increase

### Scenario 2: Validating Power-Law Formula

1. **Tab 2**: Ensure log scale is enabled
2. View scatter plot: points should align with black dashed line (α=2.5)
3. Hover over points to see prediction vs observation
4. Deselect specific cycles to see if pattern holds for subsets
5. **Tab 4**: Check R²=0.888 (from correlation analysis)

### Scenario 3: Comparing Cycle Behaviors

1. **Tab 2**: Filter to just Massachusetts and Latvia (extremes)
   - Massachusetts: N=5 depth=168, mass=1M
   - Latvia: N=5 depth=31, mass=83k
2. **Tab 1**: Note that aggregate distributions don't separate by cycle (need per-cycle data)
3. Hypothesis: Massachusetts likely contributes to N=5 tail (depth>100)

### Scenario 4: Exploring Skewness Patterns

1. **Tab 3**: Focus on bottom-left panel (Skewness vs N)
2. Observe pattern:
   - N=3: 0.52 (nearly symmetric)
   - N=4: 1.63 (right-skewed)
   - N=5: 1.88 (most extreme)
   - N=6: 1.18 (moderate)
   - N=7: 1.34 (right-skewed)
3. **Tab 1**: Compare N=3 (symmetric histogram) to N=5 (extreme tail)
4. Hypothesis: Odd N values create more heterogeneous path behavior

### Scenario 5: Finding Depth Metrics

1. **Quick Stats Panel**: Select different N values (3-7)
2. Watch metrics update: mean, median, p90, tail ratio
3. Compare tail ratios:
   - N=3: 32.3/17 = 1.9×
   - N=4: 28/11 = 2.5×
   - N=5: 64/12 = 5.3× (strongest)
4. **Tab 4**: See full percentile table for precise values

---

## Technical Details

### Data Sources

**Basin mass data**:
- Files: `entry_breadth_n={N}_full_analysis_2025_12_31.tsv`
- 6 cycles × 5 N values = 30 data points

**Depth distributions**:
- Files: `path_characteristics_n={N}_mechanism_depth_distributions.tsv`
- ~1000 paths per N (973-988 convergent paths)

**Depth statistics**:
- File: `depth_distributions/depth_statistics_by_n.tsv`
- Precomputed mean, median, percentiles, variance, skewness

### Performance

- Load time: <2 seconds
- All plots are interactive (zoom, pan, hover)
- Comparison mode rendering: ~1 second (5 histograms)
- No data processing on interaction (all precomputed)

### Limitations

1. **Aggregate statistics only**: Cannot show per-cycle depth distributions
2. **Sample vs full basin**: Distributions from 1000 sample paths, not full basins
3. **No N=8+ data**: Currently limited to N=3-7

---

## Keyboard Shortcuts

- **Zoom**: Click and drag on any plot
- **Pan**: Hold Shift + click and drag
- **Reset**: Double-click on plot
- **Export**: Click camera icon (top-right of each plot)

---

## Stopping the Server

In terminal where server is running:
```bash
Ctrl+C
```

Or from another terminal:
```bash
# Find process ID
ps aux | grep interactive-depth-explorer-enhanced

# Kill process
kill <PID>
```

---

## Next Steps After Exploration

Based on patterns discovered interactively:

1. **Parse per-cycle depth distributions** to see if Massachusetts drives N=5 tail
2. **Extend to N=8** to test if variance drops (prediction: σ²≈150-250)
3. **Fit mixture models** to N=5 distribution (bimodal Gaussian or exponential + power-law)
4. **Hub connectivity analysis** to explain WHY N=5 creates bimodal pattern
5. **Correlate cycle-specific α with variance** (hypothesis: high variance → low α)

---

## Troubleshooting

**Port already in use**:
- Server runs on port 8051 (not 8050)
- If 8051 is occupied, edit script line 619: `port=8052`

**Module not found**:
```bash
pip install dash dash-bootstrap-components
```

**No data displayed**:
- Check that data files exist in `data/wikipedia/processed/analysis/`
- Run `analyze-depth-distributions.py` first to generate statistics

**Blank plots**:
- Refresh browser (Ctrl+R)
- Check browser console for JavaScript errors
- Try disabling browser extensions

---

## Example Insights from Interactive Exploration

From previous exploration sessions:

1. **N=5 distribution is NOT unimodal**: Visible two-phase structure (local + distant convergence)
2. **Variance correlates with tail**: High variance (N=5) → strong exploratory tail
3. **Power-law holds across cycles**: All points align with α=2.5 line in log-log plot
4. **N=7 mystery**: High mean depth (24.7) but doesn't dominate basin mass (coverage penalty?)
5. **N=4 uniformity**: Extremely narrow distribution (σ=11) → predictable rapid convergence

---

**Ready to explore!** 🚀

Open http://127.0.0.1:8051/ in your browser to start interactive analysis.
