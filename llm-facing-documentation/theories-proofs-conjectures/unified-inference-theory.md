# Unified Inference Theory: Basin Partitions, Multi-Rule Tunneling, and Event-Coupled Inference

**Document Type**: Theory  
**Target Audience**: LLMs  
**Purpose**: Comprehensive formal framework integrating N-Link theory, database inference, tunneling, and event-coupled inference  
**Created**: 2025-12-15  
**Supersedes**: inference-summary.md, inference-summary-with-event-tunneling.md  
**Status**: Active

---

## Abstract

This document unifies the formal mathematical frameworks developed for self-referential graph systems. It covers:
1. N-Link deterministic traversal and basin partition theory
2. Database inference graph theory and multi-rule tunneling
3. Local inference enumeration and operator gating
4. Event-coupled inference and signature refinement

**Target audience**: LLMs with background in graph theory, deterministic maps, functional graphs, and relational database semantics.

---

## 1. System Context

This theory addresses formal structures arising from:
- N-Link Rule Theory on finite self-referential graphs
- Database Inference Graph Theory
- Local Inference Enumeration and Operator Gating
- Deterministic traversal partitions and multi-rule tunneling
- Event-coupled inference from execution context

All results apply to finite, closed, self-referential systems (Wikipedia articles, database schemas, function call graphs, file systems).

---

## 2. N-Link Deterministic Traversal Theory

### 2.1 Definitions

**Finite Directed Graph**  
A closed directed graph \( G = (V, E) \) with \( |V| < \infty \).

**Outgoing Link Ordering**  
For each node \( a \in V \), outgoing edges are ordered:  
\[
\text{links}(a) = [L_1^a, L_2^a, \dots, L_{k_a}^a].
\]

**N-Link Function**  
For fixed \( N \in \mathbb{N} \):  
\[
f_N(a) = 
\begin{cases}
L_N^a & N \le k_a \\
\text{HALT} & N > k_a.
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
Every node's forward path ends exactly in:

1. **HALT**, if \( f_N(a_t) = \text{HALT} \);  
2. **CYCLE**, if \( a_t = a_j \) for some \( j < t \).

Mutually exclusive, exhaustive.

---

### 2.4 Terminal States and Basins

**Terminal State**  
Either a HALT node or a directed cycle \( C \subseteq V \).

**Basin of Attraction**  
\[
\text{Basin}_N(T) = \{ a \in V : \text{Path}_N(a) \text{ terminates at } T \}.
\]

**Theorem 3 (Partition Theorem)**  
The basins \( \{ \text{Basin}_N(T) \} \) form a **disjoint partition** of \( V \).

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
   N_1 < N_2 \implies P_{\text{HALT}}(N_1) \le P_{\text{HALT}}(N_2).
   \]

2. **Basin Size Power Law**  
   \( P(\text{basin size} = s) \sim s^{-\alpha} \).

3. **Critical N (Phase Transition)**  
   Exists \( N^* \) such that  
   \( P_{\text{CYCLE}}(N^*) = P_{\text{HALT}}(N^*) = 0.5 \).

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
\forall I \in \mathcal{I}, \quad \text{Basins}_I \text{ partition the schema graph }.
\]

**Proof Sketch**  
Identical to N-Link termination and partition arguments; determinism + finiteness ⇒ HALT/CYCLE.

---

### 3.3 Multi-Rule Tunneling

If \( I_1 \) and \( I_2 \) are different deterministic rules, their basin partitions differ.  
Nodes reachable by both are **tunnel nodes**.

**Definition (Tunnel Node)**:  
A node \( n \) is a tunnel node between rules \( I_1 \) and \( I_2 \) if:
\[
\exists a, b : a \in \text{Basin}_{I_1}(T_i) \land b \in \text{Basin}_{I_2}(T_j) \land a \xrightarrow{I_1} n \xrightarrow{I_2} b
\]

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

Multiplicity-based operators (counts, sums, ratios) are **degenerate** in 1:1 and on the "1 side" of M:1.

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

## 5. Event-Coupled Inference

### 5.1 Integration with Basin Structure

Let \(V\) be a finite node set (tables, columns, rows, or entities).

Define four orthogonal deterministic inference rule families:

- \(I_{struct}\): structural constraints (PK/FK, uniqueness)
- \(I_{sem}\): semantic and type-based inference
- \(I_{val}\): value-set and cardinality inference
- \(I_{event}\): event-coupled inference from logs, transactions, or execution context

Each rule family \(I\) induces a finite candidate-next relation:
\[
N_I(v) \subseteq V
\]

A deterministic selector \(S\) produces a traversal function:
\[
f_I(v) =
\begin{cases}
S(N_I(v)) & N_I(v) \neq \emptyset \\
\text{HALT} & N_I(v) = \emptyset
\end{cases}
\]

By finiteness and determinism, each \(f_I\) induces a basin partition over \(V\) with HALT or CYCLE terminals.

---

### 5.2 Multi-Axis Tunneling

A multi-axis traversal path is defined as:
\[
P = [(v_0, I_0), (v_1, I_1), \dots, (v_t, I_t)]
\]
where:
\[
v_{k+1} = f_{I_k}(v_k)
\]

A **tunnel step** occurs when \(I_{k+1} \neq I_k\).

A **tunnel node** is any node where traversal under one axis halts or becomes unproductive, but switching to another axis enables continued traversal.

---

### 5.3 Event Signatures and Refinement

Define an **event signature**:
\[
\sigma(v) = (x_1, x_2, \dots, x_k)
\]

This induces an equivalence relation:
\[
v \equiv_\sigma w \iff \sigma(v) = \sigma(w)
\]

**Theorem (Monotonic Refinement)**

If a refined signature is defined as:
\[
\sigma' = (\sigma, y)
\]
then:
\[
|[v]_{\sigma'}| \le |[v]_{\sigma}|
\]

Adding constraints to an event signature cannot increase the size of equivalence classes.

---

### 5.4 Event-Signature Convergence Conjecture

**Conjecture**  
In systems where:
1. event identifiers are high-resolution and stable,
2. concurrency per event identifier is bounded,
3. generating processes are consistent,

there exists a refinement \(\sigma^*\) such that:
\[
|[v]_{\sigma^*}| = 1
\]

for a large subset of nodes, yielding effective 1:1 mappings not declared in schema metadata.

---

### 5.5 Implications

Event-coupled inference:
- Enables tunneling across basin partitions
- Recovers from HALT artifacts (e.g., redirects)
- Extends explicit 1:1 mappings across inference axes
- Unifies structural, semantic, value, and process-level inference

---

## 6. Cross-Theory Meta-Conclusions

1. Deterministic traversal on any finite self-referential system ⇒ **basin partitions**.  
2. Changing traversal rules ⇒ **multiple partitions**.  
3. Intersections of partitions ⇒ **tunnel structure** revealing deeper semantics.  
4. Local inference space at a node is **finite and structured**, governed by relationship type.
5. Event-coupled inference adds a fourth dimension to structural/semantic/value-based inference axes.

---

## 7. Open Conjectures (Cross-Domain)

1. **Universal attractors** across multiple rules correspond to semantically central nodes.  
2. **Tunnel density** correlates with importance of schema entities.  
3. **Inference entropy** can measure schema complexity and redundancy.
4. **Event-signature convergence** enables discovery of implicit 1:1 relationships from execution traces.

---

## Document History

**2025-12-15**: Created by merging inference-summary.md and inference-summary-with-event-tunneling.md  
**2025-12-10**: Original inference summaries created during theory development sessions

---
