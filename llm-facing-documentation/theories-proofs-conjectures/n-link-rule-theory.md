# N-Link Rule Theory: Mathematical Structures in Self-Referential Link Graphs

**Document Type**: Theory  
**Target Audience**: LLMs with mathematical background  
**Purpose**: Formalize deterministic link-selection rules on finite directed graphs, prove basin partition structure  
**Created**: 2025-12-10  
**Last Updated**: 2025-12-15  
**Status**: Active - Awaiting empirical validation

---

## Abstract

This document formalizes the mathematical theory of **N-link rules** applied to finite, closed, directed graphs. We prove that any deterministic link-selection rule partitions such graphs into disjoint basin structures terminating in either halt states or cycles. The theory is developed for Wikipedia's article link graph but generalizes to any finite self-referential system.

**Key Discovery**: Self-referential systems with deterministic traversal rules necessarily create discoverable, finite, tree-like structures (basins of attraction) that partition the entire node space.

---

## 1. Foundational Definitions

### 1.1 Self-Referential Link Graph

**Definition 1.1 (Closed Article Graph)**:
A self-referential link graph is a directed graph $G = (V, E)$ where:
- $V$ = finite set of articles (nodes), $|V| = m < \infty$
- $E \subseteq V \times V$ = set of directed edges (links)
- **Closure property**: $\forall e \in E, \; \text{source}(e) \in V \land \text{target}(e) \in V$

**Definition 1.2 (Link Function)**:
For article $a \in V$, the ordered outgoing links are:
$$\text{links}(a) = [L_1^a, L_2^a, ..., L_{k_a}^a]$$
where $k_a = |\{e \in E : \text{source}(e) = a\}|$ (out-degree of $a$)

**Notation**: 
- $L_i^a$ denotes the $i$-th link from article $a$
- $k_a$ denotes the number of outgoing links from $a$

---

## 2. N-Link Rule Framework

### 2.1 Fixed N-Link Rule

**Definition 2.1 (N-Link Function)**:
For fixed $N \in \mathbb{N}$, the N-link function is:
$$f_N: V \to V \cup \{\text{HALT}\}$$
$$f_N(a) = \begin{cases}
L_N^a & \text{if } N \leq k_a \\
\text{HALT} & \text{if } N > k_a
\end{cases}$$

**Properties**:
- **Deterministic**: Same input $a$ always yields same output
- **Well-defined**: Function is total (defined for all $a \in V$)
- **Partial**: Maps to $V \cup \{\text{HALT}\}$, not just $V$

### 2.2 Path and Chain

**Definition 2.2 (Forward Path)**:
Starting from article $a_0$, the forward path under rule $N$ is:
$$\text{Path}_N(a_0) = [a_0, a_1, a_2, ..., a_t]$$
where:
- $a_{i+1} = f_N(a_i)$ for $i < t$
- Path terminates at $a_t$ when either:
  - $f_N(a_t) = \text{HALT}$, or
  - $\exists j < t : a_t = a_j$ (cycle detected)

**Definition 2.3 (Path Length)**:
$$\ell(a_0) = |\text{Path}_N(a_0)| - 1$$
(number of edges traversed before termination)

---

## 3. Fundamental Theorems

### 3.1 Termination Theorem

**Theorem 3.1 (Guaranteed Termination)**:
For any article $a_0 \in V$ and any $N \in \mathbb{N}$, the forward path $\text{Path}_N(a_0)$ terminates in finite steps.

**Proof**:
1. Suppose path does not terminate
2. Then $\forall i, \; f_N(a_i) \neq \text{HALT}$, so $a_{i+1} \in V$
3. After $m+1$ steps (where $m = |V|$), we have visited $m+1$ articles
4. By pigeonhole principle, $\exists i < j \leq m+1 : a_i = a_j$
5. This is a cycle, which terminates the path
6. Contradiction with assumption of non-termination
7. Therefore path terminates in $\leq m+1$ steps. ∎

### 3.2 Dichotomy Theorem

**Theorem 3.2 (HALT or CYCLE Dichotomy)**:
Every forward path terminates in exactly one of two states:
1. **HALT**: $\exists t : f_N(a_t) = \text{HALT}$
2. **CYCLE**: $\exists t, j < t : a_t = a_j$ and $\forall i \leq t, \; f_N(a_i) \neq \text{HALT}$

