# N-Link Analysis - Future

**Document Type**: TODO List  
**Target Audience**: LLMs + Developers  
**Purpose**: Track planned analysis work and open questions for basin partition experiments  
**Last Updated**: 2025-12-31
**Status**: Active

---

## High Priority

- [x] Implement Phase 1 fixed-N analysis (N∈{3,4,5,6,7} complete)
- [x] Produce per-N terminal/basin stats files (complete for N∈{3,4,5,6,7})
- [x] Add lightweight title lookup for top terminals (implemented in reproduction script)
- [x] Map finer N resolution (N∈{4,6}) to characterize phase transition curve - **DONE** 2025-12-31
- [x] Link degree distribution analysis to correlate with basin mass peaks - **DONE** 2025-12-31
- [x] Path characteristics analysis (convergence, HALT, branching) - **DONE** 2025-12-31
- [x] Cycle evolution tracking across N - **DONE** 2025-12-31
- [ ] Entry breadth analysis (count unique depth=1 nodes per basin)
- [ ] Produce `summary_over_N.parquet` with $P_{HALT}(N)$ and terminal counts across wider N range
- [ ] Map N∈{8,9,10} to complete HALT saturation curve

## Medium Priority

- [x] Universal attractors across N (terminal frequency) - Same 6 cycles found across N∈{3,4,5,6,7}
- [x] Validate heavy-tail / power-law conjecture - Confirmed for N=5 (67% high-trunk basins)
- [ ] Basin overlap metrics across N (Jaccard / mapping matrix)
- [ ] Percolation model development (predict basin mass from degree distribution + N)
- [ ] Test on other graphs (different language Wikipedias, citation networks)

## Low Priority

- [ ] Extend to generalized rules (mod-K, adaptive depth, cycle-avoiding)
- [ ] Cross-domain experiments (apply same code to other self-referential graphs)

## Open Questions

- [ ] What is the minimal output schema that supports all theory validation plots?
- [ ] What is the acceptable runtime/memory envelope on the target machine?
