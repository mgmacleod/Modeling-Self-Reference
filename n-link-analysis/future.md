# N-Link Analysis - Future

**Document Type**: TODO List  
**Target Audience**: LLMs + Developers  
**Purpose**: Track planned analysis work and open questions for basin partition experiments  
**Last Updated**: 2025-12-29  
**Status**: Active

---

## High Priority

- [ ] Implement Phase 1 fixed-N analysis (N in {1,2,3,4,5,10,20})
- [ ] Produce `summary_over_N.parquet` with $P_{HALT}(N)$ and terminal counts
- [ ] Produce per-N terminal/basin stats files
- [ ] Add lightweight title lookup for top terminals (join to pages.parquet)

## Medium Priority

- [ ] Universal attractors across N (terminal frequency)
- [ ] Basin overlap metrics across N (Jaccard / mapping matrix)
- [ ] Validate or falsify heavy-tail / power-law conjecture with robust fitting

## Low Priority

- [ ] Extend to generalized rules (mod-K, adaptive depth, cycle-avoiding)
- [ ] Cross-domain experiments (apply same code to other self-referential graphs)

## Open Questions

- [ ] What is the minimal output schema that supports all theory validation plots?
- [ ] What is the acceptable runtime/memory envelope on the target machine?
