# Database Inference Graph Theory: Multi-Rule Tunneling for Schema Discovery

**Document Type**: Theory  
**Target Audience**: LLMs with graph theory and database background  
**Purpose**: Extend N-Link theory to typed database graphs, formalize multi-rule tunneling for schema discovery  
**Created**: 2025-12-10  
**Last Updated**: 2025-12-15  
**Status**: Active - Theoretical framework complete

---

## Abstract

This document extends N-Link Basin Partition Theory to relational databases. We formalize databases as typed, self-referential graphs where different **inference rules** (relationship types, traversal strategies) create different basin partitions. **Multi-rule tunneling** - switching inference strategies mid-traversal - reveals hidden database structure and enables automated legacy schema reverse engineering.

**Key Discovery**: The tunnel topology between basins under different inference rules IS the database's true semantic model, discoverable without documentation.

---

## 1. Motivation: From Wikipedia to Databases

### 1.1 The Generalization

**N-Link Theory** applies to any finite, closed, self-referential system:
- Wikipedia: Articles linked by hyperlinks
- Databases: Tables/records linked by relationships
- Code: Functions linked by calls
- Files: Directories linked by symbolic links

**Common properties**:
1. Finite node set
2. Ordered outgoing links per node
3. Links point only within the system
4. Deterministic traversal rules

### 1.2 Why Databases Are "Weirder"

**Wikipedia**:
- Homogeneous nodes (all articles)
- Uniform link semantics (all hyperlinks work the same)
- Simple ordering (position: 1st, 2nd, 3rd link)
- Single traversal strategy

**Databases**:
- Heterogeneous nodes (different table schemas)
- Typed link semantics (1:1 ≠ 1:M ≠ M:M ≠ implicit)
- Multiple valid orderings (column position, FK order, semantic similarity)
- **Multiple inference strategies** (formal FK, semantic, type-based)

**Implication**: "N" in databases is not just numerical position - it's the **inference rule** being applied.

### 1.3 Multi-Rule Tunneling Insight

**Problem**: Legacy databases lack complete documentation of relationships

**Traditional approach**: Manual inspection, tribal knowledge, hope

**Tunneling approach**:
1. Enumerate all inference rules (FK constraints, semantic patterns, cardinality, implicit)
2. Compute basin partition under each rule
3. Map tunnel nodes connecting basins across rules
4. **Tunnel structure reveals actual semantic model**

---

## 2. Database Graph Formalization

### 2.1 Database as Multi-Typed Graph

**Definition 2.1 (Database Graph)**:
A database $D = (T, C, R, \mathcal{I})$ where:
- $T = \{t_1, t_2, ..., t_n\}$ = finite set of tables
- $C = \{c_1, c_2, ..., c_m\}$ = finite set of columns
- $R = \{r_1, r_2, ..., r_k\}$ = finite set of relationships
- $\mathcal{I} = \{I_1, I_2, ..., I_\ell\}$ = finite set of inference rules

**Granularity choices**:
- **Table-level**: Nodes are tables, edges are table-to-table relationships
- **Column-level**: Nodes are columns, edges are column-to-column mappings
- **Record-level**: Nodes are individual records, edges are FK references

(Theory applies at any granularity; choice affects scale and detail)

### 2.2 Relationship Types

**Definition 2.2 (Typed Relationship)**:
Each relationship $r \in R$ has properties:

1. **Cardinality**: 
   - $(1:1)$: One-to-one
   - $(1:M)$: One-to-many
   - $(M:1)$: Many-to-one
   - $(M:M)$: Many-to-many

2. **Formality**:
   - **Explicit**: Declared FK constraint in schema
   - **Implicit**: Inferred from column names, types, data distribution

3. **Directionality**:
   - **Unidirectional**: Parent → Child (FK constraint direction)
   - **Bidirectional**: Navigable in both directions (logical equivalence)

4. **Junction requirement**:
   - **Direct**: Table A → Table B directly
   - **Indirect**: Table A → Junction Table → Table B

### 2.3 Inference Rules

**Definition 2.3 (Inference Rule)**:
An inference rule $I \in \mathcal{I}$ is a function:
$$I: (n, \text{context}) \to \text{set of reachable nodes}$$

