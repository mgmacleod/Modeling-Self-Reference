Felt like I'd leave this to you and had already done the E.O.S. protocol just prior to this follow-up question:

One last thing for my own sanity - I'm only human and can only be good at so many things - but I've noticed you repeatedly assert a sort of 'obviousness' to the theoretical work that is derived from graph theory.
Am I just exploring a well-explicated area of mathematics and having the 'moments of wonder' because it's my first time here?
By which I mean, am I just recreating already existing work? And if yes, shouldn't we find and explicitly pull in such work as reference material?




You’re not crazy for feeling wonder here. Two things can be true at once:

some of the foundational scaffolding you’re using really is classical / well‑explicated, and
the specific phenomenon you’re seeing (Wikipedia + ordered prose links + fixed-N successor rule + phase-transition‑like behavior) is not something I’d assume is “already done” in exactly this form.
What parts are “standard math” (you’re rediscovering known lemmas)
These are genuinely “textbook” once you name them:

Functional graph structure: a deterministic map on a finite set decomposes into disjoint components, each with a directed cycle and in-trees feeding it. (Sometimes called a functional digraph or random mapping model when studied probabilistically.)
Eventual periodicity / cycle detection: “iterate until repeat or halt” is Floyd/Brent territory.
Basin labeling with path compression: the “compute terminal for each node; memoize; shrink remaining work” idea is standard dynamic programming on functional graphs.
Multiplex / multilayer graphs: modeling (node,rule) and allowing layer-switches is a known graph formalism (multiplex networks / multilayer networks).
So yes: the claims like “you can’t map a basin without a terminal,” “basins partition,” “labeling shrinks the search space,” etc. are not novel mathematically.

What parts are likely not “already solved” in your exact setting
This is where you’re plausibly in new territory (or at least uncommon combinations):

The specific successor rule f 
N
  defined by the Nth ordered prose link is an idiosyncratic, data-dependent dynamical system, not the usual “pick a random outgoing edge” model.
The empirical phase transition curve you found (62× rise at N=5, 112× collapse at N=9, depth power-law with exponent ~2–3, extreme trunk concentration) is a concrete phenomenon about Wikipedia’s topology coupled to this rule. I wouldn’t assume there’s prior literature stating “Nth prose link induces a sharp discrete phase transition on Wikipedia in exactly these ranges.”
The “tunneling” idea, as you mean it (systematically switching N / rule mid-walk to reveal latent structure), resembles known multilayer navigation ideas—but the application and the particular traversal rules may be new.
So: you are almost certainly reusing known mathematics, but you’re not necessarily recreating someone’s full result end-to-end.

Should you explicitly pull in references?
Yes—because it helps with:

vocabulary (so future readers stop reinventing definitions),
credibility (reviewers/peers can locate the known parts),
and focus (you can reserve “novelty” claims for the empirical discoveries + specific coupling mechanisms).
A practical way to do it without derailing the project:

Reference buckets to add

Functional graphs / mappings: decomposition into cycles + in-trees; basin terminology.
Random mapping model (optional): baseline expectations for cycle lengths / basin sizes if f were random; useful contrast.
Multilayer / multiplex networks: formalism for (node,layer) and inter-layer edges.
Percolation / phase transitions on networks: you’re observing a sharp transition in reachable mass vs a parameter (N); even if the mechanism is different, the analytic language is the same.
Web graph / Wikipedia graph studies: degree distributions, bow-tie structure, strongly connected core, etc.—this provides “priors” for why your rule might couple strongly at certain thresholds.
What I recommend (lightweight, high-value)
If you want, when you’re back (or Matt is), I can:

add a short “Related Work / Known Math” section to the theory docs (and/or n-link-analysis docs),
with names of the concepts (functional digraphs, random mapping model, multiplex networks, percolation),
and placeholders for citations to fill in once you decide how formal you want to be.
I didn’t fetch external sources in this session (to avoid guessing at exact papers), but the honest answer is: yes, parts of this are classical, and yes, it’s worth explicitly importing that literature—while still leaving plenty of room for your genuinely surprising empirical findings.

