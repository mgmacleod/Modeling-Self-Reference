# Annotated Bibliography: Multi-Rule Tunneling for Schema Discovery

This bibliography supports research on viewing database schemas as multiplex structures where different inference rules (FK-based, semantic, cardinality, implicit) create distinct graph partitions over the same node set. Switching between rule layers—"tunneling"—reveals hidden structural relationships invisible to any single rule type.

---

## 1. Multiplex and Multilayer Networks (2000–2025)

### Foundational Formalism and Unified Frameworks

**Kivelä, M., Arenas, A., Barthelemy, M., Gleeson, J.P., Moreno, Y., and Porter, M.A.** "Multilayer networks." *Journal of Complex Networks* 2(3): 203–271, 2014.

This 69-page anchor paper establishes the definitive mathematical framework for multilayer networks through tensors and supra-adjacency matrices. It constructs a "dictionary" unifying diverse terminology (multiplex, interdependent, networks of networks) and formalizes how identical node sets can exhibit different connectivity patterns across layers. The framework directly maps to schema discovery where tables/columns maintain identity while edge semantics vary by inference rule type.

**Boccaletti, S., Bianconi, G., Criado, R., et al.** "The structure and dynamics of multilayer networks." *Physics Reports* 544(1): 1–122, 2014.

This exhaustive 122-page review redefines structural measures for multilayer systems and covers inter-layer coupling mechanisms, percolation, and dynamical processes. The treatment of how "multilayer nature affects processes and dynamics" applies directly to understanding how different inference rules reveal different structural properties in database schemas.

**De Domenico, M., Solé-Ribalta, A., Cozzo, E., et al.** "Mathematical formulation of multilayer networks." *Physical Review X* 3(4): 041022, 2013.

Introduces the complete tensorial framework using rank-4 tensors, generalizing centrality measures, clustering coefficients, and modularity to the multilayer setting. The mathematical formulation enables precise treatment of how nodes exhibit "different connectivity patterns depending on the information encoded by the layer"—analogous to database tables having different relationship structures under different inference rules.

### Cross-Layer Dynamics and Community Structure

**Mucha, P.J., Richardson, T., Macon, K., Porter, M.A., and Onnela, J.-P.** "Community structure in time-dependent, multiscale, and multiplex networks." *Science* 328(5989): 876–878, 2010.

Develops generalized modularity for "multislice" networks where identical nodes appear across layers with inter-layer coupling. Demonstrates on U.S. Senate voting records how switching between slices reveals community structure invisible in any single layer—precisely the mechanism underlying multi-rule schema discovery.

**Gómez, S., Díaz-Guilera, A., Gómez-Gardeñes, J., et al.** "Diffusion dynamics on multiplex networks." *Physical Review Letters* 110(2): 028701, 2013.

Introduces the supra-Laplacian matrix for analyzing diffusion across multiplex structures. The spectral analysis reveals which layer combinations accelerate or impede information spread, providing theoretical tools for understanding how schema discovery algorithms propagate across multi-rule structures.

**De Domenico, M., Nicosia, V., Arenas, A., and Latora, V.** "Structural reducibility of multilayer networks." *Nature Communications* 6: 6864, 2015.

Uses quantum information theory to determine the minimum number of layers necessary to accurately represent a multilayer system. **Highly relevant**: directly addresses whether all inference rule types are necessary or whether some are redundant, providing methodology to identify which rule combinations provide maximal structural distinguishability.

### Interdependent Networks and Emergent Structure

**Buldyrev, S.V., Parshani, R., Paul, G., Stanley, H.E., and Havlin, S.** "Catastrophic cascade of failures in interdependent networks." *Nature* 464(7291): 1025–1028, 2010.

Foundational paper demonstrating that coupled networks exhibit drastically different behavior than isolated networks—failure cascades across layers can cause complete fragmentation. Demonstrates that inter-layer dependencies reveal structural vulnerabilities invisible when layers are analyzed in isolation, analogous to discovering schema dependencies only visible when multiple inference rules interact.

