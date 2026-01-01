# N-Link Analysis Framework Testing Plan

**Created**: 2026-01-01
**Last Updated**: 2026-01-01
**Purpose**: Systematic validation of analysis infrastructure before production runs
**Status**: ✅ VALIDATION COMPLETE
**Target**: Complete framework validation for Multi-N analysis (N=2-10)

---

## Current State

### What's Been Validated ✓
- **Single N execution (N=5)**: Harness runs successfully in quick mode (6 cycles, ~30-60 min)
- **Visualization pipeline**: All 9 N=5 cycles visualized (3D basins, 2D dashboards, interactive HTML)
- **Core scripts (26 total)**: All execute without errors for N=5
- **Report generation**: Human-facing reports generated successfully
- **Data dependencies**: Validation script confirms all required files present

### What Hasn't Been Tested ✗
- **Multi-N execution**: Running harness for N≠5 (especially N=3,4,6,7,8,9,10)
- **Cross-N comparison**: Scripts that aggregate across multiple N values
- **Edge cases**: N=1, N=2, very large N (N>15)
- **Error recovery**: What happens when scripts fail mid-pipeline
- **Reproducibility**: Do runs with same parameters produce identical outputs?
- **Performance scaling**: How does runtime scale with basin size?
- **Resource limits**: Memory/disk usage for giant basins (Massachusetts at N≠5)

---

## Testing Philosophy

**Goal**: Validate infrastructure is production-ready for Multi-N systematic comparison (Tier 1.1 in NEXT-STEPS.md)

**Approach**: Incremental validation with increasing complexity
1. Test individual N values (N=3,4,6,7) one at a time
2. Test edge cases (N=1,2,8,9,10)
3. Test cross-N comparison scripts
4. Test error handling and recovery
5. Full Multi-N pipeline validation

**Success Criteria**:
- ✓ Harness completes without errors for all N∈{3,4,5,6,7,8,9,10}
- ✓ Outputs are consistent (same N, same parameters → same results)
- ✓ Cross-N comparison scripts produce meaningful visualizations
- ✓ Documentation is accurate (parameters, outputs match reality)
- ✓ No silent failures (if script fails, harness catches it)

---

## Testing Tiers

### Tier 0: Individual N Validation (Priority: CRITICAL)

**Goal**: Verify harness works for N values beyond N=5

**Test Cases**:

#### TC0.1: N=3 Quick Mode
```bash
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 3 --tag test_n3_quick
```

**Expected**:
- Completes in ~20-40 min (smaller basins than N=5)
- Generates 6 cycle basins (same cycles or different?)
- All outputs tagged with test_n3_quick

**Validate**:
- [ ] Harness completes without errors
- [ ] Check `data/wikipedia/processed/analysis/*test_n3_quick*` files created
- [ ] Compare basin sizes to N=5 (should be smaller based on coverage data)
- [ ] Review `n-link-analysis/report/overview.md` for N=3 results

**Key Question**: Do the same cycles appear at N=3? (Massachusetts, Sea_salt, etc.)

---

#### TC0.2: N=4 Quick Mode
```bash
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 4 --tag test_n4_quick
```

**Expected**:
- Fastest convergence (from mechanism comparison data: median ~11 steps)
- Different cycles than N=5? (need to check sample-nlink-traces output)
- Lower HALT rate (~1-2%)

**Validate**:
- [ ] Harness completes
- [ ] Basin sizes smaller than N=5 (coverage 35% vs 32.6%)
- [ ] Depth distributions shallower than N=5
- [ ] Trunkiness patterns different from N=5

---

#### TC0.3: N=6 Quick Mode
```bash
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 6 --tag test_n6_quick
```

**Expected**:
- Higher HALT rate (~10% based on mechanism comparison)
- Basin mass smaller than N=5 (~290k vs 1.99M)
- Different cycle landscape

