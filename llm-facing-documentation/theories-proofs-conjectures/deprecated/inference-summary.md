# LLM-Facing Summary of Formal Theorems, Proofs, and Conjectures

**DEPRECATED**: This document has been superseded by [unified-inference-theory.md](../unified-inference-theory.md)  
**Date Deprecated**: 2025-12-15  
**Reason**: Merged with inference-summary-with-event-tunneling.md for consolidated theory reference  
**Location**: Moved to deprecated/ subdirectory to reduce context pollution

---

## 1. System Context

This document summarizes the formal structures, theorems, proofs, and conjectures arising from the conversation regarding:

- N-Link Rule Theory on finite self-referential graphs  
- Database Inference Graph Theory  
- Local Inference Enumeration and Operator Gating  
- Deterministic traversal partitions and multi-rule tunneling

It is explicitly designed as an **LLM-facing context document**.  
Assume the reader already understands abstract graph theory, deterministic maps, functional graphs, and relational database semantics.

---

## 2. N-Link Deterministic Traversal Theory

### 2.1 Definitions

**Finite Directed Graph**  
A closed directed graph \( G = (V, E) \) with \( |V| < \infty \).

**Outgoing Link Ordering**  
For each node \( a \in V \), outgoing edges are ordered:  
\[
	ext{links}(a) = [L_1^a, L_2^a, \dots, L_{k_a}^a].
\]

**N-Link Function**  
For fixed \( N \in \mathbb{N} \):  
\[
f_N(a) = 
egin{cases}
L_N^a & N \le k_a \\
	ext{HALT} & N > k_a.
\end{cases}
\]

**Forward Path** under \( f_N \):  
Sequence \( [a_0, a_1, \dots] \) where \( a_{i+1} = f_N(a_i) \) until HALT or cycle.

---

### 2.2 Theorem: Guaranteed Termination

**Theorem 1**  
Every forward path under \( f_N \) terminates in finite time.

**Proof Sketch**  
- If no HALT occurs, all nodes remain in \( V \).  
- After \( |V| + 1 \) steps, pigeonhole principle ⇒ repeat.  
- Repetition ⇒ cycle ⇒ termination.

---

### 2.3 Theorem: HALT/CYCLE Dichotomy

**Theorem 2**  
Every node’s forward path ends exactly in:

1. **HALT**, if \( f_N(a_t) = 	ext{HALT} \);  
2. **CYCLE**, if \( a_t = a_j \) for some \( j < t \).

Mutually exclusive, exhaustive.

---

### 2.4 Terminal States and Basins

**Terminal State**  
Either a HALT node or a directed cycle \( C \subseteq V \).

**Basin of Attraction**  
\[
	ext{Basin}_N(T) = \{ a \in V : 	ext{Path}_N(a) 	ext{ terminates at } T \}.
\]

**Theorem 3 (Partition Theorem)**  
The basins \( \{ 	ext{Basin}_N(T) \} \) form a **disjoint partition** of \( V \).

**Proof Sketch**  
- Deterministic map ⇒ each node has unique terminal.  
- Coverage follows from Theorem 1.

---

### 2.5 DAG Structure

**Theorem 4**  
Reverse edges restricted to a basin form a directed acyclic graph rooted at the terminal (except the cycle itself).

---

### 2.6 Conjectures

1. **HALT Probability Monotonicity**  
   \[
   N_1 < N_2 \implies P_{	ext{HALT}}(N_1) \le P_{	ext{HALT}}(N_2).
   \]

2. **Basin Size Power Law**  
   \( P(	ext{basin size} = s) \sim s^{-lpha} \).

3. **Critical N (Phase Transition)**  
   Exists \( N^* \) such that  
   \( P_{	ext{CYCLE}}(N^*) = P_{	ext{HALT}}(N^*) = 0.5 \).

---

## 3. Database Inference Graph Theory

### 3.1 Generalization of N-Link Rules

Database graphs consist of:

- Tables \(T\)  
- Columns \(C\)  
- Typed relationships \(R\)  
- Inference rules \( \mathcal{I} \)

A deterministic inference step is analogous to selecting the next node via \( N \), but rule-dependent rather than position-dependent.

---

### 3.2 Theorem: Rule-Induced Basin Partitioning

For any deterministic inference rule \( I \):

\[
orall I \in \mathcal{I}, \quad 	ext{Basins}_I 	ext{ partition the schema graph }.
\]

**Proof Sketch**  
Identical to N-Link termination and partition arguments; determinism + finiteness ⇒ HALT/CYCLE.

---

### 3.3 Multi-Rule Tunneling

If \( I_1 \) and \( I_2 \) are different deterministic rules, their basin partitions differ.  
Nodes reachable by both are **tunnel nodes**.

**Conjecture**  
Tunnel structure across rules encodes the true semantic structure of the database (cross-rule invariants reveal core entities).

---

## 4. Local Inference Enumeration & Operator Gating

### 4.1 Key Insight

At any anchor \( c \), the possible inferences are:

- finite,  
- deterministic,  
- relationship-dependent,  
- expressible as a finite set of inference operators.

Multiplicity-based inferences require multiplicity in relationship cardinality.

---

### 4.2 Relationship Types

- 1:1  
- 1:M  
- M:1  
- M:M  

Multiplicity-based operators (counts, sums, ratios) are **degenerate** in 1:1 and on the “1 side” of M:1.

---

### 4.3 Operators

| Operator | Preconditions | Notes |
|----------|---------------|-------|
| Coverage | always valid | informative regardless of type |
| Count-per-parent | 1:M or M:M | degenerate (0/1) in 1:1 |
| Child distribution | 1:M or M:M | same gating |
| Aggregates (sum/avg) | multiplicity + numeric field | collapses for 1:1 |
| Ratios/densities | multiplicity required | meaningless for strict 1:1 |

**Theorem (Operator Gating)**  
Given a strict 1:1 relationship, all multiplicity-based operators reduce to degenerate distributions.

---

### 4.4 Algorithm (Abbreviated)

1. Identify candidate neighbors via schema, names, types, values.  
2. Compute FD tests, cardinality, evidence.  
3. Assign relationship type and determinism.  
4. Gate which inference operators are meaningful.  
5. Return finite inference alphabet for the anchor.

---

## 5. Cross-Theory Meta-Conclusions

1. Deterministic traversal on any finite self-referential system ⇒ **basin partitions**.  
2. Changing traversal rules ⇒ **multiple partitions**.  
3. Intersections of partitions ⇒ **tunnel structure** revealing deeper semantics.  
4. Local inference space at a node is **finite and structured**, governed by relationship type.

---

## 6. Open Conjectures (Cross-Domain)

1. **Universal attractors** across multiple rules correspond to semantically central nodes.  
2. **Tunnel density** correlates with importance of schema entities.  
3. **Inference entropy** can measure schema complexity and redundancy.

---

*Document ends.*