**Gao, J., Buldyrev, S.V., Stanley, H.E., and Havlin, S.** "Networks formed from interdependent networks." *Nature Physics* 8: 40–48, 2012.

Introduces the "network of networks" concept with exact solutions for connectivity in interdependent random networks. Provides theoretical basis for understanding how different inference rules (each creating a network layer) interact to form a complete picture of schema structure.

**Cellai, D., López, E., Zhou, J., Gleeson, J.P., and Bianconi, G.** "Percolation in multiplex networks with overlap." *Physical Review E* 88(5): 052811, 2013.

Shows that link overlap among layers (edges present in multiple layers) improves robustness and changes critical behavior. **Directly relevant**: edges appearing under multiple inference rules (FK-based AND semantic AND cardinality) represent robust schema connections, while layer-specific edges reveal specialized structure.

### Layer Aggregation and Emergence

**Cardillo, A., Gómez-Gardeñes, J., Zanin, M., et al.** "Emergence of network features from multiplexity." *Scientific Reports* 3: 1344, 2013.

Empirically analyzes how structural properties emerge from layer aggregation in the European Air Transportation Multiplex. Addresses whether topological features characterize individual layers or only emerge at aggregate level—directly mapping to whether schema properties exist within individual inference rules or emerge when rules are combined.

**De Domenico, M., Granell, C., Porter, M.A., and Arenas, A.** "The physics of spreading processes in multilayer networks." *Nature Physics* 12: 901–906, 2016.

Reviews how multiplexity and interdependencies affect both dynamics and function. Central message: "throwing away or aggregating available structural information can generate misleading results"—directly supporting multi-rule analysis where different inference rules capture distinct structural relationships.

**Battiston, F., Nicosia, V., and Latora, V.** "Structural measures for multiplex networks." *Physical Review E* 89(3): 032804, 2014.

Proposes multiplex degree, clustering, and centrality measures characterizing "multiplexicity"—inter-layer connectivity and structural overlap. Provides metrics for identifying "hub" tables central under multiple inference rules vs. "specialized" tables central only under specific rules.

**De Domenico, M.** "More is different in real-world multilayer networks." *Nature Physics* 19: 1247–1262, 2023.

Recent review summarizing how layered structure produces phenomena invisible in isolated subsystems or their aggregation. Title references Philip Anderson's emergence paradigm—the theoretical foundation for multi-rule tunneling where schema structure emerges from inference rule combinations, not from any single rule.

---

## 2. Functional Dependencies and Schema Theory (2000–2025)

### Conditional Functional Dependencies

**Fan, W., Geerts, F., Jia, X., and Kementsietsidis, A.** "Conditional Functional Dependencies for Capturing Data Inconsistencies." *ACM Transactions on Database Systems* 33(2): Article 6, 2008.

Introduces CFDs extending traditional FDs with value patterns, providing Armstrong-like axioms for CFD inference (proven coNP-complete vs. linear for FDs). CFDs demonstrate how different dependency types partition schemas differently based on data patterns, directly supporting the concept of switching between rule sets.

**Fan, W., Geerts, F., Li, J., and Xiong, M.** "Discovering Conditional Functional Dependencies." *IEEE Transactions on Knowledge and Data Engineering* 23(5): 683–697, 2011.

Develops CFD discovery algorithms including CFDMiner (closed itemset mining), CTANE (level-wise TANE extension), and FastCFD. Presents discovery combining FD-based and pattern mining approaches—switching between methodologies reveals different dependency structures.

### Core FD Discovery Algorithms

**Huhtala, Y., Kärkkäinen, J., Porkka, P., and Toivonen, H.** "TANE: An Efficient Algorithm for Discovering Functional and Approximate Dependencies." *The Computer Journal* 42(2): 100–111, 1999.

Seminal algorithm using tuple partitioning for efficient FD validation, supporting approximate FD discovery via error thresholds. TANE's partition-based approach enables testing different dependency types using the same underlying structure—efficient rule switching.

**Papenbrock, T., Ehrlich, J., Marten, J., et al.** "Functional Dependency Discovery: An Experimental Evaluation of Seven Algorithms." *Proceedings of the VLDB Endowment* 8(10): 1082–1093, 2015.

