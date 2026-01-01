# Interactive Depth Structure Explorer - User Guide

**Tool**: `interactive-depth-explorer.py`
**Purpose**: Web-based UI for exploring basin mass vs depth relationships interactively

---

## Quick Start

### Launch the UI

```bash
python3 n-link-analysis/scripts/interactive-depth-explorer.py
```

Then open your browser to: **http://127.0.0.1:8050**

---

## Features

### Main Visualization (Center Panel)
- **Interactive log-log scatter plot** of basin mass vs max depth
- **Zoom/pan** controls (Plotly interactive)
- **Hover tooltips** showing N, depth, mass, entry breadth
- **Reference power-law lines** (adjustable α)
- **Fitted lines per cycle** (from regression analysis)
- **N labels** on data points (toggle on/off)

### Control Panel (Left Sidebar)

#### 1. Cycle Selection
- Multi-select dropdown
- Choose one or more cycles to display
- Default: All cycles selected

#### 2. N Value Range
- Slider to filter N values
- Range: 3-7
- Focus on specific N transitions (e.g., N=4-5)

#### 3. Reference Power-Law (α)
- Slider to adjust reference line exponent
- Range: 1.0-4.0 (step 0.1)
- Default: α=2.5 (discovered mean)
- Use to test hypotheses (α=2, 3, etc.)

#### 4. Display Options (Checkboxes)
- ☑ **Show reference power-law** - Gray dashed line at selected α
- ☑ **Show fitted lines** - Per-cycle fitted lines (dotted)
- ☑ **Show N labels** - Annotate points with N values
- ☑ **Log-log scale** - Toggle between log and linear axes

#### 5. Selection Statistics
- Real-time stats for filtered data
- Point count, cycle count, N range
- Depth and mass ranges
- Correlation coefficient

### Detail Panels (Bottom Row)

#### Depth vs N (Left)
- Line plot showing depth evolution across N
- All selected cycles overlaid
- Reveals N=5 peak visually

#### Basin Mass vs N (Right)
- Log-scale plot of mass vs N
- Shows basin mass trajectories
- Highlights N=5 peak

### Data Table (Bottom)
- Sortable table of all selected points
- Columns: Cycle, N, Basin Mass, Max Depth, Entry Breadth, Entry Ratio
- Auto-sorted by basin mass (largest first)

---

## Usage Scenarios

### Scenario 1: Compare Specific Cycles

**Goal**: Compare Massachusetts (low α) vs Autumn (high α)

**Steps**:
1. In cycle selector, choose only "Massachusetts ↔ Gulf_of_Maine" and "Autumn ↔ Summer"
2. Keep N range at [3, 7]
3. Enable "Show fitted lines"
4. Observe slope difference on log-log plot

**Expected**: Massachusetts has shallower slope (~1.87), Autumn steeper (~3.06)

### Scenario 2: Focus on N=4→N=5 Transition

**Goal**: Examine depth amplification at N=5

**Steps**:
1. Set N range to [4, 5] (just two values)
2. Select all cycles
3. Enable "Show N labels"
4. Zoom in on the region where N=5 points cluster

**Expected**: Clear vertical jump from N=4 (low depth) to N=5 (high depth)

### Scenario 3: Test Power-Law Exponent

**Goal**: Determine if α=2 or α=2.5 fits better

**Steps**:
1. Set reference α to 2.0
2. Observe how well data aligns with gray dashed line
3. Adjust α to 2.5
4. Compare visual fit

**Expected**: α=2.5 should align better with most cycles

### Scenario 4: Identify Outliers

**Goal**: Find cycles that deviate from universal α=2.5

**Steps**:
1. Set reference α to 2.5
2. Enable "Show fitted lines"
3. Look for cycles whose fitted lines diverge from reference
4. Select specific outlier cycles to isolate

**Expected**: Autumn and Massachusetts as extremes (α=3.06 vs α=1.87)

### Scenario 5: Explore Single Cycle in Detail

**Goal**: Deep dive into Massachusetts basin structure

**Steps**:
1. Select only "Massachusetts ↔ Gulf_of_Maine"
2. Keep all N values [3, 7]
3. Enable all display options
4. Zoom into the N=5 point (depth=168, mass=1M)

**Expected**: See extreme depth outlier at N=5, fitted line with α=1.87