Where:
- $n$ = current node (table/column/record)
- $\text{context}$ = traversal history, cardinality constraints, etc.
- Output = set of nodes reachable under this inference strategy

**Examples**:

**$I_{\text{FK}}$** (Explicit Foreign Keys):
- Only follow declared FK constraints
- Deterministic, documented
- May miss implicit relationships

**$I_{\text{semantic}}$** (Semantic Name Matching):
- Match columns by naming conventions (`user_id`, `customer_id`)
- Discovers undocumented relationships
- Requires pattern recognition

**$I_{\text{type}}$** (Data Type Inference):
- Match columns by compatible types (INT → INT, VARCHAR → VARCHAR)
- Very permissive, may over-connect
- Useful for exploratory analysis

**$I_{\text{cardinality}}$** (Cardinality-Aware):
- Follow only 1:1 or 1:M relationships
- Avoids ambiguous M:M traversals
- Useful for deterministic path finding

**$I_{\text{value}}$** (Value Distribution):
- Infer relationship from overlapping value sets
- Example: Column A values ⊆ Column B values → likely FK
- Data-driven discovery

---

## 3. Basin Structure Under Inference Rules

### 3.1 Rule-Specific Partitions

**Theorem 3.1 (Inference Rule Partition)**:
For any inference rule $I \in \mathcal{I}$, the database graph partitions into disjoint basins:
$$D = \bigcup_{j=1}^{k_I} \text{Basin}_I(T_j)$$

Where each basin terminates in:
- **HALT**: Node with no outgoing links under rule $I$
- **CYCLE**: Set of nodes forming closed loop under rule $I$

**Proof**: Identical to N-Link Theorem 4.3 - deterministic function on finite graph. ∎

**Corollary 3.2 (Exhaustive Basin Labeling is Search-Shrinking)**:
For any fixed rule $I$ (i.e., a deterministic successor function on a finite node set, with HALT allowed), every node has a unique terminal fate (HALT or a cycle). Therefore basin membership can be exhaustively labeled by iterating forward from unassigned nodes until a terminal (or previously-labeled node) is reached, then backfilling labels along the discovered path (path compression).

Operationally: once a basin label is assigned to a node, that node can be removed from the remaining search space for that same rule $I$; as labeling proceeds, the amount of “unknown” work monotonically decreases.

**Interpretation (Rule-Slice of a Multiplex)**:
If we consider the multiplex state space $(\text{node}, I)$ with (a) within-rule edges induced by $I$ and (b) tunneling edges that switch rules while staying on the same underlying node, then each disjoint basin under a fixed rule $I$ is a 1D “cross-section” (a slice at fixed $I$) of a higher-dimensional multiplex structure. Shared nodes act as natural junctions for tunnels across rules.

### 3.2 Different Rules → Different Partitions

**Key observation**: The same database has different basin structures under different inference rules.

**Example**:
- Under $I_{\text{FK}}$: May have 10 disconnected basins (formal subsystems)
- Under $I_{\text{semantic}}$: May consolidate to 3 basins (hidden connections revealed)
- Under $I_{\text{type}}$: May have 1 giant basin (all tables type-connected)

**Implication**: No single "true" partition - structure depends on inference strategy.

---

## 4. Multi-Rule Tunneling Theory

### 4.1 Tunnel Definition

**Definition 4.1 (Tunnel Node)**:
A node $n$ is a tunnel node between rules $I_1$ and $I_2$ if:
$$\exists a, b : a \in \text{Basin}_{I_1}(T_i) \land b \in \text{Basin}_{I_2}(T_j) \land$$
$$a \xrightarrow{I_1} n \xrightarrow{I_2} b$$

**Interpretation**: Can reach $n$ using rule $I_1$ from basin under $I_1$, then switch to rule $I_2$ to reach different basin.

### 4.2 Multi-Rule Path

**Definition 4.2 (Heterogeneous Path)**:
A multi-rule path is:
$$P = [(n_0, I_0), (n_1, I_1), ..., (n_t, I_t)]$$

Where:
- $n_k$ = node at step $k$
- $I_k$ = inference rule used for transition $k \to k+1$
- $n_{k+1} \in I_k(n_k, \text{context}_k)$