Comprehensive comparison of seven FD algorithms (TANE, FUN, Dep-Miner, FD_Mine, DFD, FastFDs, FDEP), classifying by strategy. Demonstrates that different algorithmic approaches are optimal for different data characteristics—supporting the idea that switching inference strategies reveals different schema structure.

**Papenbrock, T. and Naumann, F.** "A Hybrid Approach to Functional Dependency Discovery." *Proceedings of ACM SIGMOD*, 2016, pp. 821–833.

Introduces HyFD combining sampling-based induction with efficient validation, outperforming previous approaches on datasets with 50+ attributes. HyFD's hybrid strategy—combining induction and validation phases—exemplifies synergistic rule switching.

### Generalized Dependency Types

**Chu, X., Ilyas, I.F., and Papotti, P.** "Discovering Denial Constraints." *Proceedings of the VLDB Endowment* 6(13): 1498–1509, 2013.

Introduces denial constraints (DCs) as unifying language generalizing FDs, CFDs, and check constraints, with linear implication testing. DCs subsume multiple dependency types, enabling systematic switching between specialized rule types within a single formalism.

**Szlichta, J., Godfrey, P., and Gryz, J.** "Fundamentals of Order Dependencies." *Proceedings of the VLDB Endowment* 5(11): 1220–1231, 2012.

Foundational paper defining order dependencies (ODs) describing lexicographical ordering relationships, properly subsuming FDs. ODs capture order-based semantics (e.g., higher salary → higher taxes) invisible to equality-based FD analysis.

**Szlichta, J., Godfrey, P., Golab, L., Kargar, M., and Srivastava, D.** "Effective and Complete Discovery of Order Dependencies via Set-based Axiomatization." *Proceedings of the VLDB Endowment* 10(7): 721–732, 2017.

Develops efficient lattice-driven OD discovery with complete inference rules. Provides algorithms for switching to order-based dependency analysis, revealing ordered relationships that partition schemas differently than functional dependencies.

### Inclusion Dependencies

**Papenbrock, T., Kruse, S., Quiané-Ruiz, J.-A., and Naumann, F.** "Divide & Conquer-based Inclusion Dependency Discovery." *Proceedings of the VLDB Endowment* 8(7): 774–785, 2015.

Introduces BINDER for detecting unary and n-ary INDs using divide-and-conquer, achieving **26× speedup** over SPIDER. INDs represent inter-table structure complementing intra-table FD analysis—enables first stage of multi-rule pipelines applying semantic and cardinality rules.

### Approximate and Relaxed Dependencies

**Kruse, S. and Naumann, F.** "Efficient Discovery of Approximate Dependencies." *Proceedings of the VLDB Endowment* 11(7): 759–772, 2018.

Presents Pyro for discovering approximate FDs and UCCs, addressing real-world data issues. Approximate dependencies represent a different rule type revealing patterns invisible to exact FD analysis.

**Caruccio, L., Deufemia, V., and Polese, G.** "Relaxed Functional Dependencies—A Survey of Approaches." *IEEE Transactions on Knowledge and Data Engineering* 28(1): 147–165, 2016.

Surveys **35 types** of relaxed FDs including probabilistic, differential, and metric FDs. Catalogs the full landscape of FD relaxations—each representing a different rule type revealing different structural aspects. Essential for understanding the space of possible rule sets to tunnel between.

### Surveys and Foundations

**Abedjan, Z., Golab, L., and Naumann, F.** "Profiling Relational Data: A Survey." *The VLDB Journal* 24(4): 557–581, 2015.

Comprehensive survey of data profiling tasks including FD/IND/UCC discovery with algorithm taxonomy. Provides foundational overview of all dependency types essential for understanding how different dependency classes partition schemas differently.

---

## 3. Schema Reverse Engineering (2000–2025)

### Foundational Surveys

**Rahm, E. and Bernstein, P.A.** "A Survey of Approaches to Automatic Schema Matching." *The VLDB Journal* 10(4): 334–350, 2001.

