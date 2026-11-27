# Program synthesis, superoptimisation and learning-guided search for shortening multi-output straight-line arithmetic programs (Santa 2026 – Elf Calculator)

Research date: 2026-11-24. Scope: methods that are neither in `notes/research.md` nor in the project's "already tried" list. Nothing here was run on the competition data.

How each claim is labelled:

- **[V-text]** verified: I read the source's own text (PDF converted to text) and the claim matches it.
- **[V-fetch]** verified one step removed: the source page itself was fetched, but the facts were extracted by the fetch tool's summariser, so I did not check the wording character by character.
- **[S]** unverified: seen only in a search-result summary.
- **[Inference]** my own mapping onto the Elf Calculator problem. No source tests any of these methods on 40–60-bit integer straight-line programs.

---

## 1. Superoptimisation: Massalin, Bansal–Aiken, Souper, LENS, unbounded superoptimisation, STOKE

### Takeaway

Exact superoptimisers top out at roughly 3–12 instructions by enumeration and about 16 with window decomposition. STOKE's MCMC reached longer programs only because its cost function gives partial credit (bit-level Hamming distance over test cases, plus credit for a correct value in the wrong register), and it fails when that signal is deceptive. For this problem the family offers no search engine stronger than the short-window resynthesis and LNS already in place; the only transferable pieces are STOKE's two-phase design and its acceptance of temporarily invalid programs.

### Cited Findings

**STOKE (Schkufza, Sharma, Aiken, ASPLOS 2013)**

- Cost is `c(R;T) = eq(R;T) + perf(R;T)`. Because a theorem-prover check ran "well below 100" times per second, correctness is approximated on test cases: "we use the number of bits difference in live outputs (i.e., the Hamming distance) to measure correctness." [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)
- An "improved" correctness term rewards a correct or nearly correct value in the wrong register, with a small misplacement penalty `w_m`. With the strict version, "the strict version obtained a minimum cost which was only slightly superior to that obtained by a pure random search." The authors explain the gain as letting a candidate "simultaneously explore as many alternate computations as can be fit within a sequence of length ℓ." [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)
- Move set: four proposals on a fixed-length sequence with an `UNUSED` token. Opcode (replace an opcode with one of the same operand signature), Operand (replace one operand; immediates come from "a bag of predefined constants"), Swap (interchange two instructions), Instruction (replace with a random instruction or `UNUSED`). Parameters in Figure 11: p_c = 0.16, p_o = 0.5, p_s = 0.16, p_i = 0.16, p_u = 0.16, β = 0.1, ℓ = 50, 32 test cases per target. [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)
- Acceptance is the Metropolis ratio. The acceptance threshold is sampled first so test-case evaluation can stop early once the bound is exceeded. The emulator ran "just under 500,000" test-case executions per second. [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)
- Two phases share one search implementation. Synthesis starts from random instructions and uses only the correctness term. Optimisation starts from code known to be equivalent, uses both terms, and may "experiment with 'shortcuts' that (temporarily) violate transformation correctness." The split was introduced because a single-phase version "was rarely able to produce code competitive with expert handwritten code." [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)
- Scale: both phases ran on "40 dual-core 1.8 GHz AMD Opterons" with "budgets of 30 minutes". The headline result is an 11-instruction Montgomery multiplication kernel. [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)
- Failure mode: STOKE "is unable to synthesize a rewrite for three of the Hacker's Delight Benchmarks", each of which differs "by only a single bit from a simple yet completely incorrect alternative", so the cost has "no partially correct computations that can be hill-climbed". [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)

**Massalin and Bansal–Aiken (as summarised in the STOKE paper, a secondary source)**

- "Massalin reported being able to optimize instruction sequences of up to length 12, however to do so, it was necessary to restrict the set of enumerable opcodes to between 10 and 15." [V-text, secondary] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)
- Bansal and Aiken enumerate x86 superoptimisations offline into a database, "exploiting symmetries between programs that are equivalent up to register renaming", for "input code sequences of at most length 6 and producing code sequences of at most length 3"; the database is then applied repeatedly along a sliding window. [V-text, secondary] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)

**LENS and GreenThumb (Phothilimthana, Thakur, Bodik, Dhurjati, ASPLOS 2016)**