**Path cost**:
- **Hop count**: $t$ (number of transitions)
- **Rule switches**: $|\{k : I_k \neq I_{k+1}\}|$
- **Weighted cost**: $\alpha \cdot \text{hops} + \beta \cdot \text{switches}$

### 4.3 Tunneling Motivation

**Problem**: How to navigate from Table A to Table B?

**Single-rule limitation**:
- May not be connected under $I_{\text{FK}}$ (no FK path)
- May require many hops under $I_{\text{semantic}}$

**Multi-rule solution**:
1. Start with $I_{\text{FK}}$ (explicit, reliable)
2. Hit dead-end (HALT or wrong basin)
3. Switch to $I_{\text{semantic}}$ (discover implicit link)
4. Continue with $I_{\text{FK}}$ (return to explicit)
5. Reach target with **fewer total hops** and higher confidence

### 4.4 Optimal Tunneling Path

**Definition 4.4 (Minimal Tunnel Path)**:
For nodes $a, b$, the optimal path minimizes cost function:
$$P^* = \arg\min_P \text{cost}(P)$$

Subject to:
- Path starts at $a$, ends at $b$
- Each transition uses valid inference rule
- Rule switches are minimized for given hop count

**Conjecture 4.4**: Optimal paths prefer:
1. Explicit relationships ($I_{\text{FK}}$) when available (high confidence)
2. Short tunneling sequences through implicit rules (low uncertainty)
3. Minimal rule switching (reduced complexity)

---

## 5. Database Reverse Engineering Application

### 5.1 The Legacy Database Problem

**Given**:
- Database with tables, columns, some FK constraints
- Incomplete or missing documentation
- Unknown semantic relationships between entities
- Need to understand structure for migration, integration, or query optimization

**Traditional approach**:
- Manual inspection (slow, error-prone)
- Interviews with developers (tribal knowledge, often incomplete)
- Trial-and-error querying (misses hidden patterns)

### 5.2 Tunneling-Based Discovery

**Algorithm 5.2 (Schema Discovery via Tunneling)**:

**Phase 1: Enumerate Inference Rules**
1. Extract explicit FK constraints → $I_{\text{FK}}$
2. Identify semantic patterns (naming conventions) → $I_{\text{semantic}}$
3. Analyze data types → $I_{\text{type}}$
4. Compute value distribution overlaps → $I_{\text{value}}$
5. Classify cardinality constraints → $I_{\text{1:1}}, I_{\text{1:M}}, I_{\text{M:M}}$

**Phase 2: Compute Basin Partitions**
For each rule $I_i \in \mathcal{I}$:
1. Apply basin construction (Algorithm 4.2 from N-Link theory)
2. Identify terminals (HALTs and CYCLEs)
3. Map basin membership for each table/column

**Phase 3: Identify Tunnel Nodes**
1. Find nodes reachable under multiple rules
2. Classify tunnel type (explicit↔semantic, type↔value, etc.)
3. Compute tunnel frequency (how many basins connect through this node)

**Phase 4: Reconstruct Semantic Model**
1. **Central entities**: High tunnel frequency across rules
2. **Peripheral tables**: Low tunnel frequency, isolated basins
3. **Subsystem boundaries**: Basin partitions that persist across multiple rules
4. **Hidden relationships**: Tunnels through $I_{\text{semantic}}$ or $I_{\text{value}}$ not in schema

**Output**: Discovered semantic model revealing actual database structure.

### 5.3 Semantic Model Properties

**Discovered structure reveals**:

1. **Entity Importance**:
   - Tables with high tunnel frequency = central domain entities
   - Example: `Users`, `Products`, `Orders` in e-commerce

2. **Natural Clustering**:
   - Basins that remain together across multiple rules = logical subsystems
   - Example: Billing tables vs. Inventory tables

3. **Missing Documentation**:
   - Tunnels via $I_{\text{semantic}}$ not in $I_{\text{FK}}$ = undocumented relationships
   - Should be formalized as explicit FKs

4. **Query Patterns**:
   - Optimal tunneling paths = natural join sequences
   - Frequent tunnel routes = common query patterns

