# LLM-Facing Summary of Formal Theorems, Proofs, and Conjectures
(Extended with Event-Coupled Basin Tunneling)

**DEPRECATED**: This document has been superseded by [unified-inference-theory.md](../unified-inference-theory.md)  
**Date Deprecated**: 2025-12-15  
**Reason**: Merged with inference-summary.md for consolidated theory reference  
**Location**: Moved to deprecated/ subdirectory to reduce context pollution

---

## Note
This document supersedes `inference-summary.md` by adding a formal integration
of event-coupled inference into basin and tunneling theory.

---

## X. Event-Coupled Inference in Basin and Tunneling Theory

### X.1 Integration of Event-Coupled Inference into Basin Structure

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
HALT & N_I(v) = \emptyset
\end{cases}
\]

By finiteness and determinism, each \(f_I\) induces a basin partition over \(V\) with HALT or CYCLE terminals.

---

### X.2 Multi-Axis Tunneling

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

### X.3 Event Signatures and Refinement

Define an **event signature**:
\[
\sigma(v) = (x_1, x_2, \dots, x_k)
\]

This induces an equivalence relation:
\[
v \equiv_\sigma w \iff \sigma(v) = \sigma(w)
\]

#### Theorem (Monotonic Refinement)

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

### X.4 Event-Signature Convergence Conjecture

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

### X.5 Implications

Event-coupled inference:
- enables tunneling across basin partitions,
- recovers from HALT artifacts (e.g., redirects),
- extends explicit 1:1 mappings across inference axes,
- unifies structural, semantic, value, and process-level inference.

---

End of document.