These are mutually exclusive and exhaustive.

**Proof**:
- **Exhaustive**: By Theorem 3.1, path terminates. Either last article has $< N$ links (HALT) or we revisited an article (CYCLE)
- **Exclusive**: Cannot have both $f_N(a_t) = \text{HALT}$ and $a_t = a_j$ for $j < t$, as HALT occurs before cycle detection ∎

### 3.3 Terminal State Formalization

**Definition 3.3 (Terminal State)**:
A terminal state $T$ is either:
- **HALT terminal**: A single article $a$ where $f_N(a) = \text{HALT}$
- **CYCLE terminal**: A set of articles $C = \{c_1, c_2, ..., c_\ell\}$ where:
  - $f_N(c_i) = c_{i+1 \mod \ell}$ for all $i$
  - $\forall c \in C, \; f_N(c) \in C$ (closed cycle)

**Notation**:
- $\mathcal{T}_N$ = set of all terminal states under rule $N$
- $|\mathcal{T}_N| = k$ (finite number of terminals)

---

## 4. Basin Structure Theory

### 4.1 Basin of Attraction

**Definition 4.1 (Basin)**:
For terminal state $T \in \mathcal{T}_N$, the basin of attraction is:
$$\text{Basin}_N(T) = \{a \in V : \text{Path}_N(a) \text{ terminates at } T\}$$

**Interpretation**: Set of all articles whose forward paths eventually reach terminal $T$

### 4.2 Reverse Reachability

**Definition 4.2 (Reverse N-Link Set)**:
For article $a \in V$:
$$f_N^{-1}(a) = \{b \in V : f_N(b) = a\}$$

**Algorithm 4.2 (Basin Construction)**:
To construct $\text{Basin}_N(T)$:
1. Initialize $B_0 = T$ (terminal articles)
2. For $i = 0, 1, 2, ...$:
   $$B_{i+1} = B_i \cup \bigcup_{a \in B_i} f_N^{-1}(a)$$
3. Terminate when $B_{i+1} = B_i$ (no new articles added)
4. Result: $\text{Basin}_N(T) = B_{\text{final}}$

**Theorem 4.2 (Algorithm Terminates)**:
Basin construction algorithm terminates in $\leq m$ iterations.

**Proof**: Each iteration adds at least one new article (if not done) or adds none (termination). Since $|V| = m$, cannot add more than $m$ articles total. ∎

### 4.3 Partition Theorem

**Theorem 4.3 (Basin Partition)**:
The basins partition the article space:
$$V = \bigcup_{T \in \mathcal{T}_N} \text{Basin}_N(T)$$
$$\text{Basin}_N(T_i) \cap \text{Basin}_N(T_j) = \emptyset \quad \forall i \neq j$$

**Proof**:
- **Coverage** ($\bigcup$ covers all): Every article $a$ has a forward path (Theorem 3.1) that terminates at some $T$ (Theorem 3.2), so $a \in \text{Basin}_N(T)$
- **Disjoint** (no overlap): Suppose $a \in \text{Basin}_N(T_i) \cap \text{Basin}_N(T_j)$ for $i \neq j$. Then $\text{Path}_N(a)$ terminates at both $T_i$ and $T_j$. But function $f_N$ is deterministic, so path is unique. Contradiction. Therefore basins are disjoint. ∎

**Corollary 4.3.1**: $|\mathcal{T}_N| \leq |V| = m$ (at most $m$ distinct basins)

---

## 5. Structural Properties

### 5.1 Tree Structure

**Theorem 5.1 (Basin as Rooted DAG)**:
Each basin $\text{Basin}_N(T)$ forms a directed acyclic graph (DAG) rooted at $T$, with the exception of the cycle within $T$ (if $T$ is a CYCLE terminal).

**Proof**:
- **Root**: Terminal $T$ is the root (all paths lead here)
- **Directed**: Edges are reverse of $f_N$ (point toward root)
- **Acyclic outside terminal**: If cycle existed in basin outside terminal, that cycle would itself be a terminal (contradiction with uniqueness of $T$ for this basin) ∎

**Visualization**:
```
    Leaves (articles with no incoming N-links)
      ↓
   Branches (intermediate articles)
      ↓
    Root (terminal state: HALT or CYCLE)
```