**Validate**:
- [ ] Check HALT rate in sample-nlink-traces output
- [ ] Confirm basin mass decline from N=5 peak
- [ ] Verify fragmentation increase

---

#### TC0.4: N=7 Quick Mode
```bash
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 7 --tag test_n7_quick
```

**Expected**:
- Slowest convergence (median ~20 steps)
- HALT rate ~12%
- Deep basins (similar to or deeper than N=5)
- Bimodal depth distribution

**Validate**:
- [ ] Convergence depth matches predictions
- [ ] Basin mass smaller than N=5 but larger than N=6
- [ ] Depth distribution shows bimodal pattern

---

### Tier 1: Edge Case Testing (Priority: HIGH)

**Goal**: Test boundary conditions and unusual N values

#### TC1.1: N=8 Quick Mode
```bash
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 8 --tag test_n8_quick
```

**Why Test**: Beyond analyzed range (N=3-7); tests if infrastructure handles arbitrary N

**Expected**:
- Unknown cycle landscape (no prior data)
- Likely continued decline in basin mass
- Possible continued HALT rate increase

**Validate**:
- [ ] Completes without index errors
- [ ] Cycles identified and analyzed
- [ ] Results logged for comparison

---

#### TC1.2: N=10 Quick Mode
```bash
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 10 --tag test_n10_quick
```

**Why Test**: Round number, nice endpoint for phase curve

**Expected**:
- High fragmentation
- Many small basins vs few large ones
- Low coverage

**Validate**:
- [ ] Harness handles high fragmentation gracefully
- [ ] Sampling finds enough cycles to analyze

---

#### TC1.3: N=2 Quick Mode (Edge Case)
```bash
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 2 --tag test_n2_quick
```

**Why Test**: Minimum interesting N (N=1 is trivial - always self-loops)

**Expected**:
- Very shallow basins
- Fast convergence
- High coverage (most pages have ≥2 links)

**Validate**:
- [ ] No array indexing errors (second link exists)
- [ ] Results make semantic sense

---

### Tier 2: Cross-N Comparison (Priority: HIGH)

**Goal**: Validate scripts that compare results across multiple N values

**Prerequisites**: TC0.1-TC0.4 completed (N=3,4,5,6,7 data exists)

#### TC2.1: Compare Cycle Evolution
```bash
python n-link-analysis/scripts/compare-cycle-evolution.py \
  --n-values 3 4 5 6 7 \
  --tag multi_n_test_2026-01-01
```

**Expected**:
- Identifies which cycles appear at multiple N values
- Shows basin size evolution for each cycle
- Generates visualization showing cycle trajectories

**Validate**:
- [ ] Script runs without errors
- [ ] Output files created: `cycle_evolution_*.tsv`, `*.png`
- [ ] Visualizations show expected N=5 peak for some cycles
- [ ] Universal cycles identified (appear at 3+ N values)

---

#### TC2.2: Mechanism Comparison Across N
```bash
python n-link-analysis/scripts/visualize-mechanism-comparison.py \
  --n-values 3 4 5 6 7 \
  --tag multi_n_test_2026-01-01
```

**Expected**:
- Updates mechanism comparison charts with new N values
- Shows convergence depth, HALT rate, path length across N
- Validates odd-even pattern hypothesis

**Validate**:
- [ ] Charts generated successfully
- [ ] N=5 peak visible in basin mass chart
- [ ] HALT rate increases N=6,7 confirmed
- [ ] Convergence depth oscillation visible

---

### Tier 3: Reproducibility Testing (Priority: MEDIUM)

**Goal**: Ensure deterministic outputs for identical inputs

#### TC3.1: Repeated N=5 Run
```bash
# Run 1
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 5 --tag repro_test_1

# Run 2 (same parameters)
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 5 --tag repro_test_2
```

**Validate**:
- [ ] Compare basin_n=5_cycle=Massachusetts_*.tsv files (should be identical)
- [ ] Compare trunkiness_dashboard files (should be identical)
- [ ] Check random seed handling in scripts that use randomness