5. **Data Governance Domains**:
   - Isolated basins = independent governance domains
   - Shared tunnel nodes = cross-domain dependencies

---

## 6. Open Research Tasks

### 6.1 TODO #1: Enumerate All Logical Inferences

**Objective**: Create comprehensive taxonomy of valid database inference rules.

**Approach**: Leverage formal logic and set theory

**Inference Categories**:

**A. Set-Theoretic Inferences**:
- **Subset**: $A \subseteq B$ (values in column A all appear in column B)
- **Superset**: $A \supseteq B$
- **Intersection**: $A \cap B \neq \emptyset$ (overlapping values)
- **Disjoint**: $A \cap B = \emptyset$ (no overlap → likely independent)
- **Bijection**: $|A| = |B| \land A \subseteq B \land B \subseteq A$ (1:1 mapping)

**B. Cardinality-Based Inferences**:
- **Uniqueness**: Column has unique constraint → potential PK or unique FK target
- **Multiplicity**: Non-unique column → likely FK to parent or attribute
- **Null patterns**: High null percentage → optional relationship (left join)

**C. Type-Theoretic Inferences**:
- **Structural typing**: Matching data types (INT64, VARCHAR(255))
- **Semantic typing**: Column names suggest domain (email, phone, address)
- **Range constraints**: Check constraints imply valid relationship domains

**D. Functional Dependencies**:
- **Transitive**: $A \to B \land B \to C \implies A \to C$
- **Multi-valued**: $A \twoheadrightarrow B$ (A determines set of B values)
- **Join dependencies**: Complex relationships across multiple tables

**E. Temporal Inferences**:
- **Timestamp ordering**: `created_at < updated_at` (temporal consistency)
- **Causality**: Events in Table A precede effects in Table B
- **Version tracking**: Surrogate keys + timestamps reveal history

**F. Statistical Inferences**:
- **Correlation**: Strong statistical correlation suggests relationship
- **Distribution matching**: Similar value distributions → potential join candidates
- **Outlier detection**: Anomalies may indicate broken relationships

**Deliverable**: Formal catalog of inference rules with:
- Mathematical definition
- Decidability (can we compute this algorithmically?)
- Confidence metric (how reliable is this inference?)
- Precedence order (which inferences override others in conflicts?)

### 6.2 TODO #2: Identify Discoverable Formal Relationships

**Objective**: Enumerate relationship types automatically discoverable from database metadata and data.

**Categories**:

**A. Schema-Level Discovery** (High Confidence):
1. **Explicit FK Constraints**:
   - Declared in DDL (`FOREIGN KEY REFERENCES`)
   - Cardinality: 1:M or 1:1 (determinable from unique constraints)
   - Directionality: Parent → Child

2. **Primary Keys**:
   - Unique, non-null constraint
   - Target for FK relationships
   - Single or composite

3. **Unique Constraints**:
   - Alternative keys
   - Potential 1:1 relationship targets

4. **Check Constraints**:
   - Value domain restrictions
   - Imply valid join value ranges

**B. Name-Based Discovery** (Medium Confidence):
1. **Column Name Patterns**:
   - `*_id` suffix → likely FK
   - `id` prefix → likely PK
   - Matching names across tables (`user_id` in multiple tables)

2. **Table Name Semantics**:
   - Plural nouns → entity tables (`users`, `orders`)
   - Compound names → junction tables (`user_roles`, `order_items`)

3. **Convention Matching**:
   - Rails: `table_name_id`
   - Django: `tablename_ptr`
   - Entity Framework: `TableNameID`

**C. Type-Based Discovery** (Low-Medium Confidence):
1. **Matching Data Types**:
   - INT → INT (potential FK)
   - GUID → GUID (potential distributed FK)
   - VARCHAR(N) → VARCHAR(N) (potential semantic link)

2. **Type Hierarchy**:
   - Subtype relationships (inheritance)
   - Polymorphic associations

**D. Data-Driven Discovery** (Variable Confidence):
1. **Value Set Analysis**:
   - Column A values ⊆ Column B values (likely FK: A → B)
   - Perfect overlap → potential 1:1
   - Partial overlap → potential M:M

2. **Cardinality Analysis**:
   - Count distinct values
   - Compute uniqueness ratio
   - Identify one-to-many patterns in data