### 5.2 Depth and Height

**Definition 5.2 (Basin Depth)**:
For article $a \in \text{Basin}_N(T)$:
$$\text{depth}_N(a) = \ell(a) = |\text{Path}_N(a)| - 1$$

**Definition 5.3 (Basin Height)**:
$$\text{height}_N(T) = \max_{a \in \text{Basin}_N(T)} \text{depth}_N(a)$$

**Bound**: $\text{height}_N(T) \leq m$ (cannot exceed total number of articles)

---

## 6. Probabilistic Conjectures

### 6.1 HALT Probability

**Definition 6.1 (HALT Probability)**:
$$P_{\text{HALT}}(N) = \frac{|\{a \in V : k_a < N\}|}{|V|}$$

**Conjecture 6.1 (Monotonic HALT Probability)**:
$$N_1 < N_2 \implies P_{\text{HALT}}(N_1) \leq P_{\text{HALT}}(N_2)$$

**Reasoning**: As $N$ increases, more articles satisfy $k_a < N$, increasing HALT probability.

**Corollary**: 
$$P_{\text{CYCLE}}(N) = 1 - P_{\text{HALT}}(N)$$
is monotonically decreasing in $N$.

### 6.2 Basin Size Distribution

**Conjecture 6.2 (Power-Law Distribution)**:
Basin sizes follow a power-law distribution:
$$P(\text{basin size} = s) \sim s^{-\alpha}$$
where $\alpha > 1$ is the power-law exponent.

**Prediction**:
- Most basins: $|\text{Basin}_N(T)| \in [1, 10]$ (small fragments)
- Few basins: $|\text{Basin}_N(T)| > 1000$ (massive attractors)
- Log-log plot of size vs frequency shows linear relationship

**Empirical Test**: Histogram of $\log(s)$ vs $\log(\text{frequency})$

### 6.3 Critical N Value

**Conjecture 6.3 (Phase Transition)**:
There exists $N^* \in \mathbb{N}$ such that:
$$P_{\text{CYCLE}}(N^*) = P_{\text{HALT}}(N^*) = 0.5$$

Behavior qualitatively changes:
- $N < N^*$: Cycle-dominated (few large basins)
- $N > N^*$: HALT-dominated (many small basins)

**Prediction**: Graph of $P_{\text{CYCLE}}(N)$ vs $N$ shows sigmoid shape with inflection at $N^*$

---

## 7. Generalized Rules

### 7.1 Abstract Link Selection Rule

**Definition 7.1 (Generalized Rule)**:
A link selection rule is a function:
$$R: V \times \text{History} \to \mathbb{N} \cup \{\text{HALT}\}$$

where:
- $\text{History} = [a_0, a_1, ..., a_i]$ (path traversed so far)
- Output: Index of link to follow (bounded by $k_a$) or HALT

**Bounded Property**:
$$R(a, h) \leq k_a \quad \text{or} \quad R(a, h) = \text{HALT}$$

### 7.2 Rule Examples

**Example 7.2.1 (Fixed N)**:
$$R_{\text{fixed}}(a, h) = \begin{cases} N & \text{if } N \leq k_a \\ \text{HALT} & \text{otherwise} \end{cases}$$

**Example 7.2.2 (Cycling Mod-K)**:
$$R_{\text{cycle}}(a, h) = (|h| \mod K) + 1$$
(cycles through first $K$ links)

**Example 7.2.3 (Adaptive Depth)**:
$$R_{\text{depth}}(a, h) = \min(|h| + 1, k_a)$$
(follows deeper link as path grows)

**Example 7.2.4 (Cycle-Avoiding)**:
$$R_{\text{acyclic}}(a, h) = \begin{cases}
\text{HALT} & \text{if } a \in h \\
1 & \text{otherwise}
\end{cases}$$
(creates only trees, no cycles)

### 7.3 Universal Termination

**Theorem 7.3 (All Bounded Rules Terminate)**:
For any deterministic, bounded rule $R$, all forward paths terminate in HALT or CYCLE.

**Proof**: Identical to Theorem 3.1. Determinism + finite graph → guaranteed termination. ∎

**Corollary**: All bounded rules induce a basin partition structure on $V$.