**Known Variability**:
- Random sampling (sample-nlink-traces.py) - uses seed, should be deterministic
- Visualization timestamps - acceptable difference

---

### Tier 4: Error Handling (Priority: MEDIUM)

**Goal**: Verify graceful degradation when things go wrong

#### TC4.1: Missing Dependency
```bash
# Temporarily move links_resolved.parquet
mv data/wikipedia/processed/links_resolved.parquet data/wikipedia/processed/links_resolved.parquet.backup

# Run harness
python n-link-analysis/scripts/run-analysis-harness.py --quick --n 5 --tag error_test_missing_dep

# Restore
mv data/wikipedia/processed/links_resolved.parquet.backup data/wikipedia/processed/links_resolved.parquet
```

**Expected**:
- validate-data-dependencies.py catches missing file
- Harness exits early with clear error message
- No partial outputs created

**Validate**:
- [ ] Error message is clear and actionable
- [ ] Harness doesn't continue with incomplete data
- [ ] No corrupted output files

---

#### TC4.2: Script Failure Mid-Pipeline
```bash
# Modify a script to intentionally fail (e.g., syntax error)
# Run harness and observe behavior
```

**Expected**:
- Harness catches script failure (non-zero exit code)
- Logs which script failed
- Stops pipeline execution

**Validate**:
- [ ] Failure is logged clearly
- [ ] Subsequent scripts don't run
- [ ] User can identify where to fix issue

---

### Tier 5: Performance Profiling (Priority: LOW)

**Goal**: Understand resource requirements for production runs

#### TC5.1: Runtime Scaling
```bash
# Measure runtime for different N values
time python n-link-analysis/scripts/run-analysis-harness.py --quick --n 3 --tag perf_n3
time python n-link-analysis/scripts/run-analysis-harness.py --quick --n 5 --tag perf_n5
time python n-link-analysis/scripts/run-analysis-harness.py --quick --n 7 --tag perf_n7
```

**Collect**:
- Total runtime
- Per-script runtime (check harness logs)
- Memory usage (use `time -v` on Linux)

**Validate**:
- [ ] Runtime correlates with basin size (N=5 likely slowest)
- [ ] No memory leaks (memory usage stable across scripts)
- [ ] Disk space usage reasonable (<50GB for all N=3-10)

---

#### TC5.2: Full Mode Performance
```bash
# Run full mode (9 cycles, full samples) for N=5
time python n-link-analysis/scripts/run-analysis-harness.py --n 5 --tag perf_full
```

**Expected**:
- ~2-4 hours runtime (vs ~30-60 min quick mode)
- 3x more samples, 1.5x more cycles

**Validate**:
- [ ] Runtime prediction accurate
- [ ] No timeout issues
- [ ] Output quality improvement worth the time

---

## Execution Strategy

### Phase 1: Core Validation (Week 1)
**Goal**: Validate N=3,4,6,7 work correctly

**Order**:
1. TC0.1 (N=3) - Easiest, smallest basins
2. TC0.2 (N=4) - Fast convergence
3. TC0.3 (N=6) - Test fragmentation
4. TC0.4 (N=7) - Test deep basins
5. TC2.1 (Cross-N evolution) - Validate comparison works

**Deliverable**: Confidence that harness works for N≠5

---

### Phase 2: Edge Cases & Extensions (Week 2)
**Goal**: Test boundary conditions and extended range

**Order**:
1. TC1.1 (N=8) - Beyond analyzed range
2. TC1.2 (N=10) - Complete decade
3. TC1.3 (N=2) - Lower bound
4. TC2.2 (Mechanism comparison) - Full visualization suite

**Deliverable**: Complete N=2-10 coverage validated

---

### Phase 3: Quality Assurance (Week 3)
**Goal**: Ensure reliability and reproducibility