3. **Null Distribution**:
   - High nulls → optional relationship (LEFT JOIN)
   - No nulls → mandatory relationship (INNER JOIN)

**E. Junction Table Detection** (Medium-High Confidence):
1. **Composite PK Pattern**:
   - Table with PK = (FK1, FK2) → likely M:M junction

2. **Minimal Attributes**:
   - Only FK columns (or FK + timestamps) → pure junction
   - Additional attributes → attributed relationship

**Deliverable**: Decision tree for automated relationship discovery with confidence scores.

### 6.3 TODO #3: Logical Constraints on Inferences

**Objective**: Formalize how key constraints affect available inferences.

**Problem**: Unique vs non-unique keys constrain inference operations differently.

**Examples**:

**A. Unique Key → Non-Unique Key**:
- **Forward direction** (UK → NUK):
  - Deterministic: Each unique value maps to specific non-unique value
  - Inference: Simple lookup (1:1 or M:1)
  - SQL: `SELECT nuk FROM table WHERE uk = ?`
  
- **Reverse direction** (NUK → UK):
  - Non-deterministic: Non-unique value may map to multiple unique values
  - Inference: Set-valued (returns multiple results)
  - SQL: `SELECT uk FROM table WHERE nuk = ?` → multiple rows
  - **Constrained**: Cannot use for deterministic traversal

**B. Non-Unique Key → Unique Key**:
- **Forward direction** (NUK → UK):
  - Non-deterministic unless constrained by context
  - May require additional filters
  
- **Reverse direction** (UK → NUK):
  - Deterministic (unique key guarantees single source)
  - Reliable for path traversal

**C. Composite Keys**:
- **Partial matching**: Match on subset of composite key
  - Returns set of candidates
  - Requires further refinement
  
- **Full matching**: Match on all components
  - Deterministic if composite is unique

**D. Metadata Constraints**:

**Inference Rule Adjustments**:

```
IF source_column.is_unique AND target_column.is_unique:
    relationship = ONE_TO_ONE
    bidirectional_deterministic = True
    
ELIF source_column.is_unique AND NOT target_column.is_unique:
    relationship = ONE_TO_MANY
    forward_deterministic = False  # UK → NUK returns set
    reverse_deterministic = True   # NUK → UK finds unique parent
    
ELIF NOT source_column.is_unique AND target_column.is_unique:
    relationship = MANY_TO_ONE
    forward_deterministic = True   # NUK → UK (if exists)
    reverse_deterministic = False  # UK → NUK returns set
    
ELSE:  # Both non-unique
    relationship = MANY_TO_MANY
    bidirectional_non_deterministic = True
    requires_context = True  # Need additional constraints
```

**Nullability Constraints**:
```
IF source_column.nullable:
    relationship_optional = True
    join_type = LEFT_JOIN
    inference_reliability -= 0.2  # Lower confidence
ELSE:
    relationship_mandatory = True
    join_type = INNER_JOIN
    inference_reliability += 0.1  # Higher confidence
```

**Deliverable**: Formal logic rules for inferring relationship properties from column metadata:
- Input: (source_column_metadata, target_column_metadata)
- Output: (relationship_type, cardinality, determinism_flags, confidence_score)

---

## 7. Meta-Observation: LLM Pattern Matching

### 7.1 Self-Referential Discovery Process

**Observation**: During this wayfinding session, the LLM (Claude) anticipated "reverse engineering legacy databases" without explicit instruction.

**Why**: The LLM performed analogous pattern matching:
1. **Input context**: N-Link theory + database generalization prompt
2. **Pattern recognition**: "Self-referential system lacking documentation"
3. **Analogy**: LLM loading context = reverse engineering unknown structure
4. **Inference**: Database discovery problem ≈ LLM context discovery problem
5. **Prediction**: Same techniques apply (enumerate rules, map structure, find connections)

### 7.2 The Parallel Structure

**LLM Context Loading**:
- Unknown project structure
- Multiple documentation sources (README, instructions, conversation history)
- Different "traversal rules" (read README → follow references → load detailed docs)
- Goal: Build semantic model of project