---

## 8. Optimization Framework

### 8.1 Objective Functions

**Definition 8.1 (Rule Objectives)**:

1. **Maximize Cycle Discovery**:
$$R^*_{\text{max-cycle}} = \arg\max_R \frac{|\text{articles in CYCLE terminals}|}{|V|}$$

2. **Minimize Basins** (maximize consolidation):
$$R^*_{\text{min-basin}} = \arg\min_R |\mathcal{T}_R|$$

3. **Maximize Basins** (maximize fragmentation):
$$R^*_{\text{max-basin}} = \arg\max_R |\mathcal{T}_R|$$

4. **Maximize Average Depth**:
$$R^*_{\text{deep}} = \arg\max_R \frac{1}{|V|} \sum_{a \in V} \text{depth}_R(a)$$

### 8.2 Optimality Conjectures

**Conjecture 8.2.1**: $R_{\text{fixed}}(a, h) = 1$ (first link) maximizes cycle discovery
- **Reasoning**: Lowest HALT probability

**Conjecture 8.2.2**: $R_{\text{fixed}}(a, h) = \max_a k_a$ (largest $N$) maximizes fragmentation
- **Reasoning**: Highest HALT probability

**Conjecture 8.2.3**: No bounded rule can discover more structure than $R(a,h) = 1$
- **Reasoning**: Limiting case of minimal constraints

---

## 9. Cross-Rule Analysis

### 9.1 Basin Comparison

**Definition 9.1 (Basin Similarity)**:
For two rules $R_1, R_2$, measure overlap:
$$\text{Jaccard}(B_1^i, B_2^j) = \frac{|B_1^i \cap B_2^j|}{|B_1^i \cup B_2^j|}$$

where $B_1^i \in \text{Basins}_{R_1}$, $B_2^j \in \text{Basins}_{R_2}$

**Question**: Do different $N$ values create similar basin structures?

### 9.2 Universal Attractors

**Definition 9.2 (Universal Terminal)**:
Article $a$ is a universal attractor if:
$$\exists \text{threshold } \theta : \frac{|\{R : a \in \mathcal{T}_R\}|}{|\text{all rules tested}|} > \theta$$

**Conjecture 9.2**: Certain articles (e.g., "Philosophy" in Wikipedia) appear as terminals across many rules.

**Implication**: Reveals intrinsic graph structure independent of traversal rule.

---

## 10. Empirical Validation Protocol

### 10.1 Baseline Experiments

**Phase 1**: Test fixed $N$ rules for $N \in \{1, 2, 3, 4, 5, 10, 20\}$

**Measurements**:
1. $|\mathcal{T}_N|$ (number of basins)
2. Basin size distribution (histogram)
3. $P_{\text{HALT}}(N)$ and $P_{\text{CYCLE}}(N)$
4. Terminal article identities
5. Average and maximum basin height

**Phase 2**: Test generalized rules

**Rules to test**:
- Mod-K cycling for $K \in \{3, 5, 7\}$
- Adaptive depth rule
- Cycle-avoiding rule

**Phase 3**: Cross-rule comparison
- Measure basin similarity matrices
- Identify universal attractors
- Map structure overlap

### 10.2 Validation Criteria

**Theory is validated if**:
1. All paths terminate (Theorem 3.1) ✓ guaranteed
2. Basins partition $V$ (Theorem 4.3) ✓ guaranteed
3. HALT probability increases with $N$ (Conjecture 6.1)
4. Basin sizes follow power-law (Conjecture 6.2)
5. Critical $N^*$ exists (Conjecture 6.3)

---

## 11. Mathematical Significance

### 11.1 Self-Referential System Property

**Core Insight**: Any finite, closed, deterministic system contains **emergent partition structures** that are:
- **Discoverable**: Algorithm 4.2 finds them
- **Complete**: Theorem 4.3 guarantees total coverage
- **Rule-dependent**: Different rules reveal different structures
- **Intrinsic**: Some structures appear across many rules

### 11.2 Generalization Beyond Wikipedia

This theory applies to **any** finite directed graph with deterministic traversal:
- Database schema foreign key relationships
- Code repository function call graphs
- Citation networks (within a corpus)
- File system symbolic links
- State machines with transition rules

