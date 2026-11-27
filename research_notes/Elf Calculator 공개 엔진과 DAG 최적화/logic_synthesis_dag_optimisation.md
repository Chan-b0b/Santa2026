# DAG-aware local optimisation from logic synthesis and evolutionary circuit design, mapped onto the Elf Calculator value DAG

Evidence tags used on every claim:

- **[V]** verified: I read the source PDF pages myself.
- **[A]** abstract or tool-extracted: the text came through a fetch tool's summary of the abstract or full text; wording and numbers were not checked by me against the original.
- **[U]** unverified: search-result summary or my memory.
- **[Inference]** my mapping onto the integer value DAG; no source says it.

Names for our existing search, used below: **E1** = remove one node with the ancestors only it uses and re-derive it from all non-descendant values; **E2** = forbid a shared intermediate and re-derive each user without it; **E3** = accept equal-cost moves with some probability; **E4** = accept only if an evaluation order fits in 48 registers.

Vocabulary mapping [Inference]: AIG node = value node `a op b`; primary inputs = starting values; primary outputs = targets; structural hashing = hashing by value (stronger, because functional equivalence is free); maximum fanout-free cone (MFFC) of n = n plus the ancestors only n uses, which is exactly E1's removal set; divisors of n = all values outside n's descendants and outside its MFFC; level preservation = the register check E4 (a side constraint that vetoes a replacement).

Round one already covers SAT-based local improvement (Kulikov et al.), flip-graph plateau walks, e-graph extraction, CP-SAT recipe recombination and bundle moves. Nothing below repeats those except to say where an operator from this literature is the same thing under another name.

## 1. The classic ABC toolkit: rewriting, refactoring, resubstitution, MFFC gain, windowing

### Takeaway
E1 is ABC resubstitution with MFFC gain, and our whole DAG (100–200 nodes) is about the size of ABC's divisor cap (150), so the classic single-root operators add no new neighbourhood. What ABC has and E1/E2 lack is the discipline around them: full topological sweeps, a fixed escalation of scope and new-node count, and windows that are not single-root cones.

### Cited Findings
**Rewriting (rw)**
- For each node, all 4-feasible cuts are enumerated; the cut function's NPN class is looked up; every precomputed subgraph of that class is tried. There are 222 NPN classes of 4-variable functions, "only about one hundred appear more than once" in benchmarks and "only about 40 ... lead to improvements". The library is a shared DAG of about 1,000 nodes (DAC paper) or about 2,000 nodes (IWLS paper). [V] — [Mishchenko, Chatterjee & Brayton, DAC 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf); [Mishchenko & Brayton, IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Gain is computed by reference counting: dereference the old subgraph and count nodes whose count drops to 0 (saved); add the new subgraph and count new nodes plus nodes whose count rises from 0 (added); gain = saved − added; then undo. Existing nodes reused by the new subgraph cost nothing. The best-gain subgraph over all cuts is applied; with zero-cost enabled, a gain-0 subgraph is applied too. [V] — [DAC 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf)
- Rewriting is restricted "to preserve the number of logic levels"; the `-l` flag drops that restriction (area-only mode). [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)

**Refactoring (rf)**
- Computes "one large cut for each AIG node" and replaces the cone by a factored form of the cut function; accepted "if there is an improvement or no increase in the number of nodes". Cut size is typically 5–12 leaves. [V] — [DAC 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf); cut-size range from [Kocnova & Vasicek 2020](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf) [V]