Seminal taxonomy distinguishing schema-level vs. instance-level, element-level vs. structure-level, and linguistic vs. constraint-based matchers. Provides foundational classification of inference rule types (linguistic, structural, constraint-based) that can be tunneled between during schema discovery.

**Bernstein, P.A., Madhavan, J., and Rahm, E.** "Generic Schema Matching, Ten Years Later." *Proceedings of the VLDB Endowment* 4(11): 695–701, 2011.

Retrospective documenting evolution toward hybrid approaches combining corpus-based, instance-level, and ML matchers. Validates multi-rule paradigm: effective matching requires combining multiple evidence types.

### Foreign Key Detection

**Rostin, A., Albrecht, O., Bauckmann, J., Naumann, F., and Leser, U.** "A Machine Learning Approach to Foreign Key Discovery." *Proceedings of WebDB*, 2009.

Introduces ML for distinguishing true FKs from spurious INDs using ten heuristic features (name similarity, coverage ratio, type compatibility). Demonstrates that combining multiple rule types in a classifier outperforms single-heuristic approaches—directly supports multi-rule methodology.

**Zhang, M., Hadjieleftheriou, M., Ooi, B.C., Procopiuc, C.M., and Srivastava, D.** "On Multi-Column Foreign Key Discovery." *Proceedings of the VLDB Endowment* 3(1-2): 805–814, 2010.

Proposes "Randomness" rule subsuming multiple FK heuristics (INDs, names, min/max values), requiring only two data passes. Exemplifies how multiple implicit rules unify into single discriminative features enabling efficient rule interpretation switching.

**Jiang, L. and Naumann, F.** "Holistic Primary Key and Foreign Key Detection." *Journal of Intelligent Information Systems* 54(3): 439–461, 2020.

Proposes simultaneous PK/FK detection recognizing their interdependence, achieving **88% PK precision** and **91% FK precision**. Demonstrates that different constraint types must be discovered holistically—switching between PK and FK rules reveals relationships that individual rules miss.

**Chen, Z., Narasayya, V.R., and Chaudhuri, S.** "Fast Foreign-Key Detection in Microsoft SQL Server PowerPivot for Excel." *Proceedings of the VLDB Endowment* 7(13): 1417–1428, 2014.

Describes practical FK detection in commercial tools combining name patterns, type compatibility, and cardinality ratios. Provides industrial validation that multiple heuristic rules must work together for practical FK discovery.

### Schema Matching and Mapping

**Madhavan, J., Bernstein, P.A., and Rahm, E.** "Generic Schema Matching with Cupid." *Proceedings of VLDB*, 2001, pp. 49–58.

Algorithm combining linguistic and structural matching with context-dependent shared-type handling. Cupid explicitly combines multiple rule types (linguistic, structural, type-based)—exemplifying multi-rule approach at element-matching level.

**Miller, R.J., Haas, L.M., and Hernández, M.A.** "Schema Mapping as Query Discovery." *Proceedings of VLDB*, 2000, pp. 77–88.

Introduces paradigm of schema mapping as query discovery based on value correspondences. Foundation of IBM's Clio project. Frames mapping as discovery where hidden relationships must be inferred through multiple evidence types.

**Fagin, R., Haas, L.M., Hernández, M., Miller, R.J., Popa, L., and Velegrakis, Y.** "Clio: Schema Mapping Creation and Data Exchange." *Conceptual Modeling: Foundations and Applications*, Springer LNCS 5600, pp. 198–236, 2009.

Comprehensive Clio description providing non-procedural mappings and automatic query generation. Uses schema constraints, correspondences, and data semantics together—demonstrates how constraint-based and semantic rules combine for relationship discovery.

### Inclusion Dependencies and Theoretical Foundations

**Casanova, M.A., Fagin, R., and Papadimitriou, C.H.** "Inclusion Dependencies and Their Interaction with Functional Dependencies." *Proceedings of PODS*, 1982, pp. 171–176.

Foundational paper establishing PSPACE-completeness of IND inference with complete axiomatization. Shows finite implication differs from unrestricted implication when INDs and FDs combine—critical theoretical basis for understanding how dependency types interact during rule switching.