- Prior enumerative search "could only synthesize up to three ARM instructions within an hour"; stochastic search handled larger programs but "can get stuck at local minima"; symbolic (solver-based) search was the slowest. [V-text] — [ASPLOS'16 PDF](https://thakur.cs.ucdavis.edu/assets/pubs/mangpo_thakur_ASPLOS16.pdf)
- LENS is bidirectional enumeration (forward from inputs, backward from outputs) that refines the test-case equivalence abstraction only where candidates connect. It raised solved benchmarks "from 11 to 20 (out of 22)" with an "11x reduction on the search time on average", yet "still cannot synthesize ARM code with more than five instructions or GreenArrays (GA) code with more than 12 instructions." [V-text] — [ASPLOS'16 PDF](https://thakur.cs.ucdavis.edu/assets/pubs/mangpo_thakur_ASPLOS16.pdf)
- Context-aware window decomposition optimises a window against the exact pre- and post-context instead of in isolation, picks windows at random, and repeats until no window improves. It synthesised "an optimal (or nearly optimal) ARM program of 16 instructions within 10 minutes." [V-text] — [ASPLOS'16 PDF](https://thakur.cs.ucdavis.edu/assets/pubs/mangpo_thakur_ASPLOS16.pdf)
- A cooperative superoptimiser runs enumerative, stochastic and symbolic instances that exchange their best program; it raised consistently solved benchmarks "from 23 to 29 (out of 32) over using the enumerative search alone." [V-text] — [ASPLOS'16 PDF](https://thakur.cs.ucdavis.edu/assets/pubs/mangpo_thakur_ASPLOS16.pdf)

**Souper, dataflow pruning, unbounded superoptimisation, learned proposals**

- Dataflow-based pruning for Souper (Mukherjee, Kant, Liu, Regehr, OOPSLA 2020) discards partial candidates with holes using forward and backward dataflow analyses; reported 2.32x speedup and 65% fewer solver calls over 269,113 synthesis problems. [S] — [paper PDF](https://users.cs.utah.edu/~regehr/dataflow-pruning.pdf); Souper itself: [arXiv 1711.04422](https://arxiv.org/pdf/1711.04422)
- Unbounded superoptimisation (Jangda and Yorsh, Onward! 2017) moves the search into the SMT solver with an encoding whose size does not depend on candidate length; evaluated only on "small but tricky" examples, and it can stop with a correct but non-optimal answer. [S] — [Onward! 2017 record](https://qmro.qmul.ac.uk/xmlui/handle/123456789/29154)
- Bunel et al. (ICLR 2017) replace STOKE's uniform proposal distribution with one learned by reinforcement learning and report outperforming STOKE on Hacker's Delight and generated programs. No numbers were retrieved. [S] — [arXiv 1611.01787](https://arxiv.org/pdf/1611.01787)

**Independent head-to-head on a hard synthesis task (Ullrich and Hack, CGO 2025)**

- For branchless sorting kernels, STOKE "is unable to synthesize a correct program for n = 3. Also the warm-start optimization mode fails to find a program of optimal length." SMT-based synthesis needed 25–97 minutes for n = 3, and none of the solver-based or stochastic contenders produced an n = 4 kernel within a one-week timeout. [V-text] — [paper PDF](https://compilers.cs.uni-saarland.de/papers/ullrich_sorting_kernels.pdf)

### Inferences

- **STOKE-style MCMC. Mapping:** fixed-length slot array with `UNUSED`; moves change an operator, re-point an operand to another register, swap, or insert/delete; cost = length + λ·(repair distance of each missing target) + penalties for `value_limit` and register overflow. The "right value, wrong register" credit is automatic here because a target may appear in any register. **Expected benefit:** low. Elf programs take no inputs, so the test-case signal that made STOKE work degenerates to "is the 39-bit target present", which is exactly the deceptive, plateau-shaped cost on which STOKE failed. The only usable gradient is a repair distance (0 if present, 1 if `a op b` over the pool hits it, 2 by a hash join), and that is what the existing reduction search already computes. **Cost:** 3–5 days; CPU only. **Why it may not transfer:** AlphaDev-S and the sorting-kernel study both show warm-started stochastic search stays in the basin of its seed (section 4), and the public report in `research.md` of 0–1 instruction gains from local search at 132.5k points the same way.
- **What is worth lifting from STOKE:** (a) allow LNS/annealing to pass through invalid states with a penalty rather than repairing after every move; (b) sample the acceptance threshold first so evaluation can stop early. Both are small changes to the existing LNS, not a new method.
- **Bansal–Aiken lookup tables. Mapping:** a canonicalised database keyed on symbolic window semantics. Because Elf values are concrete, a window only has to reproduce numbers, which is a weaker requirement than symbolic equivalence; exhaustive resynthesis on concrete values (already tried) dominates a symbolic table. **Not recommended.**
- **LENS. Mapping:** bidirectional enumeration equals the existing meet-in-the-middle; the reduced-bitwidth and selective-refinement tricks address test-case equivalence, which does not exist for constant programs. The only new element is the **cooperative portfolio**: let LNS, window resynthesis and the constructive solvers share one incumbent per puzzle during the run instead of merging only at the end. **Expected benefit:** small; **cost:** 1–2 days.
- **Dataflow / abstract-interpretation pruning. Mapping:** prune "can target t be reached from pool P in d more steps" using magnitude bounds and reachable residue sets modulo small numbers. With pools of 30+ values and three ring operations, residue sets saturate after one or two steps, so pruning power is near zero beyond depth 1–2, where hash joins are already exact. **Not recommended.**
- **Solver-based synthesis (Souper, unbounded superoptimisation, Brahma in section 2).** Multiplication of two 60-bit unknowns is the hard case for bit-blasting; together with the sorting-kernel timings above and the 12-bit proof limit already recorded in `research.md` §4.7, whole-puzzle encoding is not credible. Use solvers only for *selection* over a precomputed candidate set (section 3).

### Gaps

- Massalin (1987), Bansal–Aiken (2006) and Souper were not read in the original; their scale figures come from the STOKE paper or search summaries.
- Exact numbers for unbounded superoptimisation and for learned-proposal STOKE were not retrieved.
- No source applies any superoptimiser to input-free (constant-only) integer programs.

---

## 2. Enumerative and bidirectional synthesis: observational equivalence, top-down plus bottom-up, component-based synthesis

### Takeaway

The synthesis literature's central tricks (deduplicate by observed values, propagate the goal backward through inverse semantics, prune partial programs by abstract interpretation) are the same ideas as the project's duplicate-set pruning, meet-in-the-middle and `v = q·b ± c` reduction. I found nothing specific to integer targets beyond what is already implemented; the one adjacent literature with a transferable result is linear straight-line programs over GF(2), where randomised restarts of a distance-guided greedy set records.

### Cited Findings

- Deduplication by behaviour is what makes enumeration scale: in the sorting-kernel A* search, "The most important pruning technique is the deduplication of equivalent programs"; for n = 4 it enumerated 4.9·10^9 programs while skipping 16.8·10^9 semantically identical ones. [V-text] — [Ullrich & Hack](https://compilers.cs.uni-saarland.de/papers/ullrich_sorting_kernels.pdf)
- Duet (Lee, POPL 2021) combines bottom-up enumeration of components with top-down propagation that derives sub-goals for missing subexpressions through inverse maps. [S] — [POPL 2021 page](https://popl21.sigplan.org/details/POPL-2021-research-papers/54/Combining-the-Top-down-Propagation-and-Bottom-up-Enumeration-for-Inductive-Program-Sy)
- Simba (Yoon, Lee, Yi) alternates forward and backward abstract interpretation to reject partial programs that no completion can satisfy. [V-fetch, abstract] — [arXiv 2304.10768](https://arxiv.org/abs/2304.10768). Reported as solving 519 of 544 bit-vector problems against 456 for Duet and 409 for Probe. [S] — [arXiv 2304.10768 PDF](https://arxiv.org/pdf/2304.10768)
- Oriented metrics (Meyer and Tepe, POPL 2026) restrict bottom-up enumeration to a ball around the target under a direction-aware distance and report "more than an order of magnitude" improvement on string and bit-vector domains. [V-fetch, abstract] — [arXiv 2511.02491](https://arxiv.org/abs/2511.02491)
- BUSTLE (Odena et al., ICLR 2021) trains a model to "prioritize compositions of intermediate values during search" in bottom-up synthesis, evaluated on string-manipulation benchmarks. [V-fetch, abstract] — [arXiv 2007.14381](https://arxiv.org/abs/2007.14381)
- Brahma (Gulwani, Jha, Tiwari, Venkatesan, PLDI 2011) encodes which component output feeds which input as "location variables" and solves an ∃∀ formula by counterexample-guided SMT; it synthesised "10-20 line loop-free bitvector programs", with formula size quadratic in the number of components. [S] — [Microsoft Research page](https://www.microsoft.com/en-us/research/publication/synthesis-loop-free-programs/)
- Shortest linear programs over GF(2) (the closest multi-output straight-line literature): Tan and Peyrin revisit the Boyar–Peralta greedy and show that randomising its selection steps, plus new tie-breaking criteria, gives large gains, including a 94-XOR AES MixColumns; applicable "up to about 32 x 32" matrices. [V-fetch, abstract] — [ePrint 2019/847](https://eprint.iacr.org/2019/847)
- A 2025 preprint reports a faster reimplementation of Boyar–Peralta and 89 g-XORs for the AES linear layer against a previous best of 91. [S] — [ePrint 2025/1493](https://eprint.iacr.org/2025/1493)
- Nested Rollout Policy Adaptation (Rosin, IJCAI 2011) runs nested Monte Carlo rollouts and adapts a per-move rollout policy by gradient steps toward the best sequence found; it set an 82-move Morpion Solitaire record (previous human record 68, nested Monte Carlo search 80), reportedly after about a week of computation. [S] — [IJCAI 2011](https://www.ijcai.org/Abstract/11/115)

### Inferences

- **Duet / Simba / oriented metrics. Mapping:** backward propagation through inverse semantics is `t − a`, `t + a`, `t / a`, `t·a` over pool values, i.e. the existing reduction search; an "oriented ball around the target" is the existing restriction to values near `t` or near `t / b`. **Benefit:** none beyond the current code. These papers confirm the design rather than extend it.
- **Brahma. Mapping:** location-variable encoding of a whole puzzle (100–200 instructions, 60-bit multiplications) is out of reach; for windows of 6–8 instructions enumeration is already faster. **Not recommended.**
- **Randomised distance-guided greedy with massive restarts (Tan–Peyrin recipe). Mapping:** the project's "shared intermediates first" greedy is the analogue of Boyar–Peralta. The transferable finding is procedural: randomise every tie-break and near-tie, run thousands of restarts per puzzle, and keep the best. **Expected benefit:** small to moderate if restarts are currently few or deterministic; it also feeds the candidate pool of section 3. **Cost:** 1–2 days plus CPU time, trivially parallel.
- **Nested rollouts / NRPA. Mapping:** a state is (pool, remaining targets); an action is "add this intermediate or apply this reduction"; a rollout completes the program with the existing fast greedy constructor, and its length scores the action. NRPA additionally learns per-action weights online, which needs hashable action codes (for example the reduction rule type plus a bucketed size ratio). **Expected benefit:** moderate and uncertain; rollouts replace a hand-written evaluation of "how good is this shared intermediate" with a measured one. **Cost:** about one week; needs a constructor that runs in milliseconds, since each decision costs hundreds of rollouts. **Why it may not transfer:** NRPA's records are on problems with a few hundred legal moves per state; here the action space per step is 10^4 or more, so the candidate actions must be pre-filtered by the existing heuristics.

### Gaps

- I found no synthesis paper targeting integer constants at 40–60 bits with multiplication and exact division.
- Duet, Brahma and NRPA were not read in the original.
- No published comparison of rollout-based search against beam search on addition-chain-like problems was found.

---

## 3. Equality saturation and e-graphs: minimum-cost DAG extraction shared across outputs

### Takeaway

Yes, there is a usable formulation, and for concrete integers it is simpler than general equality saturation: every e-class is one integer value, every e-node is one derivation `a op b = v`, and "DAG extraction with unit node cost" is exactly "choose the fewest values that derive all targets". The e-graph literature supplies the integer program (egg's `LpExtractor`), the hardness results, and a practical recipe (heuristic solution, prune, warm-started exact solve). The catch is that the method only recombines derivations that are already in the candidate pool.

### Cited Findings

- egg's ILP extractor has one binary per e-node and one binary "active" per e-class; class active equals the sum of its node variables; a chosen node forces its child classes active; each root class is forced active; the objective is the sum of node cost times node variable, so with unit cost it counts selected nodes. The documentation states: "Using ILP only counts common sub-expressions once, so it can lead to a smaller DAG expression." Cycles are handled crudely by forbidding the e-nodes that a depth-first search finds on a back edge. Solver: COIN-OR CBC. [V-fetch] — [egg 0.9.3 `lp_extract.rs`](https://docs.rs/crate/egg/0.9.3/source/src/lp_extract.rs)
- Tensat's ILP instead keeps cycles out with a topological-order variable per e-class; a follow-up replaces these with explicit cycle constraints as weighted partial MaxSAT and reports similar extraction times. [S] — [EGRAPHS 2023 paper](https://www.cs.princeton.edu/~dh7120/assets/papers/EGRAPHS2023.pdf); Tensat: [arXiv 2101.01332](https://arxiv.org/pdf/2101.01332)
- Hardness: "E-graph extraction is known to be NP-hard" and "is also hard to approximate to any constant factor". An exact algorithm runs in 2^O(w²)·poly(w, n) for treewidth w, but on the 288-e-graph extraction-gym suite "the vast majority of e-graphs in this test set were too large for computing exact tree decomposition", and the paper gives no runtime comparison with ILP. [V-fetch] — [Sun, Zhang, Ni, arXiv 2408.17042](https://arxiv.org/html/2408.17042v2)
- e-boost (2025) combines parallel heuristic DAG extraction, threshold-based pruning of the candidate space, and an ILP warm-started from the heuristic solution; it claims "558x runtime speedup over traditional exact approaches (ILP)" and "19.04% performance improvement" over the SmoothE extractor. [V-fetch, abstract] — [arXiv 2508.13020](https://arxiv.org/abs/2508.13020)
- E-graph rewriting has been applied to arithmetic datapaths with bit-width-dependent rewrites, with "a reduction in circuit area by up to 71%"; the authors state that multiple constant multiplication is a special case of their approach. [V-fetch, abstract] — [Coward et al., arXiv 2204.11478](https://arxiv.org/abs/2204.11478)
- extraction-gym is "A suite of benchmarks to test e-graph extraction algorithms" whose inputs are JSON files, with pluggable extractors. [V-fetch] — [GitHub](https://github.com/egraphs-good/extraction-gym)
- The STOKE authors' criticism of rewrite-based search applies here too: equality saturation "relies heavily on expert knowledge" and "it is unlikely that a set of expert written rules would ever cover the set of all interesting optimizations." [V-text] — [arXiv 1211.0557](https://arxiv.org/pdf/1211.0557)

### Inferences

- **Formulation (derivation hypergraph + ILP extraction).**
  - Candidate set `V`: integers in `[1, value_limit]`. Start values `S ⊂ V`, targets `T ⊂ V`.
  - Derivations `D`: every `(v, op, a, b)` with `a, b, v ∈ V` and `a op b = v`, found by hash lookups over pairs.
  - Variables: `x_v ∈ {0,1}` (value is computed), `y_d ∈ {0,1}` (derivation is used).
  - Minimise `Σ_{v ∉ S} x_v` subject to `x_t = 1` for targets; `Σ_{d derives v} y_d ≥ x_v`; `y_d ≤ x_a`, `y_d ≤ x_b`.
  - Acyclicity: `+` and `×` (operands above 1) always produce a result larger than both operands, so any cycle must contain a `−` or `÷` derivation. Either add order variables as Tensat does, or solve without them and add a cut whenever the solution contains a cycle; few cuts should be needed.
  - Arithmetic identities (commutativity, associativity, distributivity) need not be written as rewrite rules: two expressions land in the same class exactly when they evaluate to the same integer. The role of "rewrites" is taken over by whatever generates candidate values.
- **Where candidates come from.** (1) Every value in every valid program found so far for that puzzle, across all solvers, seeds and public solutions; (2) all one-step derivations among those values; (3) "bridge" values `t ± v`, `t / v`, `v·w` that would connect two or more existing values. Following e-boost, prune to values that appear in some solution within a few instructions of the incumbent, then warm-start the solver with the incumbent.
- **Expected benefit:** uncertain. It strictly generalises per-puzzle best-of merge (it mixes sub-derivations across programs instead of choosing whole programs), so when warm-started from the incumbent it cannot return anything longer, subject to the register check below. The one public data point is negative: `research.md` §4.9 records that recombining 656 alternatives gave zero gain at a 132.5k baseline. That pool may have been homogeneous; this project's pool comes from structurally different solvers (Bos–Coster, `q·b ± c`, factor sharing, BFS, meet-in-the-middle), where cross-program sharing is more plausible. Treat as "cheap to test, possibly a few percent, possibly nothing".
- **Cost:** 3–5 days. With `|V|` in the low thousands the model has thousands of binaries and 10^4–10^6 derivation rows; CP-SAT or HiGHS on CPU with a warm start and a 1–5 minute limit per puzzle is about 1–3 CPU-days for 1,000 puzzles, parallelisable. Used with a time limit it behaves as an exact large-neighbourhood step rather than a proof of optimality.
- **Why it may not transfer:** (a) the LP relaxation of this AND/OR selection problem is weak, so the solver may stall on larger pools; (b) the 48-register limit is not in the model and must be checked afterwards by scheduling, with recomputation or a re-solve if it is violated; (c) the result is bounded by pool quality, so it does nothing for a puzzle on which every solver misses the same structure; (d) treewidth-based exact extraction is unlikely to apply, since these graphs are dense.
- **Full equality saturation with symbolic rewrite rules** (as in the datapath work) is not recommended: targets are constants with no shared symbolic structure to saturate over.

### Gaps

- I did not verify from its README which extractors extraction-gym ships or its exact JSON schema; the README only points to the `data/` directory and the egraph-serialize repository. Reusing its extractors therefore needs a short check of the repository.
- The Tensat and SmoothE papers were not read in the original.
- No source reports e-graph extraction on integer-constant derivation graphs; the size and solve-time estimates above are mine.
- Whether the public "Arithmetic Graph Rewrites" notebook listed in `research.md` uses anything like this was not checked.

---

## 4. Learning-guided search with published results: AlphaDev, AlphaTensor, FunSearch, AlphaEvolve, OpenEvolve, ShinkaEvolve, PatternBoost, ALE-Bench and ALE-Agent

### Takeaway

The AlphaZero-style systems need accelerator clusters and, where a classical baseline exists, lose to it; they are out of scope for two months on CPU. LLM-driven evolution of *heuristic code* is the one learning-guided method with published wins on fixed-instance scoring problems at affordable cost (about $100 per problem in ALE-Bench, about $1,300 for a contest win, 50–150 evaluations in ShinkaEvolve), and it needs only CPU for evaluation plus API spend. Its documented weakness is that it tends to refine existing ideas rather than invent new constructions.

### Cited Findings

**AlphaDev (Nature 2023)**

- Program lengths: sort3 17 instructions (human 18), sort4 28 (28), sort5 42 (46), VarSort5 63 (115). Training used TPU v3 with up to 16 cores and up to 512 actors on TPU v4, converging in up to 2 days. [V-fetch] — [Nature 2023, PMC copy](https://pmc.ncbi.nlm.nih.gov/articles/PMC10247365/)
- Against stochastic superoptimisation: the cold-start variant "is unable to find the optimal programs"; the warm-start variant matches AlphaDev on fixed sorts and is more compute-efficient there, but "struggles to escape this local maxima" on variable sorts. AlphaDev explored at most about 12 million programs against about 31 trillion for AlphaDev-S. [V-fetch] — [Nature 2023, PMC copy](https://pmc.ncbi.nlm.nih.gov/articles/PMC10247365/)
- The lead author is quoted as saying learning became slow beyond 297 actions and games longer than 130 instructions. [S] — [MIT Technology Review](https://www.technologyreview.com/2023/06/07/1074184/google-deepmind-game-ai-alphadev-algorithm-code-faster/amp/)
- Classical rebuttal: an A*-based enumerative search "outperforms AlphaDev in synthesis time by two orders of magnitude ran on a standard notebook instead of a TPU cluster." Reported times (enumeration / AlphaDev-RL / AlphaDev-S): n = 3: 97 ms / 6 min / 0.4 s; n = 4: 2443 ms / 30 min / 0.6 s; n = 5: 11 min / ≈1050 min / ≈345 min. It also proved by exhaustive search that no length-19 kernel exists for n = 4, which took two weeks. [V-text] — [Ullrich & Hack, CGO 2025](https://compilers.cs.uni-saarland.de/papers/ullrich_sorting_kernels.pdf)

**AlphaTensor (Nature 2022)**

- Single-player game with "more than 10^12 actions for most interesting cases"; made to work by 5 million synthetic factorisation demonstrations, random change-of-basis augmentation, sampled actions, and a per-step penalty with a rank-based terminal penalty. Compute: 64 TPU cores, 600,000 iterations, 1,600 actors, about a week. [V-fetch] — [Nature 2022, PMC copy](https://pmc.ncbi.nlm.nih.gov/articles/PMC9534758/)

**FunSearch and AlphaEvolve**

- AlphaEvolve's own comparison table: FunSearch "evolves single function", "up to 10-20 lines of code", "needs fast evaluation (≤ 20min on 1 CPU)", "millions of LLM samples used"; AlphaEvolve "evolves entire code file", "up to hundreds of lines", "can evaluate for hours, in parallel, on accelerators", "thousands of LLM samples suffice", "benefits from SOTA LLMs". [V-text] — [AlphaEvolve white paper, arXiv 2506.13131](https://arxiv.org/pdf/2506.13131)
- Recipe for fixed mathematical instances: "evolve heuristic search algorithms rather than directly evolving the constructions themselves." Each candidate "was given a fixed time budget (e.g., 1000 seconds) and was shown the best construction found by the previous best heuristic." The final results "were often the result of a sequence of different, specialized heuristics", early ones making large gains and later ones fine-tuning. [V-text] — [arXiv 2506.13131](https://arxiv.org/pdf/2506.13131)
- Choice of abstraction: the paper hypothesises that constructor functions suit "highly symmetric solutions", whereas "for problems with non-symmetric solutions it works better to evolve customized search algorithms." [V-text] — [arXiv 2506.13131](https://arxiv.org/pdf/2506.13131)
- Outcomes on over 50 open mathematical problems: best known construction rediscovered in about 75% and improved in about 20%. Ensemble of Gemini 2.0 Flash and Pro; MAP-Elites plus islands database; evaluation cascade; up to "on the order of 100 compute-hours to evaluate any new solution". Stated main limitation: an automated evaluator must exist. [V-text] — [arXiv 2506.13131](https://arxiv.org/pdf/2506.13131)
- A 67-problem follow-up by Georgiev, Gómez-Serrano, Tao and Wagner reports rediscovering best known solutions in most cases and improving several. [V-fetch, abstract] — [arXiv 2511.02864](https://arxiv.org/abs/2511.02864)

**Open implementations**

- OpenEvolve: MAP-Elites with island populations and LLM ensembles; works with any OpenAI-compatible API; the user writes an initial program with `EVOLVE-BLOCK-START`/`END` markers, an `evaluator.py` and a `config.yaml`; Apache-2.0; documented examples run 50–100 iterations, and the circle-packing example shows progress to generation 460. [V-fetch] — [GitHub README](https://github.com/algorithmicsuperintelligence/openevolve)
- OpenEvolve cost per iteration is reported in a search summary as roughly $0.15–0.60 with o3, $0.03–0.12 with o3-mini and $0.08–0.30 with Gemini 2.5 Pro, but the fetched README text showed no dollar figures. Treat as unconfirmed. [S, conflicting] — [GitHub README](https://github.com/algorithmicsuperintelligence/openevolve)
- ShinkaEvolve (ICLR 2026, Apache-2.0): adds parent sampling that balances exploration and exploitation, rejection of near-duplicate code by embedding similarity (threshold 0.95), and a UCB1 bandit over LLMs. It reached a state-of-the-art 26-circle packing in 150 evaluations and used 50 generations per ALE-Bench task. Starting from ALE-Agent's solutions it improved them by about 2.3% on average over 10 tasks; on one task the score rose from 2880 (5th place) to 3140 (2nd). The authors note that changes often stayed "algorithmically close" to the starting solution. No dollar costs are given. [V-fetch] — [arXiv 2509.19349](https://arxiv.org/html/2509.19349v1)
- A competing framework's own benchmark reports OpenEvolve needing 783 evaluations and succeeding in one of three runs on a circle-packing threshold, and ShinkaEvolve failing it. Vendor comparison; weigh accordingly. [S] — [LoongFlow, arXiv 2512.24077](https://arxiv.org/pdf/2512.24077)

**LLM agents on heuristic contests**

- ALE-Bench (NeurIPS 2025): all runs limited to 4 hours in C++20. Scaffold ablation with Gemini 2.5 Pro, average performance and cost per problem: base 1167 at $7.64; plus domain-knowledge prompts 1264 at $11.12; plus best-first search with beam-like multi-child expansion 1879 at $100.33, generating about 1,000 solution codes at about $0.11 per response. "Method 2 yielded substantial gains." The paper also says "AI excels in contests suited to specific approaches, like simulated annealing" and that long-format contests remain harder. [V-fetch] — [arXiv 2506.09050](https://arxiv.org/html/2506.09050v2)
- The percentile for that configuration is reported differently in two places: top 8.6% (rating 2222) in the fetched paper text, top 6.8% in the NeurIPS slides as summarised by search. [V-fetch] vs [S] — [arXiv 2506.09050](https://arxiv.org/html/2506.09050v2); [NeurIPS slides](https://neurips.cc/media/neurips-2025/Slides/121724.pdf)
- ALE-Agent won AtCoder Heuristic Contest 058 on 2025-12-14, first of 804, in a 4-hour window, with 2,654 GPT-5.2 calls and 2,119 Gemini 3 Pro Preview calls, at about $1,300 in total. The winning program was greedy construction followed by simulated annealing. The authors state that "AI does not always rival or surpass top humans", and an expert reviewer judged human design of the greedy part still superior. [V-fetch] — [Sakana AI](https://sakana.ai/ahc058/)

**PatternBoost and a 2026 head-to-head**

- PatternBoost alternates problem-specific local search with a small transformer trained on the best constructions, whose samples seed the next round. Without local search the method is "disastrously bad"; on one problem a hand-crafted method beat it, and the authors write that "handcrafted specialized algorithms can still outperform generic ML methods." [V-fetch] — [arXiv 2411.00566](https://arxiv.org/html/2411.00566v1)
- RadonBench (October 2026) compares exhaustive extension, greedy local search, PatternBoost, AlphaZero and AlphaEvolve on one combinatorial-geometry search task. No method reached the target; greedy local search and AlphaEvolve produced the closest near misses, ahead of PatternBoost and AlphaZero. [V-fetch, abstract] — [arXiv 2610.33259](https://arxiv.org/abs/2610.33259)

### Inferences

- **Practical recipe for LLM-driven evolution on this problem** (assembled from the AlphaEvolve, ALE-Agent and ShinkaEvolve practices cited above):
  1. Freeze a trusted verifier. The evaluator returns total instructions on a fixed puzzle subset, per-puzzle lengths, and any validity error as text feedback.
  2. Evolve the *solver or improver code*, not programs for individual puzzles. Two granularities: a FunSearch-style priority function inside the existing reduction search (which candidate `v = q·b ± c` or shared intermediate to take next), or an AlphaEvolve-style `improve(puzzle, incumbent, time_budget)` routine that is shown the best known program and must shorten it.
  3. Use an evaluation cascade: about 20 puzzles to reject broken candidates, about 100 stratified puzzles for ranking, all 1,000 only for the top few.
  4. Put domain knowledge in the prompt (the rule set, what has been tried and failed, the gap to the leaderboard) and expand several children per parent; in ALE-Bench the breadth step, not the knowledge step, produced most of the gain.
  5. Keep every valid per-puzzle program any candidate ever produces and merge per puzzle. There is no hidden test set, so fitting the 1,000 instances is the objective, not a risk; the archive of evolved variants is itself a portfolio and feeds the candidate pool of section 3.
- **Expected benefit:** the most likely of the surveyed methods to yield new constructive ideas, because it searches over heuristics rather than over programs. The only quantitative anchor is ShinkaEvolve's roughly 2.3% average gain over an already strong agent solution in 50 generations; a similar gain here would be about 3,000 instructions, and porting ideas across variants could give more from a 147k start. This is an extrapolation from different problems.
- **Cost:** 3–5 days to wrap the solver and evaluator (OpenEvolve or ShinkaEvolve can be used as is). API spend on the order of $100–$1,500 by the ALE-Agent figures. CPU: with a 100-puzzle ranking stage at about one second per puzzle, a candidate evaluates in seconds on a multi-core machine, so 1,000 candidates fit in a day.
- **Why it may not transfer:** ALE-Bench attributes agent strength to annealing-shaped problems, and this problem is constructive and number-theoretic; ShinkaEvolve's edits stayed close to the starting algorithm; RadonBench shows AlphaEvolve merely level with greedy local search on a hard instance; proposals may converge on the same ideas that are already tried unless the prompt lists them explicitly. Competition rules on LLM use were not checked.
- **AlphaDev / AlphaTensor-style reinforcement learning:** not feasible on CPU in two months (16–64 TPU cores, hundreds to thousands of actors, days to a week), and on the one task with a classical comparison enumeration was about 100 times faster. See section 5.
- **PatternBoost. Mapping:** train a small transformer on token sequences of good programs and sample seeds for local search. Each puzzle is a separate fixed instance with at most a handful of good solutions, integers of 39 bits tokenise poorly, and training is slow without a GPU. **Not recommended.**
- **AlphaTensor's synthetic-demonstration idea** is reusable without RL: random short programs from a puzzle's start values give unlimited (value set, known program length) pairs, which can calibrate or train a cost-to-go estimate (section 5).

### Gaps

- The FunSearch Nature paper could not be fetched (access blocked), so its sample counts and ablations are cited only through AlphaEvolve's comparison table.
- No dollar cost is published for OpenEvolve or ShinkaEvolve runs; the only measured costs are ALE-Agent's.
- I found no public report of LLM-driven evolution applied to this competition, to Santa 2025, or to addition chains, straight-line programs or integer complexity. Searches for the Santa 2026 discussion forum returned nothing indexed.
- How the current leaderboard leaders obtained 125,650 is unknown.

---

## 5. Reinforcement learning or learned value functions for addition chains and arithmetic expression search

### Takeaway

The earlier judgement stands: I found no evidence that reinforcement learning or a learned value function beats classical search on addition chains, integer straight-line programs or Countdown-style games at any scale near 40–60 bits. Published learning results in this area stop at circuits of six gates or four-number games with targets up to 100, and they are trained against, and evaluated below, exhaustive search.

### Cited Findings

- CircuitBuilder (March 2026) frames arithmetic-circuit synthesis with `+` and `×` gates as a single-player game with an AlphaZero-style loop. Ground truth comes from "enumerating all polynomials reachable from seed nodes ... within C arithmetic operations." Evaluated over F5 at C = 5 and C = 6 gates on one Tesla T4: PPO+MCTS reaches about 35% success with two variables and 27.3% (C = 5) or a 23.5% peak (C = 6) with three; SAC reaches 57.8% and 46.3% with two variables and 10.7% and 9.4% with three. The authors call the setting "far smaller than the regimes studied in algebraic complexity theory." [V-text] — [arXiv 2603.17075](https://arxiv.org/pdf/2603.17075)
- Stream of Search trains a 250M-parameter transformer on Countdown with 4 input numbers and targets from 10 to 100 (5-number games were excluded because traces "can be 60,000 tokens long"). It reaches 51.27% accuracy, "slightly lower" than the average of the symbolic strategies that generated its training data; fine-tuning solves about 36% of problems those heuristic strategies missed. Hardware: 4 × 80 GB A100. The authors note that external search methods "are likely to be more efficient for these tasks". [V-fetch] — [arXiv 2404.03683](https://arxiv.org/html/2404.03683v1)
- AlphaDev's sorting kernels (17–63 instructions) were matched or beaten by enumerative search about two orders of magnitude faster on a notebook (figures in section 4). [V-text] — [Ullrich & Hack](https://compilers.cs.uni-saarland.de/papers/ullrich_sorting_kernels.pdf)
- AlphaTensor's success on an exact, enormous-action-space problem required 5 million synthetic demonstrations, symmetry augmentation, 64 TPU cores and 1,600 actors for about a week. [V-fetch] — [Nature 2022, PMC copy](https://pmc.ncbi.nlm.nih.gov/articles/PMC9534758/)
- Two targeted searches for reinforcement learning on addition chains returned no such work; what exists is genetic and evolutionary algorithms for short addition chains and new deterministic generation methods. [S] — [MIT DSpace, 2017 evolutionary algorithm paper](https://dspace.mit.edu/bitstream/1721.1/115968/2/10732_2017_9340_ReferencePDF.pdf); [arXiv 2207.13276](https://arxiv.org/pdf/2207.13276)
- A search for reinforcement learning on multiple constant multiplication or adder graphs found RL only for adjacent hardware problems (multiplier compressor trees, prefix adders), not for constant synthesis. [S] — [RL-MUL, DAC 2023](https://personal.hkust-gz.edu.cn/yuzhema/papers/C30-DAC2023-RL-MUL.pdf); [arXiv 2405.06758](https://arxiv.org/html/2405.06758v1)
- Monte Carlo tree search (bandit-guided, no neural network) has improved multivariate Horner schemes by choosing the variable order, reducing evaluation cost "sometimes by factors up to two" against the greedy most-frequent-variable rule. [V-fetch, abstract] — [Kuipers et al., arXiv 1207.7079](https://arxiv.org/abs/1207.7079)

### Inferences

- **Confirmation of the "plain RL is a poor fit" judgement.** Three independent lines agree: (1) scale: learned agents solve 5–6 gate circuits and 4-number Countdown, against 100–200 instructions and 39-bit targets here; (2) baselines: in every case with a classical comparison, enumeration or symbolic search is equal or better and far cheaper; (3) compute: the successful systems used TPU clusters for days. On CPU in two months it is not viable.
- **The one qualification** is that learning succeeded on exact problems when unlimited synthetic supervision existed (AlphaTensor) and when learning was confined to re-ranking candidates inside a classical search (BUSTLE in section 2). The analogue here is a **supervised cost-to-go model**, not RL: generate random short programs from each puzzle's start values, record (value, pool features) → instructions used, fit a small gradient-boosted model on CPU, and use it to order candidates in the best-first reduction search. **Expected benefit:** small. For near-random 39-bit integers the informative features are size ratios to pool values, small-factor smoothness and nearness to products, all of which hand-written costs already use. **Cost:** about one week. **Why it may not transfer:** synthetic programs do not follow the distribution of the real targets, and the exact-match objective leaves little smooth signal to regress on.
- **Rough headroom estimate.** Counting the number of distinct programs of n instructions (operator and two operand choices per step, three start values) against the roughly 1,060 bits needed to specify 30 random 39-bit targets gives n ≥ about 84, or about 2.8 instructions per target; the same count gives about 3.2 at 45 bits and 4.1 at 60 bits. This is my own back-of-envelope calculation, valid only for typical random target sets and ignoring `value_limit`, exact-division and register limits. If the targets are close to random, the leaders' 4.67 per target is within a factor of about 1.7 of this floor, so remaining gains are in sharing structure across targets rather than in a fundamentally shorter per-target construction. If the targets were generated from hidden short programs, this bound does not apply.

### Gaps

- No paper was found that trains or evaluates any learned method on addition chains, addition sequences or integer straight-line programs at cryptographic or 40–60-bit sizes. Absence from two keyword searches is not proof of absence.
- The evolutionary addition-chain papers were not read; their exponent sizes and whether they beat window methods are unverified.
- The headroom estimate depends on the unknown target distribution; `research.md` already lists target generation as an open question.

---

## 6. Ranked shortlist: what to try first within two months on CPU-only compute

### Takeaway

Try, in order: LLM-driven evolution of the solver's heuristics; ILP extraction over a pooled derivation hypergraph as the merge stage; rollout-guided construction. The first generates diverse constructions, the second exploits them, and both run on CPU apart from API spend. Deprioritise MCMC, learned value functions, AlphaZero-style RL, PatternBoost and solver-based whole-program synthesis.

### Cited Findings

- Evidence for rank 1: about 1,000 generated programs at about $100 per problem lifted ALE-Bench performance from 1167 to 1879; a later run won a live 804-entrant contest for about $1,300; ShinkaEvolve added about 2.3% on top of agent solutions in 50 generations. [V-fetch] — [ALE-Bench](https://arxiv.org/html/2506.09050v2); [Sakana AHC058](https://sakana.ai/ahc058/); [ShinkaEvolve](https://arxiv.org/html/2509.19349v1)
- Evidence for rank 2: ILP extraction counts shared subexpressions once; warm-started ILP after heuristic pruning is the current practical recipe. [V-fetch] — [egg `lp_extract.rs`](https://docs.rs/crate/egg/0.9.3/source/src/lp_extract.rs); [e-boost](https://arxiv.org/abs/2508.13020)
- Evidence for rank 3: randomised restarts of a distance-guided greedy set records on linear straight-line programs; nested rollout search set a long-standing single-player puzzle record. [V-fetch] — [Tan & Peyrin](https://eprint.iacr.org/2019/847); [S] — [Rosin, IJCAI 2011](https://www.ijcai.org/Abstract/11/115)
- Evidence against stochastic and RL approaches: STOKE cold and warm start both failed on 17-instruction sorting kernels; enumeration beat AlphaDev by about 100 times; RL circuit synthesis reaches 35–58% success at 5–6 gates. [V-text] — [Ullrich & Hack](https://compilers.cs.uni-saarland.de/papers/ullrich_sorting_kernels.pdf); [CircuitBuilder](https://arxiv.org/pdf/2603.17075)

### Inferences

Ranking (all benefit estimates are my inference; none is measured on this problem):

| Rank | Method | Why this position | Effort | Compute | Main risk |
|---|---|---|---|---|---|
| 1 | LLM-driven evolution of solver heuristics (OpenEvolve or ShinkaEvolve; recipe in section 4) | Only surveyed method that searches over *constructions* rather than polishing programs; published wins on fixed-instance scoring tasks | 3–5 days setup, then runs unattended | CPU for evaluation; roughly $100–$1,500 API | Refines known ideas instead of finding new ones; problem is not annealing-shaped |
| 2 | ILP/CP-SAT extraction over pooled derivation hypergraph (section 3) | Cheap, deterministic, never longer than best-of merge when warm-started; natural consumer of rank 1's and rank 3's diversity | 3–5 days | 1–3 CPU-days per full pass | Public report of zero gain from recombination at 132.5k; bounded by pool quality; register limit handled post hoc |
| 3 | Randomised massive restarts plus rollout-guided choice of shared intermediates (NMCS/NRPA style, section 2) | CPU-only, reuses the existing fast constructor, produces diverse programs for rank 2 | about 1 week | Heavy but parallel | Action space must be pre-filtered; needs millisecond rollouts |
| 4 | Supervised cost-to-go model for ordering reductions (section 5) | Plausible but weak signal on near-random integers | about 1 week | Light | Synthetic data mismatch |
| 5 | STOKE-style annealing through invalid states; shared-incumbent portfolio (section 1) | Small extensions of the existing LNS | 2–5 days | Light | Evidence says local search stalls at this level |
| Not recommended | AlphaZero-style RL, PatternBoost, whole-puzzle SMT or component-based synthesis, symbolic peephole tables, abstract-interpretation pruning, symbolic equality saturation | Wrong scale, wrong hardware, or subsumed by existing code | — | — | — |

- Suggested sequencing: build the rank 2 extractor in week 1, since it immediately tests whether the existing solver outputs contain unexploited sharing; start rank 1 in parallel and let it run for several weeks, feeding every valid program into the rank 2 pool; add rank 3 only if rank 2 shows that pool diversity is the bottleneck.
- A go/no-go test for rank 2: run it on 50 puzzles with the current pool. If the gain is zero there as well, the pool is the problem, and effort should move to ranks 1 and 3.
- Neither rank 1 nor rank 2 replaces the step `research.md` already recommends, reproducing the public 128–132k notebooks; their programs should be added to the pool where rules permit.

### Gaps

- No measured result exists for any shortlisted method on this problem; the ranking rests on analogies to other domains.
- API cost for rank 1 is taken from ALE-Agent's contest setting and could differ by several times for longer solver code and longer evaluation loops.
- Whether stronger, multiplication-heavy solutions actually hit the 48-register limit is still unknown (`research.md` conclusion 5), which affects how often rank 2's output needs repair.
- Competition rules on external LLM usage and on reusing public solutions were not checked in this research.