---

## Interactivity Tips

### Zooming
- **Box zoom**: Click and drag to select region
- **Scroll zoom**: Mouse wheel over plot
- **Reset**: Double-click plot to reset view

### Panning
- Click and drag while zoomed in

### Exporting
- Use camera icon in Plotly toolbar (top right)
- Save current view as PNG

### Real-time Updates
- All controls update plots immediately
- No "Apply" button needed

---

## Technical Details

### Dependencies
```bash
pip install plotly dash dash-bootstrap-components pandas numpy
```

### Data Sources
- Input: `data/wikipedia/processed/analysis/entry_breadth_n={N}_full_analysis_2025_12_31.tsv`
- Fits: `data/wikipedia/processed/analysis/depth_exploration/power_law_fit_parameters.tsv`

### Port Configuration
- Default: `http://127.0.0.1:8050`
- To change port, edit `app.run_server(port=8050)` in script

### Performance
- Loads 30 data points (6 cycles × 5 N values)
- Updates instantly (<100ms)
- Handles up to ~1000 points before lag

---

## Advanced Usage

### Multiple Windows
Open multiple browser tabs to compare different views side-by-side:
- Tab 1: All cycles, N=3-7, α=2.5
- Tab 2: Single cycle, N=4-5, α=fitted
- Tab 3: High-α cycles only, N=3-7, α=3.0

### Keyboard Shortcuts (Plotly)
- **Ctrl+Scroll**: Zoom X-axis only
- **Shift+Scroll**: Zoom Y-axis only
- **Double-click**: Reset zoom

---

## Insights to Look For

### Visual Patterns

1. **Tight clustering** around α=2.5 reference line
   - Indicates universal power-law

2. **Vertical separation at N=5**
   - All cycles jump upward → depth peak

3. **Slope variation** between fitted lines
   - Wide spread (α ∈ [1.87, 3.06]) → cycle-specific geometry

4. **Outlier points**
   - Massachusetts N=5 (far right, top)
   - Autumn N=3,4 (far left, bottom)

### Quantitative Checks

1. **Correlation strength** (in statistics panel)
   - Should show r > 0.9 for depth vs mass
   - r < 0.2 for entry breadth vs mass

2. **Data table ordering**
   - Largest basins all at N=5 (top rows)
   - Smallest basins at N=4 or N=7 (bottom rows)

3. **N transition ratios**
   - Depth vs N panel: 5-10× jump at N=5
   - Mass vs N panel: 10-100× jump at N=5

---

## Troubleshooting

### "No module named 'dash'"
```bash
pip install dash dash-bootstrap-components
```

### "No module named 'plotly'"
```bash
pip install plotly
```

### Port already in use
Kill existing process:
```bash
lsof -ti:8050 | xargs kill -9
```

Or change port in script:
```python
app.run_server(port=8051)  # Use different port
```

### Slow updates
- Reduce number of selected cycles (<3)
- Disable "Show fitted lines" option
- Refresh browser

### Data not loading
Check file paths:
```bash
ls data/wikipedia/processed/analysis/entry_breadth_n=*
ls data/wikipedia/processed/analysis/depth_exploration/power_law_fit_parameters.tsv
```

---

## Next Steps After Exploration

Based on patterns discovered in the UI:

1. **Identify outliers** → Investigate what makes them special
2. **Test hypotheses** → Adjust α slider to see if predictions match data
3. **Focus analysis** → Use cycle selector to isolate interesting cases
4. **Export views** → Save PNG snapshots for documentation

---

## Example Session

**Goal**: Understand why Autumn has α=3.06 (highest)

1. Launch UI: `python3 n-link-analysis/scripts/interactive-depth-explorer.py`
2. Select only "Autumn ↔ Summer" cycle
3. Set α reference to 3.06 (the fitted value)
4. Observe tight alignment with reference line
5. Compare to Massachusetts (select both)
6. Notice Massachusetts has much shallower slope
7. Check data table: Autumn has smallest basins at N=3,4 but explodes at N=5
8. Hypothesis: Narrow entry funnel → extreme depth sensitivity

**Time**: 5-10 minutes

---

**Ready to explore!** 🚀

Launch the UI and discover patterns interactively. The visual interface reveals structure that's hard to see in static plots or tables alone.