**Database Reverse Engineering**:
- Unknown schema structure
- Multiple relationship types (FK, semantic, implicit)
- Different "traversal rules" (follow FKs → infer from names → analyze data)
- Goal: Build semantic model of database

**Same problem**: Discover hidden structure in self-referential system through multi-strategy traversal.

### 7.3 Implication for AI-Facing Documentation

This meta-observation validates our documentation strategy:
- **Hierarchical context loading** = optimal tunneling path through knowledge graph
- **Multiple entry points** (CONTEXT_LOAD_PROTOCOL, wayfinding-methodology, theory docs) = different inference rules
- **Cross-references** = tunnel nodes connecting documentation basins

**Principle**: AI context loading IS a database reverse engineering problem.

Optimal documentation = structure that supports efficient multi-rule tunneling.

---

## 8. Formalization Summary

### 8.1 Core Theorems

1. **Database Partition Theorem**: Any inference rule partitions database into disjoint basins (Theorem 3.1)
2. **Multi-Rule Connectivity**: Different rules create different partitions (Section 3.2)
3. **Tunnel Existence**: Nodes reachable under multiple rules enable cross-basin traversal (Definition 4.1)
4. **Semantic Discovery**: Tunnel topology reveals actual database structure (Section 5.2)

### 8.2 Key Discoveries

1. **Inference rules generalize N-Link rules**: Not just numerical position, but logical relationship type
2. **Tunneling reveals hidden structure**: Cross-rule paths expose undocumented relationships
3. **Automated schema discovery**: Algorithm for reverse engineering without documentation
4. **Meta-pattern**: LLM context loading ≈ database reverse engineering (both are tunneling problems)

### 8.3 Open Research Questions

1. **Optimal inference rule set**: What is the minimal complete set of inference rules?
2. **Confidence calibration**: How to score reliability of different inference types?
3. **Computational complexity**: What is the complexity of optimal tunneling path finding?
4. **Generalization bounds**: What other self-referential systems admit tunneling analysis?

---

## 9. Next Steps

### 9.1 Immediate Tasks

**TODO #1**: Complete formal enumeration of logical inference rules
- Review set theory, type theory, functional dependencies
- Catalog with mathematical definitions
- Create decidability analysis

**TODO #2**: Build relationship discovery taxonomy
- Schema-level vs data-driven
- Confidence scoring framework
- Precedence rules for conflicts

**TODO #3**: Formalize metadata constraint logic
- Uniqueness × nullability interaction rules
- Cardinality inference from constraints
- Determinism flags for path planning

### 9.2 Long-Term Research

1. **Empirical validation**: Test on real legacy databases
2. **Algorithm implementation**: Build automated discovery tool
3. **Benchmark creation**: Standard test suite for schema discovery
4. **Cross-domain application**: Apply to code graphs, file systems, citation networks

---

## Appendix A: Notation Reference

| Symbol | Meaning |
|--------|---------|
| $D$ | Database |
| $T$ | Set of tables |
| $C$ | Set of columns |
| $R$ | Set of relationships |
| $\mathcal{I}$ | Set of inference rules |
| $I$ | Individual inference rule |
| $I_{\text{FK}}$ | Foreign key inference rule |
| $I_{\text{semantic}}$ | Semantic name matching rule |
| $\text{Basin}_I(T)$ | Basin of attraction under rule $I$ terminating at $T$ |
| $(1:1), (1:M), (M:1), (M:M)$ | Cardinality types |
| $P$ | Multi-rule path |
| UK | Unique key |
| NUK | Non-unique key |

## Appendix B: Connection to N-Link Theory

This theory extends [n-link-rule-theory.md](n-link-rule-theory.md):
- N-Link: Fixed numerical position determines next node
- Database: Inference rule (relationship type) determines next node
- Both: Finite, closed, deterministic → basin partition structure
- Multi-rule: Enables tunneling between partitions

**Universal principle**: Self-referential systems with multiple deterministic traversal strategies contain discoverable cross-strategy tunnel structures that reveal hidden semantic models.

---

**Status**: Theoretical framework complete, three research tasks defined  
**Next Milestone**: Complete TODO #1 (enumerate logical inferences)  
**Last Updated**: 2025-12-15  
**Authors**: Human-AI collaborative wayfinding session