**De Marchi, F., Lopes, S., and Petit, J.-M.** "Unary and N-ary Inclusion Dependency Discovery in Relational Databases." *Journal of Intelligent Information Systems* 32(1): 53–73, 2009.

Comprehensive levelwise algorithms for IND discovery. The progressive approach demonstrates how schema structure emerges iteratively—analogous to tunneling through increasingly complex relationship patterns.

### Data-Driven Discovery

**Dasu, T., Johnson, T., Muthukrishnan, S., and Shkapenyuk, V.** "Mining Database Structure; Or, How to Build a Data Quality Browser." *Proceedings of ACM SIGMOD*, 2002, pp. 240–251.

Techniques for discovering keys, FKs, and FDs purely from data values without schema metadata. Exemplifies pure data-driven discovery requiring switching between statistical, semantic, and structural rule types.

---

## 4. Functional Graphs and Random Mappings (2000–2025)

### Flajolet-Odlyzko Framework and Extensions

**Flajolet, P. and Sedgewick, R.** *Analytic Combinatorics.* Cambridge University Press, 2009.

Definitive 800+ page treatise on generating function analysis of combinatorial structures. Chapter VII addresses mappings and functional graphs with closed-form expressions for component counts, cycle lengths, and tree heights. The symbolic-analytic pipeline directly applies to counting and characterizing schema traversal patterns.

**Flajolet, P. and Odlyzko, A.M.** "Random Mapping Statistics." *Advances in Cryptology – EUROCRYPT '89*, LNCS 434, Springer, 1990, pp. 329–354.

Seminal paper analyzing ~20 characteristic parameters of random mappings. Establishes expected cyclic points √(πn/2), expected components (1/2)log n, and expected tail length √(πn/8). Provides exact formulas for key structural parameters essential for characterizing how inference rules partition schema elements into basins of attraction.

**Aldous, D. and Pitman, J.** "The Asymptotic Distribution of the Diameter of a Random Mapping." *Comptes Rendus de l'Académie des Sciences, Paris, Série I* 334: 1021–1024, 2002.

Characterizes full limiting distribution of random mapping diameter as functional of reflecting Brownian bridge. The diameter represents maximum traversal depth—critical for understanding worst-case schema inference algorithm behavior.

### Random Graph Phase Transitions

**Janson, S., Łuczak, T., and Ruciński, A.** *Random Graphs.* Wiley-Interscience, 2000.

Comprehensive treatise with foundational Erdős-Rényi phase transition theory at edge density n/2. Phase transition theory explains how schema complexity changes as inference rule density increases—near the critical point, small rule density changes dramatically alter connected structure.

**Łuczak, T., Pittel, B., and Wierman, J.C.** "The Structure of a Random Graph at the Point of the Phase Transition." *Transactions of the American Mathematical Society* 341: 721–748, 1994.

Characterizes component structure precisely at phase transition, showing complex components have size O(n^{2/3}). Provides guidance for algorithm design when schema graphs approach critical density threshold.

**Flajolet, P., Knuth, D.E., and Pittel, B.** "The First Cycles in an Evolving Graph." *Discrete Mathematics* 75: 167–215, 1989.

Analyzes when first cycles appear as edges are added, proving expected cycle length proportional to n. Understanding cycle emergence in schema dependency graphs is crucial—cycles indicate recursive definitions or circular inference chains requiring special handling.

### Directed Graphs and Component Structure

**Cooper, C. and Frieze, A.M.** "The Size of the Largest Strongly Connected Component of a Random Digraph with a Given Degree Sequence." *Combinatorics, Probability and Computing* 13: 319–337, 2004.

Extends giant component analysis to directed graphs with specified degree sequences, establishing "bow-tie" structure. Schema graphs are inherently directed (inference rules have source→target structure)—this paper provides theory for analyzing strongly connected schema clusters.

**Hansen, J.C. and Jaworski, J.** "Random Mappings with Exchangeable In-Degrees." *Random Structures & Algorithms* 33: 105–126, 2008.