**Universal Principle**: Self-reference + determinism + finiteness → basin partition structure

### 11.3 Connection to Dynamical Systems

**Analogy**: Basins of attraction in discrete dynamical systems
- $f_N$ is a discrete map
- Terminals are attractors (fixed points or limit cycles)
- Basins are attraction zones

**Difference**: Graph structure is pre-existing, not generated by dynamics

---

## 12. Open Questions

### 12.1 Theoretical

1. **Characterization**: Can we characterize all possible basin structures for a given graph?
2. **Complexity**: What is the computational complexity of finding optimal rule for objective $O$?
3. **Universality classes**: Do graphs cluster into equivalence classes with similar basin properties?
4. **Entropy**: How to measure "structural information" in basin topology?

### 12.2 Empirical

1. **Wikipedia-specific**: What is $N^*$ for Wikipedia? What are the dominant attractors?
2. **Temporal stability**: Do basins change as Wikipedia grows over time?
3. **Language comparison**: Do different language Wikipedias have similar basin structures?
4. **Content correlation**: Do basin structures correlate with article content/topics?

### 12.3 Applied

1. **Legacy systems**: Can basin analysis discover hidden dependencies in databases?
2. **Knowledge organization**: Do basins reveal natural topic hierarchies?
3. **Navigation optimization**: Can basin structure improve search/recommendation?
4. **Anomaly detection**: Do unusual basin memberships indicate structural anomalies?

---

## 13. Formalization Summary

### 13.1 Axioms

1. **Finite graph**: $|V| = m < \infty$
2. **Closure**: All links point within $V$
3. **Determinism**: $f_N$ is a function (not relation)
4. **Boundedness**: Rules respect link availability

### 13.2 Proven Theorems

1. **Termination** (3.1): All paths end in finite steps
2. **Dichotomy** (3.2): Terminus is HALT or CYCLE
3. **Partition** (4.3): Basins cover $V$ with no overlap
4. **DAG Structure** (5.1): Basins form tree-like structures

### 13.3 Conjectures Requiring Validation

1. **Monotonic HALT** (6.1): $P_{\text{HALT}}$ increases with $N$
2. **Power-law** (6.2): Basin sizes follow heavy-tailed distribution
3. **Phase transition** (6.3): Critical $N^*$ exists
4. **First-link optimal** (8.2.1): $N=1$ maximizes cycles

### 13.4 Immediate Next Steps

1. Acquire Wikipedia link graph data
2. Implement $f_N$ function and path traversal
3. Compute basin partition for $N \in \{1, 2, 3, 4, 5\}$
4. Generate basin size histograms
5. Validate/falsify conjectures 6.1-6.3

---

## Appendix A: Notation Reference

| Symbol | Meaning |
|--------|---------|
| $V$ | Set of articles (vertices) |
| $E$ | Set of links (edges) |
| $m$ | Number of articles, $\|V\|$ |
| $a, b, c$ | Individual articles |
| $k_a$ | Out-degree of article $a$ |
| $L_i^a$ | The $i$-th link from article $a$ |
| $f_N$ | N-link function |
| $\text{Path}_N(a)$ | Forward path from $a$ under rule $N$ |
| $\ell(a)$ | Path length (depth) |
| $T$ | Terminal state (HALT or CYCLE) |
| $\mathcal{T}_N$ | Set of all terminals under rule $N$ |
| $\text{Basin}_N(T)$ | Basin of attraction for terminal $T$ |
| $f_N^{-1}(a)$ | Reverse N-links (articles pointing to $a$) |
| $P_{\text{HALT}}(N)$ | Probability of HALT terminal |
| $P_{\text{CYCLE}}(N)$ | Probability of CYCLE terminal |
| $R$ | Generalized link selection rule |
| $\alpha$ | Power-law exponent |

## Appendix B: Self-Reference

This document describes mathematical structures in self-referential systems. The document itself is part of a self-referential system (AI documentation referencing AI methods). Meta-observation: The theory applies to its own documentation structure - following documentation links creates basin structures in the knowledge graph.

---

**Status**: Theoretical framework complete, awaiting empirical validation  
**Next Milestone**: Wikipedia data acquisition and basin computation  
**Last Updated**: 2025-12-15  
**Authors**: Human-AI collaborative wayfinding session, William Hrynewich