**Order**:
1. TC3.1 (Reproducibility) - Determinism check
2. TC4.1 (Missing deps) - Error handling
3. TC4.2 (Script failure) - Recovery testing
4. TC5.1 (Performance) - Resource profiling

**Deliverable**: Production-ready framework

---

## Success Metrics

### Must-Have (Blocker if failing)
- ✓ Harness completes for N∈{3,4,5,6,7}
- ✓ Cross-N comparison scripts work
- ✓ No silent failures (errors caught and reported)
- ✓ Outputs validated against known results (N=5)

### Should-Have (Important but not blocking)
- ✓ N∈{2,8,9,10} also work
- ✓ Reproducibility within 1% (accounting for float rounding)
- ✓ Performance acceptable (<2 hours per N in quick mode)
- ✓ Error messages actionable

### Nice-to-Have (Enhancements)
- Parallel execution of independent N values
- Progress bars for long-running scripts
- Automated comparison of outputs across runs
- Performance dashboard showing runtime per script

---

## Contingency Plans

### If N=3,4,6,7 Fail
**Likely Cause**: Indexing assumptions (e.g., hardcoded N=5 somewhere)

**Action**:
1. Review error logs to identify failing script
2. Check for hardcoded constants vs parameterized N
3. Fix and re-run
4. Add test to prevent regression

---

### If Cross-N Comparison Fails
**Likely Cause**: File naming conventions, missing data

**Action**:
1. Check file paths in comparison scripts
2. Verify all required N values have been run
3. Update scripts to handle missing N gracefully

---

### If Performance Unacceptable (>6 hours per N)
**Likely Cause**: Giant basins (Massachusetts-scale at different N)

**Action**:
1. Profile to find bottleneck scripts
2. Implement early stopping (max-nodes limits)
3. Consider parallelization within basin mapping
4. Document expected runtimes in HARNESS-README.md

---

## Documentation Updates Needed

After testing completes:

1. **HARNESS-README.md**:
   - Add tested N values section
   - Update runtime estimates for different N
   - Add troubleshooting section for common errors

2. **scripts-reference.md**:
   - Mark which scripts are N-agnostic
   - Document which scripts have N-specific behavior
   - Add performance notes (script X slow for N>7)

3. **NEXT-STEPS.md**:
   - Update Tier 1.1 status (Multi-N validated)
   - Move to Tier 1.2 (Hub connectivity) or Tier 2 (Theory validation)

4. **session-log.md**:
   - Record testing findings
   - Document any bugs discovered and fixed
   - Note performance characteristics

---

## Open Questions

1. **Cycle Stability**: Do the same cycles appear at different N values?
   - Massachusetts at N=3,4,5,6,7?
   - Or completely different cycles at each N?

2. **Basin Size Scaling**: Does Massachusetts stay the largest basin at all N?
   - Or does dominance shift (e.g., Sea_salt becomes #1 at N=7)?

3. **Depth Pattern Evolution**: How do basin shapes change?
   - Does Thermosetting_polymer stay deep at N≠5?
   - Does Kingdom stay tree-like?

4. **Optimal N**: Is N=5 truly the peak, or is there N=8 or N=10 peak?
   - Coverage vs Basin Mass tradeoff curve

5. **Fragmentation Threshold**: At what N does the graph fragment completely?
   - N=15? N=20? Never?

---

## Next Actions

**Immediate** (This Session):
1. Review this plan with user
2. Get approval to proceed with Phase 1
3. Schedule testing runs (can run overnight)

**Short-Term** (Next Session):
1. Execute TC0.1 (N=3 quick mode)
2. Analyze results, compare to N=5
3. Document findings in session-log.md

**Medium-Term** (Next Week):
1. Complete Phase 1 (N=3,4,6,7 validated)
2. Run cross-N comparison
3. Generate phase transition curve visualization

---

**END OF TESTING PLAN**