Generalizes random mapping theory to exchangeable degree distributions (not uniform assignment). Schema elements rarely have uniform connectivity—some attributes are referenced more frequently. This model better captures realistic schema topology.

**Hansen, J.C. and Jaworski, J.** "Structural Transition in Random Mappings." *Electronic Journal of Combinatorics* 21: Article P1.18, 2014.

Characterizes transitions in random mappings with in-degree constraints, showing continuous interpolation between permutation and general mapping behavior. Different inference rule types impose different connectivity constraints—this paper shows how mixing constrained and unconstrained mappings affects global structure.

### Discrete Dynamics and Basin Structure

**Wuensche, A.** "Basins of Attraction of Cellular Automata and Discrete Dynamical Networks." *Encyclopedia of Complexity and Systems Science*, 2nd Edition, Springer, 2017.

Comprehensive treatment of basin-of-attraction analysis in discrete dynamical systems with algorithms for computing pre-images and reverse dynamics. Schema inference can be viewed as discrete dynamics where states are schema configurations—basin structure determines which initial schemas converge to equivalent canonical forms under rule iteration.

**Pittel, B., Spencer, J., and Wormald, N.C.** "Sudden Emergence of a Giant k-Core in a Random Graph." *Journal of Combinatorial Theory, Series B* 67: 111–151, 1996.

Shows giant k-core (minimal degree ≥k subgraph) appears discontinuously at c_k·n/2 edges. The k-core represents "stable" schema structure—attributes maintaining at least k inference connections. Sudden emergence indicates schema complexity thresholds.

### Modern Perspectives and Graph Entropy

**Frieze, A. and Karoński, M.** *Introduction to Random Graphs.* Cambridge University Press, 2016.

Modern textbook with strong algorithmic emphasis covering phase transitions, connectivity, and random digraphs. Provides complexity bounds for detecting graph properties essential for practical schema analysis tools.

**Dehmer, M. and Mowshowitz, A.** "A History of Graph Entropy Measures." *Information Sciences* 181: 57–78, 2011.

Comprehensive survey of graph entropy from information-theoretic definitions through spectral measures. Graph entropy quantifies schema structural complexity—high-entropy schemas are harder to normalize; low-entropy indicates regular, predictable structure.

**van der Hofstad, R.** "Percolation and Random Graphs." Lecture Notes, TU Eindhoven, 2024 revision.

Unified treatment connecting percolation on infinite graphs with finite random graph phase transitions. Percolation models schema attribute "activation" or inference reachability—phase transition determines when local schema information percolates to global understanding.

---

## Cross-Cutting Synthesis: The Multi-Rule Tunneling Framework

The literature across these four domains converges on a unified theoretical foundation for multi-rule tunneling:

**From multiplex network theory**: The same node set (database tables/columns) can exhibit fundamentally different connectivity patterns across layers defined by distinct edge semantics (FK relationships, semantic similarity, cardinality constraints). Structural properties **emerge from layer combinations** that are invisible in any single layer (De Domenico 2015, 2023).

**From dependency theory**: Multiple dependency types (FDs, CFDs, ODs, INDs, DCs) each partition schemas differently. The **35+ relaxed FD variants** (Caruccio 2016) demonstrate the rich space of rule types available for tunneling. Hybrid algorithms like HyFD show that **combining inference strategies** synergistically improves discovery.

**From schema reverse engineering**: The most successful approaches (Cupid, HoPF, ML-based FK discovery) explicitly **combine multiple evidence types**. No single heuristic suffices—practical accuracy requires multi-rule integration.

**From functional graph theory**: Schema dependency graphs decompose into cycles with attached trees. **Phase transitions** at O(n) rule density cause dramatic structural changes. Basin-of-attraction analysis reveals which initial configurations converge under rule iteration.

Together, this literature establishes that **switching between inference rule interpretations**—multiplex layer traversal—is both theoretically grounded and practically necessary for discovering hidden schema structure. The tunneling metaphor captures the essential insight: different rule types provide different "views" into the same underlying structure, and systematic traversal across these views reveals the complete schema architecture.