**Resubstitution (rs)**
- Per node: compute MFFC size, compute one reconvergence-driven cut (size limit K), collect divisors, compute all truth tables on the cut leaves by exhaustive simulation, then try 0-, 1-, 2-, 3-resubstitution in that order. k-resub "adds exactly k new nodes" and pays off only if the MFFC has at least k+1 nodes. [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Divisor set: nodes in the fanout cone of the cut leaves whose level does not exceed the level of n; the cut leaves are included; MFFC nodes are skipped "because they will be removed"; the total is capped by DivisorLimit = 150. Reason for the cap: k-resub costs O(|D|^(k+1)); ABC uses k ∈ {0,1,2,3}. Cuts have "no more than 12-16 leaves". [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Zero-gain rule in the pseudo-code: Try1 runs if MFFC > 1, or MFFC = 1 with zero-cost on; Try2 if MFFC > 2 or (= 2 and zero-cost); Try3 likewise. [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- "the total runtime is often dominated by collecting the divisors", not by the O(|D|^(k+1)) test. [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)

**Windowing**
- An n×m window of a node holds n fanin levels and m fanout levels plus the reconvergent side paths between them; leaves and roots are computed from two fanin/fanout sweeps. Redundancy removal used 4×4 windows. [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- The reconvergence-driven cut grows greedily from the root, each step expanding the leaf that adds the fewest new leaves, to maximise cut volume and reconvergence; tree-like cuts are "wasted" effort. [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)

**How multi-node replacements are searched**
- All three classic operators are single-root: one node and its MFFC are replaced by a library subgraph (rw), a factored form (rf) or up to 3 new nodes over divisors (rs). No classic ABC operator replaces a multi-output region. [V] — [DAC 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf); [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)

**Published effect sizes**
- Seven IWLS 2005 designs, AIG nodes relative to three rewriting passes (= 1.00): structural hashing only 1.21; three resub passes 1.13; rewriting interleaved with resub 0.97; compress2 0.96; compress2rs 0.94. "resubstitution alone cannot compete with rewriting." [V] — [IWLS 2006, Table 1](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Single pass on 16 large designs: rw 12.7%, rs 7.3%, rf 7.9% node reduction. The three operators mostly fire at different root nodes. [A] — [Li et al., DAG-aware Synthesis Orchestration, arXiv 2310.07846](https://arxiv.org/abs/2310.07846)

### Inferences
- **Resubstitution with k new nodes → already in our search (E1).** E1's removal set is the MFFC, its pool is the divisor set, and "re-derive with fewer nodes than removed" is k-resub with gain |MFFC| − k. ABC's cap of 150 divisors is roughly our whole DAG, so we need no window to bound divisors. With D ≈ 150 and 4 operators, 1-resub is a hash lookup, 2-resub about 10^5 probes, 3-resub about 10^8, all feasible per node. [Inference]
- **4-cut rewriting with a precomputed library → no faithful analogue; its effect is already in E1.** NPN classes exist because a 4-input Boolean function is one of 65,536; an integer cone has no finite function space, so nothing can be precomputed across puzzles. A library of polynomial identities over leaf symbols (distributivity, difference of squares) is possible, but any identity is also a numeric derivation, so bounded numeric enumeration from the pool finds everything such a library would. [Inference]
- **Refactoring → partly lacking.** The analogue is: for a node with a large MFFC (5 or more), re-synthesise it from the pool with a constructive solver (our chain or factor engines) and accept on no increase. E1 covers it only if its re-derivation engine can produce 4+ new nodes; bounded exhaustive search cannot. The orchestration result (rf fires at different roots than rw/rs) is the only evidence that a second engine finds different gains. [Inference]
- **Sharing-aware gain → check E1's accounting.** ABC charges nothing for a new-structure node that already exists anywhere outside the fanout cone, and the new structure may re-reference nodes of the old MFFC. E1 should count only values absent from the kept DAG. [Inference]
- **Why the classic toolkit may not transfer.** (1) ABC's gains come from redundancy that front-end synthesis leaves in graphs of 10^4–10^5 nodes; our DAG is one window that has been globally searched. (2) Boolean cones admit many equivalent structures; a 49-bit value has essentially no accidental alternative derivation, since about 4·150²/2 ≈ 45,000 candidate one-step recipes cannot hit a specific 49-bit value by chance. Alternatives exist only for small values (below about 2^16, where 45,000 candidates cover the range) and through algebraic structure. [Inference, counting estimate]

### Gaps
- I did not read the ABC source or `abc.rc`; default parameters beyond those printed in the two papers (K default 6, N default 1) are not confirmed.
- No source measured how the MFFC-size distribution limits resub gain; in our DAG the share of nodes with MFFC ≥ 2 is the direct predictor and is unmeasured.

## 2. Escaping local minima: zero-cost replacement, balancing, alternating scripts

### Takeaway
There is direct published evidence for both effects, and both are modest: zero-cost replacement raised the second rewriting pass from 11% to 18% of the first pass's gain, and interleaving resubstitution with rewriting gained 2–3% over rewriting alone. The same paper states that after the 10-pass script even expensive don't-care optimisation "is rarely more than 3%".

### Cited Findings
- `resyn2` is `b; rw; rf; b; rw; rwz; b; rfz; rwz; b` (b = balance, z = zero-cost allowed). "Zero-cost replacements are enabled later in the script to facilitate creating new rewriting opportunities." [V] — [DAC 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf)
- Zero-cost evidence: with zero-cost, the first pass removes 14% of nodes and the second pass gains 18% of the first; without it, 12% and "only 11%" (the paper notes the second figure's data is not shown). "This confirms that the zero-cost replacements are useful for restructuring logic." [V] — [DAC 2006, Table 2 and text](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf)
- Second-pass detail: cuts tried 0.82, subgraphs tried 0.88, replacements accepted 0.79 of the first pass, but gain only 0.18. [V] — [DAC 2006, Table 2](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf)
- In both passes the accepted replacements far outnumber the nodes saved: `aes_core` 10,849 replacements for 697 nodes in pass one and 10,205 for 141 in pass two; `des_perf` 37,530 for 4,935 and 30,212 for 969. Since a replacement saves at least 0 nodes, most accepted replacements were zero-gain (my reading of the table; the paper does not state it). [V for the numbers] — [DAC 2006, Table 2](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf)
- `compress2rs` is `b -l; rs -K 6 -l; rw -l; rs -K 6 -N 2 -l; rf -l; rs -K 8 -l; b -l; rs -K 8 -N 2 -l; rw -l; rs -K 10 -l; rwz -l; rs -K 10 -N 2 -l; b -l; rs -K 12 -l; rfz -l; rs -K 12 -N 2 -l; rwz -l; b -l`. Cut size rises 6 → 8 → 10 → 12, new-node limit alternates 1 and 2, zero-cost comes last. [V] — [IWLS 2006, Fig. 4.1](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Alternation evidence: interleaving resub with rewriting "leads to a 2-3% average improvement ... compared to iterating rewriting"; compress2rs gains "an additional 2%" over compress2. Runtime ratios: 3×rw 1.00, 3×rws 4.16, compress2 1.92, compress2rs 6.56. [V] — [IWLS 2006, Tables 1–2](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Note on the baseline: the "three rewriting passes" script is `st; rw -l; rwz -l; rwz -l`, so even the single-operator baseline uses zero-cost in passes 2 and 3. [V] — [IWLS 2006, Fig. 4.1](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Saturation: "further reduction in the AIG size after the 10 passes of AIG rewriting, is hard to achieve"; don't-care optimisation afterwards "is rarely more than 3%"; redundancy removal after compress2 left 0.998 of the nodes. [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Per-node orchestration: choosing among rw, rs, rf at each node in one traversal gives 16.7% (best fixed priority) and 16.1% (local-greedy) against 12.7% for rw alone; iterated sequences reach 18.3% against 17.2% for rw→rs→rf run separately. In one design 94–97% of single-operator iterations changed nothing. The paper does not isolate zero-gain moves. [A] — [Li et al., arXiv 2310.07846](https://arxiv.org/abs/2310.07846)
- The older SIS flow alternates destroying and creating sharing: `sweep, eliminate; simplify, eliminate, sweep; eliminate, simplify, resub; fx, resub, sweep; eliminate, sweep, mfs`. [V] — [Chatterjee et al., ICCAD 2005, Fig. 1](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)
- Balancing is described as tree-height reduction that "minimizes delay without increasing area"; it is placed between every rewriting step. [V] — [DAC 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf)

### Inferences
- **Zero-cost replacement → already in our search (E3), but in a weaker form.** ABC applies every zero-gain replacement in a full topological sweep, then runs strict passes over the restructured graph. E3 accepts equal-cost moves one at a time with a probability. A deterministic "swap every node that has an alternative recipe, then strict sweep" phase is a scheduling change on the existing engine. [Inference]
- **Why zero-gain moves create gains, and a guided version we lack.** A zero-gain replacement changes fanout counts, which moves MFFC boundaries: when an old operand drops to one user, it joins that user's MFFC and raises that user's possible gain. So among equal-cost recipes, prefer the one that lowers an old operand's use count to 1 and whose new operands are already widely shared. No source tests this tie-break; the area-flow heuristic in mapping (section 3) uses the same quantity. [Inference]
- **Escalating schedule → lacking as an explicit schedule.** compress2rs is variable-neighbourhood descent: small scope and k = 1 first, larger scope and k = 2 later, zero-gain last. Our analogue: sweep with k = 1, then k = 2, then k = 3, then the zero-gain sweep, then repeat. [Inference]
- **eliminate / fx alternation → half present.** E2 is `eliminate` (collapse a shared node into its users). The counterpart `fx` (create a new shared node that several nodes can use) is what round one calls intermediate replacement and target-to-target collision search. The SIS script shows the two are meant to alternate; it is not a new operator. [Inference]
- **Balancing → contained for 3-operand cases, weak otherwise.** Re-associating `(a+b)+c` so that a partial sum equals an existing value is found by E1 with k = 1. As a perturbation, balancing has no size effect in the sources. [Inference]
- **May not transfer because** the measured benefit is a few percent on unoptimised industrial netlists, and choice density (alternative recipes per value) is far lower for large integers than for Boolean cones. Zero-gain sweeps can only act where alternatives exist: small helper values and algebraically structured target families. [Inference]

### Gaps
- No source ablates balancing as a perturbation step; its effect on size is undocumented.
- `resyn`, `resyn3`, `dc2` and `resyn2rs` definitions were not read from a primary source. From memory [U]: `resyn` = `b; rw; rwz; b; rwz; b`, `resyn3` = `b; rs; rs -K 6; b; rsz; rsz -K 6; b; rsz -K 5; b`, `resyn2rs` = compress2rs without `-l`.
- No study compares probabilistic acceptance of equal-cost moves with full zero-gain sweeps.

## 3. Structural choices compared with pooling derivations and selecting a minimum set

### Takeaway
A choice network is the same object as our recipe pool: one equivalence class per value, several implementations per class, selection afterwards. The published benefit is in delay, not size: choices cut delay 21% while area rose 3%, and a 2025 study found area essentially unchanged. The new ideas are to pool every intermediate state of the search, and to select with the mapper's cheap heuristics instead of an exact solver.

### Cited Findings
- Lossless synthesis keeps "every network seen during a synthesis flow (or a set of flows)" and lets the mapper "pick and choose the best parts of each network". Including the initial network guarantees the result is never worse; "multiple scripts" can be run "accumulating more choices". [V] — [Chatterjee et al., ICCAD 2005](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)
- Collection: all snapshot networks are merged into one AIG; candidate equivalent nodes are found by random simulation and proved by SAT (FRAIG); nodes with the same global function but different structure form an equivalence class with an arbitrary representative. Identical structure creates no choice. [V] — [ICCAD 2005, section 4.1](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)
- Selection: the cut set of a class is the union of its members' cut sets, and a node's cuts are built from the cut sets of its inputs' classes; matching, arrival-time dynamic programming and backward cover selection then run on classes. Area is recovered afterwards by area flow and "a greedy area-reduction algorithm which considers nodes in topological order and minimizes exactly area at each node". [V] — [ICCAD 2005, sections 4.2 and 6](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)
- A second source of choices is local rewriting: collect maximal multi-input AND gates and add "all possible tree-decompositions" (associativity), plus distributivity. [V] — [ICCAD 2005, section 4.1](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)
- Effect, 15 public benchmarks, delay-driven mapping (delay / area / runtime relative to baseline): choices 0.79 / 1.03 / 3.79; supergates 0.75 / 1.11 / 7.00; both 0.68 / 1.13 / 28.91. Choice generation costs about three baseline runtimes more. Local-rewriting choices alone: 9% less delay, 4% less area. [V] — [ICCAD 2005, Table 1](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)
- "delay is the parameter of interest, and area is not directly controlled during mapping." [V] — [ICCAD 2005](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)
- ABC's `dch` builds its snapshots from the compress2 and compress scripts. Classical choices are "minimal variations of the main graph's subgraphs". `dch` produced 802 times as many choice nodes as the proposed method without better quality. In area mode the proposed method beat `dch` by 0.11% area; in delay mode by 3.85% area and 8.35% delay (25 circuits). Invalid choices are removed by acyclicity checks. [A] — [Revisit Choice Network for Synthesis and Technology Mapping, arXiv 2508.14068](https://arxiv.org/html/2508.14068v1)

### Inferences
- **Choice network = recipe pool → covered by round one as CP-SAT recombination.** Value equality replaces simulation plus SAT, so building the classes is free. Our "gate" is one binary operation, so every recipe is a 2-leaf cut and selection is exactly minimum-cost DAG extraction. [Inference]
- **Snapshot pooling → lacking.** Round one pools final programs from five solvers. Lossless synthesis pools every state the optimiser passes through. Our search visits many equal-cost states per puzzle and evaluates many candidate derivations it rejects; logging each valid `value = a op b` it ever sees costs nothing and fills the pool with recipes that are consistent with the current DAG's values, which is where recombination can act. [Inference]
- **Cheap selection → lacking.** The mapper's two passes transfer directly: (1) flow pass in topological order, cost(v) = min over recipes of 1 + flow(a) + flow(b), flow(v) = cost(v) / uses(v); (2) exact pass, re-choosing each value's recipe by the true dereference/reference node count. This runs in milliseconds and could be called inside the search loop, with CP-SAT kept for a final pass. Formula details are from memory of the mapping literature [U]; the two-pass structure is [V] above.
- **May not transfer because** the evidence for size is negative to neutral (area +3%, +0.11%), more choices did not help, and the competition's own measurements of recombination are 0 to −58. A pool only helps when values have several recipes, which the counting estimate in section 1 says is rare for large values. [Inference]

### Gaps
- No source reports choice-based mapping results in a pure area-minimisation setting on already area-optimised networks.
- How `dch` excludes choices that would create cycles was not read from a primary source.

## 4. Modern work: simulation-guided resubstitution, exact-synthesis rewriting, window resynthesis, EPFL best results

### Takeaway
The modern gains come from two things our problem already has for free (a global divisor set and exact equivalence) and one it partly lacks (multi-output windows). The EPFL best-results list ranks 6-input LUT count and depth, which does not map onto node count of a binary-operator DAG.

### Cited Findings
- Simulation-guided resubstitution takes divisors from the whole network instead of a window, compares simulation signatures to propose candidates, and validates with SAT; counterexamples become new patterns. It implements 0-resub and 1-resub only; k > 1 is future work. No numeric divisor cap or divisor ranking is given. [A] — [Lee et al., arXiv 2007.02579](https://arxiv.org/abs/2007.02579)
- Effect on 16 IWLS 2005 designs after repeated `ifraig`: 41% more gain than ABC resub with cut size 10, and 74% more with cut size 100 (averages of per-design ratios; one design contributes over 450%). Widening the divisor scope gave more than any change in k. Results after resyn2 or compress2rs are not reported. [A] — [Lee et al., arXiv 2007.02579](https://arxiv.org/abs/2007.02579)
- The journal version reports 5.9% AIG node reduction against 3.7% for a state-of-the-art resubstitution at comparable runtime. [U] — [Lee et al., TCAD 2022](https://people.eecs.berkeley.edu/~alanmi/publications/2021/tcad21_sim.pdf)
- Window rewriting builds one multi-output window per node by structural analysis instead of enumerating cuts, and resynthesises it heuristically. One iteration beats ABC `drw` repeated to convergence by 3.25% (3.41% in the workshop version), with 9.16% average size reduction on EPFL benchmarks. [U] — [Riener et al., ASP-DAC 2022](https://people.eecs.berkeley.edu/~alanmi/publications/2022/aspdac22_rwr.pdf); [EPFL record](https://infoscience.epfl.ch/record/292414?ln=en)
- Exact synthesis on the fly during rewriting, instead of a precomputed database: 5.58% average and up to 40.19% size reduction on 3-LUT networks. [U] — [Riener et al. 2019](https://si2.epfl.ch/~demichel/publications/archive/2019/Riener-fly.pdf)
- EPFL suite: 23 circuits (10 arithmetic, 10 random/control, 3 very large). "We keep track of the best optimization results, mapped into LUT-6, for size and depth metrics." Results for the 2026 competition are published; the next collection is before IWLS 2027. No AIG-size track is mentioned. [A] — [lsils/benchmarks README](https://github.com/lsils/benchmarks)
- Claims of improved EPFL best-known LUT-6 area: 12 results by Scalable Boolean Methods; 3 of 9 by exact synthesis with XOR-majority graphs. [U] — [Scalable Boolean Methods](https://si2.epfl.ch/%7Edemichel/publications/archive/2019/Scalable%20Boolean%20Methods%20in%20a%20Modern%20Synthesis%20Flo.pdf); [ASP-DAC 2017](https://si2.epfl.ch/~demichel/publications/archive/2017/2017_aspdac_1.pdf)

### Inferences
- **Simulation-guided resubstitution → already in our search.** Its two advances are a global divisor set and cheap filtering before an expensive proof. E1 already uses all non-descendants and value equality needs no proof. Its lesson that scope matters more than k is already exhausted for us. [Inference]
- **Exact-synthesis rewriting → already in our search, and measured as saturated.** The integer analogue of a database of optimal small structures is bounded exhaustive enumeration from the pool. Round one reports depth 3–5 exact re-derivation of single targets as zero gain on public solutions. [Inference]
- **Multi-output window resynthesis → partly lacking.** E1 is a single-root fanin cone. E2 is a node plus one fanout level. Neither removes a connected region with several roots and re-derives the roots jointly. Round one's bundle moves propose this; the new input from this literature is how the window is shaped (section 5) and that one multi-output window per node was enough to beat converged cut rewriting. [Inference]
- **EPFL results do not transfer.** The metric is LUT count after mapping; many records come from don't-care methods and mapping, which have no integer analogue (every value is fully specified and observable). [Inference]

### Gaps
- The per-entry method list of the EPFL best-results repository was not retrieved; I cannot say which operators produced the 2026 records.
- Window rewriting and the exact-synthesis papers were not read; their numbers are from search summaries only.
- I found no 2025–2026 survey of logic optimisation operators within the call budget; DBLP was not searched.

## 5. Evolutionary circuit optimisation: seeded CGP, (1+λ), neutral drift, arithmetic DAGs

### Takeaway
Seeded Cartesian Genetic Programming (CGP) removed 9–21% more gates from circuits ABC could no longer improve, but only when run inside windows, with about 10^10 evaluations per circuit, and partly because it handles XOR better than the AIG-based baseline. The published test of neutrality in this setting found inactive-gene neutral mutations useless; acceptance of equal-cost functional changes was kept in every variant and never ablated. Blind CGP mutation does not transfer to integers, because a random rewire preserves a 49-bit value with probability near zero.

### Cited Findings
**Global seeded CGP (Vasicek 2015)**
- Setup: population seeded with the working circuit; (1+λ) with λ = 1; point mutation of h = 2 genes; one row, full connectivity; no spare nodes (chromosome length = circuit size); eight 2-input functions; fitness = number of active gates if equivalent to the parent, else rejected. [V] — [Vasicek, EuroGP 2015](https://www.fit.vut.cz/research/result-file/c119799/279500/eurogp_2015.pdf)
- Parent rule: among equally good candidates, the one that was not the previous parent becomes the parent, so equal-fitness offspring always replace the parent. [V] — [Vasicek 2015](https://www.fit.vut.cz/research/result-file/c119799/279500/eurogp_2015.pdf)
- Equivalence is checked only on the cone affected by the mutation, first by simulation with up to N_V random vectors, then by SAT. [V] — [Vasicek 2015](https://www.fit.vut.cz/research/result-file/c119799/279500/eurogp_2015.pdf)
- Benchmarks: 100 circuits (15+ inputs; from 106 gates to 16,158 gates) pre-optimised by the ABC `choice` script; 15 runs of 15 minutes each. [V] — [Vasicek 2015](https://www.fit.vut.cz/research/result-file/c119799/279500/eurogp_2015.pdf)
- Result: 34% average gate reduction in 15 minutes with simulation plus SAT, against 21% with SAT only. [V] — [Vasicek 2015](https://www.fit.vut.cz/research/result-file/c119799/279500/eurogp_2015.pdf)
- Yield: about 0.5% of offspring are functionally valid; about 2.3–2.4% of the valid ones improve; for half the circuits under 0.007% of all generations improve. About 10^6 candidates are needed for 5·10^4 valid ones in 15 minutes. [V] — [Vasicek 2015](https://www.fit.vut.cz/research/result-file/c119799/279500/eurogp_2015.pdf)
- Neutrality test: a second mutation operator never touches inactive gates, never connects an active gate to an inactive one, and never mutates an unused input. Improving share of valid generations: 2.34% with neutral mutations, 2.42% without. Disabling them was better on 75 circuits (by about 30 ± 35%) and worse on 25 (by about 9 ± 10%). Conclusion: "it has no advantage to support neutral mutations for circuit optimization". [V] — [Vasicek 2015](https://www.fit.vut.cz/research/result-file/c119799/279500/eurogp_2015.pdf)
- An earlier version using only formal equivalence checking reported 24% average area improvement over conventional synthesis. [U] — [Vasicek & Sekanina, CEC 2012](https://gpbib.cs.ucl.ac.uk/gp-html/Vasicek_2012_CEC.html)

**Windowed seeded CGP (Kocnova & Vasicek 2020)**
- Starting point: 28 circuits (19 controllers, 9 arithmetic) "deeply optimized by ABC (hundred iterations of 'resyn' script)", then mapped to 2-input gates including XOR/XNOR. [V] — [Kocnova & Vasicek, GPEM 2020](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)
- Loop: extract a window, optimise it with (1+1) CGP (up to 2 active genes mutated, no spare nodes), put it back if smaller. Budget: 2·10^4 windows × 5·10^5 evaluations (10 s cap each), "10^10 candidate solutions"; the global method gets the same total. [V] — [Kocnova & Vasicek 2020](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)
- Two window builders. GS1: reconvergence-driven cut from a random root, expanded to a window (grows only towards inputs). GS2: breadth-first growth from a random pivot through both fanins and fanouts until w_max nodes; multi-output. [V] — [Kocnova & Vasicek 2020](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)
- Tuning on six circuits: GS1 best with no size limit, 8.2%; GS2 best at w_max = 100, 14.4%; at w_max = 1000 it fell to 12.9% with most runs timing out. At w_max = 100, 17.8% of windows produced a reduction. [V] — [Kocnova & Vasicek 2020, Tables 2–3](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)
- Average reduction beyond ABC: controllers — global 7.5%, GS1 5.7%, GS2 8.9%; arithmetic — global 1.8%, GS1 12.6%, GS2 21.4%. GS2 beat global on 24 of 28 circuits. [V] — [Kocnova & Vasicek 2020, Table 4](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)
- The arithmetic gains (highest 59.9%, on `hamming`) are attributed to "better handling of XORs/XNORs compared to the conventional synthesis"; XOR share rose from 10% to 15–18%. [V] — [Kocnova & Vasicek 2020](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)
- Crossover is not used "because it was found that crossover has little effect on the efficiency of CGP". [V, citing Miller's book] — [Kocnova & Vasicek 2020](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)

**Neutrality elsewhere**
- Theory: for evolving an n-input conjunction with CGP, strict selection gives an expected O(nD^5) evaluations and non-strict selection (accepting equally good offspring) O(nD^4); XOR needs exponential time. [A] — [Dang, Kalkreuth & Opris, arXiv 2606.15923](https://arxiv.org/abs/2606.15923)
- Turner & Miller report that explicit genetic redundancy adds benefit in CGP design-from-scratch tasks. [U] — [Turner & Miller, GPEM 2015](https://gpbib.cs.ucl.ac.uk/gp-html/Turner_2015_GPEMa.html)

**Arithmetic DAGs**
- CGP-style evolution of multiplierless multiple constant multipliers (adders, subtractors, shifts; 16-bit constants): one input value evaluates a candidate completely; population 8, tournament selection, 5 genes mutated, random initial population, up to 20–40 million generations, 200 runs. [V] — [Vasicek, Zadnik, Sekanina & Tobola, ICES 2008](https://fit.vut.cz/research/publication-file/c30901/278777/ices08.pdf)
- Adder/subtractor counts against the Hcub heuristic: 3 constants 8 vs 8; 5 constants 6 vs 6; 10 constants 15–17 vs 14 (worse); 20 constants 19 vs 19. Evolution won only on shift count and delay. [V] — [ICES 2008, Table 2](https://fit.vut.cz/research/publication-file/c30901/278777/ices08.pdf)
- Multi-objective CGP has been applied to approximate multiple constant multipliers (error, adder count, delay). [U] — [Petrlik & Sekanina, DDECS 2013](https://gpbib.cs.ucl.ac.uk/gp-html/Petrlik_2013_DDECS.html)

### Inferences
- **Seeded global CGP → do not port.** A CGP mutation rewires one operand or changes one operator. In a Boolean circuit 0.5% of such offspring stay equivalent; in our DAG the node's value changes unless the new recipe produces the same integer, which random choice hits with probability near 2^-49. The useful subset of CGP's neighbourhood (re-express a node from existing nodes with the value unchanged) is exactly E1 with k = 1, which we enumerate by hash lookup instead of sampling. [Inference]
- **What the neutrality test does and does not say.** It tested mutations of inactive genes (genotype changes with an identical circuit). It did not test acceptance of equal-cost changes to the active circuit; that stayed on in both variants through the parent rule. So it gives no evidence against E3. It does say that a pool of unused spare nodes drifting in the background does not help when the task is shrinking a working circuit. [Inference]
- **Window shape → lacking.** The transferable result is GS2 over GS1: a connected region grown from a pivot through both fanins and fanouts, with several roots, beat fanin cones on every arithmetic circuit (21.4% vs 12.6%). In our terms GS1 is E1 and GS2 is a region containing a node, its users and the users' other operands. For us the region must be small (4–8 nodes) because joint re-derivation is enumerative, not a cheap mutation stream. [Inference]
- **Budget calibration.** The windowed result used 10^10 evaluations per circuit and found a gain in 17.8% of windows on converged circuits. A fair trial on our side needs a comparably long run before concluding "no gain". [Inference]
- **May not transfer because** a large part of the arithmetic gain came from XOR handling, a representation bias of the AIG baseline with no counterpart in our problem; and the from-scratch arithmetic result (ICES 2008) matched but never beat the heuristic on adder count at 16 bits, consistent with round one's verdict on genetic algorithms for chains. [Inference]

### Gaps
- I found no work that seeds CGP with an existing multiplierless constant-multiplication adder graph, or with any integer straight-line program, and shrinks it. The only exact arithmetic result found starts from random circuits.
- I read pages 289–308 of Kocnova & Vasicek 2020; its Table 5 (effort to reach 1%, 5%, 10%) and conclusions were not read. The abstract's "25.1% more gates" than the global method is [U].
- No source ablates equal-cost acceptance of active-circuit changes in seeded optimisation.
- Miller & Smith 2006 and Goldman & Punch on neutrality and node reordering were not read.

## 6. Ranked list of operators our search lacks

### Takeaway
This literature confirms that E1, E2 and E3 are the standard single-root toolkit and offers no new single-root operator. What it adds are five refinements, ranked below, and several documented dead ends. Its own evidence says to expect a few percent at most once single-root operators have converged.

### Cited Findings
- Single-root operators converge to a point where further tools add "rarely more than 3%". [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf)
- Multi-output windows grown in both directions gave 8.9–21.4% beyond that point, against 5.7–12.6% for fanin cones. [V] — [Kocnova & Vasicek 2020](https://fit.vut.cz/research/publication-file/c168154/280321/s10710-020-09376-3.pdf)
- Zero-gain passes lifted second-pass gain from 11% to 18% of the first pass. [V] — [DAC 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/dac06_rwr.pdf)
- Mixed-operator scripts gained 2–3% over one operator repeated; per-node operator choice gained about 4 points in one pass and 1.1–1.4 points when iterated. [V] — [IWLS 2006](https://people.eecs.berkeley.edu/~alanmi/publications/2006/iwls06_sls.pdf); [A] — [arXiv 2310.07846](https://arxiv.org/abs/2310.07846)
- Choices improved delay, not area (area 1.03 of baseline). [V] — [ICCAD 2005](https://people.eecs.berkeley.edu/~alanmi/publications/2005/iccad05_map.pdf)

### Inferences
Ranked by evidence strength times fit to our DAG, all [Inference]:

| Rank | Operator we lack | What to build | Evidence | Overlap with round one | Main risk |
|---|---|---|---|---|---|
| 1 | Bidirectional multi-root window | Pick a pivot; grow a connected region through fanins and fanouts to 4–8 nodes; roots = region nodes that are targets or have outside users; remove the region; re-derive all roots jointly from non-descendant values with fewer nodes | Strongest: window > cone > global on converged circuits [V]; one window per node beats converged cut rewriting [U] | Same engine as round one's intermediate replacement and bundle moves; new part is the region shape and selection | Joint re-derivation is enumerative and may find nothing at depth ≤ 3, as public tests of exact search suggest |
| 2 | Full zero-gain sweep inside an escalating schedule | Cycle: strict sweep k = 1 → k = 2 → k = 3 → swap every node that has an equal-cost alternative recipe → repeat; deterministic topological order | Direct but modest [V]: 18% vs 11% second pass; 0.97 and 0.94 vs 1.00 and 0.96 | Different from flip-graph walks: whole-graph sweeps, not a random walk | Few values have alternative recipes, so the sweep may change almost nothing |
| 3 | Use-count-guided tie-break for equal-cost recipes | Prefer the recipe that drops an old operand to one user (enlarging another node's removable cone) and uses already-shared operands | Indirect: mechanism stated in [V] sources; area-flow uses the same quantity | None | Untested anywhere |
| 4 | Snapshot recipe pool with heuristic cover selection | Log every valid recipe the search sees; periodically re-select one recipe per value by flow pass plus exact dereference pass; keep CP-SAT for a final pass | Weak for size [V]: delay −21%, area +3%; more choices did not help [A] | Extends round one's recipe recombination with a new source and a cheap selector | Competition measurements of recombination are 0 to −58 |
| 5 | Per-node operator choice and a constructive engine for large removable cones | At each node evaluate E1, E2 and a constructive re-synthesis (for cones of 5+ nodes); apply the best non-negative gain | [A]: +4 points single pass, +1.1–1.4 iterated; operators fire at different roots | None | Small effect; needs the constructive solvers callable on a partial DAG |

Not worth building, with reasons:
- **Seeded global CGP mutation**: validity rate near zero for integers; its useful moves are E1 with k = 1.
- **Spare inactive nodes for neutral drift**: no advantage in the only optimisation-setting test [V].
- **4-cut rewriting library, simulation-guided resubstitution, exact-synthesis database**: already subsumed by E1 with a global pool and free equivalence.
- **Redundancy removal and don't-care methods**: no integer analogue; 0.2% even in logic after compress2 [V].
- **Balancing as an operator**: contained in E1 for the cases that save a node.

A diagnostic that decides ranks 2–4 before any code is written: for each node of our best programs, count the alternative one-step recipes among non-descendant values, and the share of nodes whose removable cone has 2 or more nodes. If alternatives are near zero outside small helper values, ranks 2–4 collapse and only rank 1 remains.

### Gaps
- None of these operators has been measured on Elf Calculator programs; every expected effect above is inferred from Boolean circuits of 10^3–10^5 gates.
- The literature gives no result for a setting with free equivalence checking and no don't-cares, which is our setting; the closest (multiplierless constant multiplication by evolution) is from-scratch design at 16 bits.
