# Stochastic search and solver-based methods for shortest addition chains, multi-target chains and straight-line programs (methods not in notes/research.md or the "already tried" list)

Researched 2026-11-24. Everything under "Inferences" is my own mapping onto the Elf Calculator problem, not something a source says.

Verification tags used on every cited finding:

| Tag | Meaning |
|---|---|
| [V-read] | I read the paper's full text in this session (PDF converted to text) |
| [V-fetch] | The fetch tool extracted it from the paper's full-text page; I did not read the raw text line by line |
| [V-abs] | Only the abstract / landing page was fetched; the paper's internals were not read |
| [U-search] | Unverified: search-engine summary only |
| [U-bg] | Unverified: background knowledge, not checked against the source in this session |

Sources I could not open: the TCHES/ToSC journal site and its mirrors (bot protection), ePrint PDFs (HTTP 403; abstract pages worked), MIT DSpace (HTTP 429), Springer (login redirect), preprints.org (HTTP 403). This is why Tan–Peyrin, Xiang et al. and Picek et al. are verified at abstract level only.

## 1. Monte Carlo methods: MCTS, Nested Monte Carlo Search, NRPA, limited discrepancy search, beam-stack search

### Takeaway
No published application of NMCS, NRPA or MCTS to addition chains or integer straight-line programs was found. The closest evidence is Cazenave's expression discovery (including a Countdown-style target-number task where NMCS levels 1–2 won and UCT was no better than random sampling) and Rosin's NRPA records on Morpion Solitaire, a single-player construction problem with depth 82–177 and branching 46, which is the same order as a top-down reduction search on one puzzle here.

### Cited Findings

**Nested Monte Carlo Search (NMCS)**
- A level-n search plays one principal sequence; at each step it runs a level n−1 search for every available move and plays the best one; level 0 is a random playout. The best sequence found at a level is memorised and followed when the lower level finds nothing better; the paper says this memorisation "is necessary for Nested Monte-Carlo search to work at level greater than one". [V-read] — [Cazenave, Monte-Carlo Expression Discovery](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)
- Cost: for tree height h and branching a, a level-1 search performs a·h²/2 playout steps. [V-read] — [Cazenave, Monte-Carlo Expression Discovery](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)
- The original NMCS paper applied it to Morpion Solitaire, SameGame and 16x16 Sudoku. [U-search] — [Cazenave, IJCAI 2009](https://ijcai.org/proceedings/2009/83)

**NMCS for expression discovery (Cazenave, IJAIT 2013; short version ECAI 2010)**
- State and action encoding: an expression tree is a stack of atoms in prefix order. A move pushes one atom (operator or terminal). A cap on node count is enforced by allowing only terminals once `index + numberLeaves >= maximumNodes`; the cap is "usually ranging from ten to one hundred". Each nesting level keeps its own stack. [V-read] — [Cazenave](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)
- Protocol: 100 runs per problem and level, stopped after 2^19 expression evaluations. [V-read] — [Cazenave](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)
- Target number problem (closest task to ours): use each of the numbers 1–10 exactly once with + − × / to reach 737; score is 1000 minus the absolute difference. Level 1 "improves much" on level 0, level 2 "is still a large improvement", levels 3 and 4 are close to level 2, and an exact solution was found. UCT was "equivalent to random sampling"; iterative deepening was worse than random sampling. [V-read] — [Cazenave](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)
- Prime-generating polynomials: level 2 found a polynomial giving 51 primes in a row versus 43 for the Cartesian GP result it cites; average best score peaks at 35 for NMCS, 15 for UCT, 5 for iterative deepening; level 3 was slightly worse than level 2. [V-read] — [Cazenave](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)
- Finite algebra: level 3 found a 31-operation discriminator term after 8,704,083 evaluations; the cited optimised GP needed 238,000,000 evaluations for a 51-operation term. [V-read] — [Cazenave](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)
- Author's conclusion: NMCS beat UCT and iterative deepening on all test domains, because it "optimizes an expression at all steps of its building while UCT and Iterative Deepening only optimize the beginning". Stated advantages: natural restarts, trivial parallelism by seed. Stated future work: memorise previously evaluated expressions. On easy tasks (Kepler's law, Santa-Fe ant) nesting was useless because random sampling already solved them. [V-read] — [Cazenave](https://www.lamsade.dauphine.fr/~cazenave/papers/MCExpression.pdf)

**Nested Rollout Policy Adaptation (NRPA, Rosin, IJCAI 2011)**
- Algorithm: a policy is a weight per move code. A rollout picks child i with probability proportional to exp(pol[code(node,i)]). Each level n ≥ 1 runs N iterations; each iteration calls level n−1 with the current policy, replaces the best sequence on "a tie or improvement", then takes one gradient step of size Alpha towards the best sequence. The lower level's final policy is discarded. All reported results use Alpha = 1.0 and N = 100. [V-read] — [Rosin, NRPA](https://cs.uwaterloo.ca/~jhoey/rgwiki/uploads/11IJCAI-NRPA-Rosin.pdf)
- Move encoding: `code(node,i)` is domain-specific; for Morpion it identifies the endpoints of the line added, for crosswords the word added. The paper states "NRPA benefits when actions with the same code have similar value across a range of nodes", and that states reachable by several move orders help because NRPA explores permutations. [V-read] — [Rosin, NRPA](https://cs.uwaterloo.ca/~jhoey/rgwiki/uploads/11IJCAI-NRPA-Rosin.pdf)
- Problem sizes and records: Morpion 5T has depth 177 and branching 46, old record 170 (human, 1976), new 177. Morpion 5D has depth 82 and branching 46, old record 80 (NMCS), new 82. Both crossword instances also improved on the previous best. [V-read] — [Rosin, NRPA](https://cs.uwaterloo.ca/~jhoey/rgwiki/uploads/11IJCAI-NRPA-Rosin.pdf)
- Efficiency versus NMCS: on all four test problems NRPA's median result at 100 s was statistically significantly better than NMCS at 1000 s; on one crossword instance NRPA level 3 at 1,000 s beat standard and sampled NMCS at 10,000 s; on Morpion 5T, NMCS at 10,000 s (even with a hand-tuned rollout policy) was worse than NRPA at 100 s. [V-read] — [Rosin, NRPA](https://cs.uwaterloo.ca/~jhoey/rgwiki/uploads/11IJCAI-NRPA-Rosin.pdf)
- Cost and result spread: each nesting level costs roughly 100x the one below. Long runs took about 1 hour (5D, level 4) and 1 week (5T, level 5) per run. Over 28 level-5 runs on 5T the median was 171 and the maximum 177, reached twice; over 40 level-4 runs on 5D, 25 reached 82. [V-read] — [Rosin, NRPA](https://cs.uwaterloo.ca/~jhoey/rgwiki/uploads/11IJCAI-NRPA-Rosin.pdf)
- Limitations the paper states: convergence can be towards a suboptimal sequence, and "NRPA may not obtain robust policies that give viable results starting from arbitrary nodes". [V-read] — [Rosin, NRPA](https://cs.uwaterloo.ca/~jhoey/rgwiki/uploads/11IJCAI-NRPA-Rosin.pdf)
- Later variants exist (Beam NRPA, Stabilized NRPA, Generalized NRPA with a bias term, limited repetitions). Beam NRPA matched but did not exceed 82 on Morpion 5D. [U-search] — [Beam NRPA](https://www.lamsade.dauphine.fr/~cazenave/papers/CazenaveBeam.pdf), [Stabilized NRPA](https://arxiv.org/pdf/2101.03563), [GNRPA with limited repetitions](https://arxiv.org/pdf/2401.10420)

**MCTS / learning on arithmetic circuits**
- CircuitBuilder (March 2026) frames finding arithmetic circuits (addition and multiplication gates) for polynomials as a single-player game with a fixed operation budget, trained AlphaZero-style; it compares PPO+MCTS with Soft Actor-Critic and reports results only for two- and three-variable targets. [V-abs] — [CircuitBuilder, arXiv 2603.17075](https://arxiv.org/abs/2603.17075)
- AlphaTensor used an AlphaZero-based search to find matrix multiplication algorithms. [U-search] — [AlphaTensor](https://pmc.ncbi.nlm.nih.gov/articles/PMC9534758)

**Limited discrepancy search and complete beam searches**
- Beam-stack search (Zhou & Hansen, ICAPS 2005) adds chronological backtracking to beam search so that it is complete and anytime. BULB (Furcy & Koenig, IJCAI 2005) combines beam search with limited discrepancy backtracking. Limited discrepancy search itself is Harvey & Ginsberg, IJCAI 1995. [U-search] — [Beam stack search, Wikipedia](https://en.wikipedia.org/wiki/Beam_stack_search), [Limited Discrepancy Beam Search](https://ijcai.org/proceedings/2005/50)
- A CP 2026 paper compares Complete Anytime Beam Search (CABS; from background knowledge, it reruns beam search with a growing beam width), beam-stack search, BULB and a new depth-bounded-discrepancy beam search inside a dynamic-programming solver. CABS had the highest average proportion of instances solved, the most optimality proofs and the lowest mean gap in every tested setting; beam-stack search and BULB only won when memory was restricted and run time extended. [V-abs] — [Chen & Beck, CP 2026](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2026.12)

### Inferences
- Encoding that fits (inference). A forward encoding (move = any instruction on the pool) has roughly |pool|²·4 raw moves and random playouts will never hit 40–60-bit targets, so it is not viable. A backward encoding matches our existing reduction search: state = set of open values (initially the targets) plus closed values (starting values); move = choose a decomposition `v = a op b` for one open value, where a and b are closed, open or new; the playout ends when nothing is open; score = −(number of decompositions). Depth is the program length (100–200) and branching is the number of candidate decompositions the generator offers (tens). That is the same scale as Morpion Solitaire in Rosin's Table 1.
- NRPA move code (inference). `code = hash(v, a, b, op)`. Targets recur in every playout and intermediates recur often, so the policy learns "for this value use this decomposition". Rosin's condition (same code has similar value across contexts) holds reasonably, because the cost of a decomposition depends mostly on its operands, and sharing is captured automatically: decompositions that produce operands reused by other targets get reinforced.
- Why this explores differently from what we tried (inference). Local search and large-neighbourhood search edit one solution. NRPA and NMCS rebuild the whole program on every playout, biased towards the best one, so they can change many coupled decomposition choices at once. Ties replace the incumbent in NRPA, which gives drift across equal-length solutions.
- Compute cost (inference, rough). Level 2 with N = 100 is 10^4 playouts per puzzle; level 3 is 10^6. If one playout of the reduction heuristic costs 20–200 ms, level 2 costs 200–2,000 s per puzzle, or about 55–555 CPU-hours for 1,000 puzzles; level 3 is only affordable if a playout is near 1 ms. Candidate decompositions per value must be memoised. A cheap first test: level 2 on 20 puzzles against equal-time independent random restarts of the same heuristic.
- Expected benefit (inference). Unknown; there is no published number for this problem class. The evidence only shows that nested search levels 1–2 beat flat random restarts and UCT on construction tasks, and that higher levels gave little at budgets of 2^19 evaluations. Plain UCT should be skipped.
- Reasons it may not transfer (inference). (1) Score differences between playouts are 1–2 instructions out of 150, so the signal is coarse. (2) Expression discovery searches trees without sharing; our gain comes from sharing in a DAG, which the tree literature does not test. (3) The register limit and value_limit must be checked after each playout or built into the move generator. (4) NRPA quality depends on the move generator: a decomposition that the generator never proposes cannot be learned.
- Limited discrepancy search (inference). With the heuristic's ranked candidate list, 1-discrepancy probing costs about depth × (branching − 1) playouts (a few thousand); NMCS level 1 is the randomised analogue. CABS-style restarts with a doubling beam are the best-supported complete variant, but beam search is already used by public solutions, so this is an incremental change.

### Gaps
- No paper applying NMCS, NRPA, UCT or beam-stack search to addition chains, addition sequences or integer straight-line programs turned up in two targeted searches. Absence in search results is not proof that none exists.
- The original LDS and beam-stack papers were not opened; the statements about them rest on search summaries.
- CircuitBuilder's state/action encoding and any comparison with optimal circuits were not on the abstract page.

## 2. Evolutionary, simulated annealing, ant colony, particle swarm and artificial immune system approaches to addition chains

### Takeaway
This line of work is weak for our purpose. Everything found targets single-exponent, addition-only chains; a 2023 survey-style statement in a competing paper says these methods "are suitable for relatively small integers until now", and I found no verified result showing them beating window-type heuristics at 40–60 bits, nor any multi-target or multiplication variant.

### Cited Findings
- Cruz-Cortés, Rodríguez-Henríquez, Juárez-Morales & Coello Coello (CIS 2005) applied a genetic algorithm with chain length as fitness and reported "quasi-optimal" chains. [U-search] — [GA for addition chains](https://www.academia.edu/96587690/Finding_Optimal_Addition_Chains_Using_a_Genetic_Algorithm_Approach)
- Cruz-Cortés, Rodríguez-Henríquez & Coello Coello (IEEE Trans. Evol. Comput. 12(1), 2008) proposed an artificial immune system and studied exponents under 20 bits and cryptographic sizes of 128–2048 bits. [U-search] — [AIS for addition chains](https://www.bohrium.com/paper-details/an-artificial-immune-system-heuristic-for-generating-short-addition-chains/811903478606594049-2422)
- Osorio-Hernández et al. (2009) used a GA with repair and local search and reported minimal chains for small exponents. [U-search] — [GA with repair](https://ipn.elsevierpure.com/en/publications/a-genetic-algorithm-with-repair-and-local-search-mechanisms-able-)
- Picek, Coello Coello, Jakobovic & Mentens (J. Heuristics 24(3), 2018) used a GA with a new encoding, crossover, mutation and a repair step, compared with other metaheuristics on moderate exponents, and went up to 2^255 − 21. For that size they "were unable to find any results produced by other metaheuristics" and added three benchmark strategies of their own. [U-search] — [Picek et al.](https://link.springer.com/10.1007/s10732-017-9340-2)
- A CEC 2016 GA paper is titled as minimising addition chains "for small exponents"; an evolutionary-programming paper appeared in Eng. Appl. Artif. Intell. 37 (2015). (Titles and venues read in the reference list below; contents not read.) [V-read for the citation only] — [Ding et al. reference list](https://arxiv.org/pdf/2207.13276)
- Assessment from a later paper proposing deterministic window variants: "The Power-tree method, the Genetic Algorithm, the Artificial Immune System and the Evolutionary Programming need complex operations, which are suitable for relatively small integers until now." [V-read] — [Ding et al., arXiv 2207.13276v2](https://arxiv.org/pdf/2207.13276)
- Deterministic baseline the metaheuristics would have to beat, from the same paper: on all 365,634 integers with optimal chain length ≤ 22, the binary method is optimal for 2.16%, the window method for 12.63% and their cross-window method with an addition-sequence precomputation for 62.58% (98.53% within one step of optimal; mean gap 0.389). On random 160-bit integers the average lengths are 238.15 (binary), 192.37 (window) and 187.89 (theirs). The paper does not run the GA/AIS methods itself. [V-read] — [Ding et al., arXiv 2207.13276v2](https://arxiv.org/pdf/2207.13276)
- A December 2023 preprint proposes simulated annealing for short addition sequences (the multi-target case) and compares with exact and heuristic algorithms. [U-search] — [SA for addition sequences](https://www.preprints.org/manuscript/202312.1556)

### Inferences
- The published metaheuristics mutate a chain directly and repair it. That is the same neighbourhood family as the local search, window replacement and large-neighbourhood search that already gave no gain near 130,000, so I would not expect a different outcome.
- The one reusable idea is indirect encoding: evolve the parameters or priorities of a constructive heuristic rather than the program. NRPA (section 1) does this with a learned policy and has stronger evidence, so a GA adds nothing obvious.
- Expected benefit: low. Compute cost: moderate (population × generations full evaluations). Reason not to transfer: none of the evidence involves multiplication, multiple targets, register limits or value limits.

### Gaps
- Ant colony (Nedjah & Mourelle) and particle swarm papers on addition chains are known to exist, but no source for them was retrieved in this session, so nothing about their results is asserted here.
- Picek et al.'s actual chain lengths for 2^127 − 3 and 2^255 − 21, their comparison against window methods, and their evaluation budgets could not be read (paywall and rate limit).
- The simulated-annealing preprint's instance sizes and results could not be read (HTTP 403).
- Whether any of these methods beats a tuned window or Bos–Coster heuristic at 40–60 bits is not established by anything I could verify.

## 3. Shortest linear program (SLP) problem from cryptography: Boyar–Peralta and its randomised variants, Paar, Xiang et al., backward search, Maximov–Ekdahl, LIGHTER, SAT

### Takeaway
This is the most mature neighbouring literature, and its history calibrates what the whole family of ideas is worth: on the standard benchmark (AES MixColumns, 32×32 over GF(2)) the best count moved 97 → 95 → 94 → 92 → 91 → 89 between 2017 and 2025, about 8% in total, with randomised tie-breaking plus restarts worth about 2–3% (the 92 step is from background knowledge only, and the counts mix two slightly different XOR cost metrics, so the trajectory is indicative). The transferable parts are the global "sum of distances to all targets" selection rule with a norm tie-break, random tie-breaking with many restarts, and making one greedy run very fast; the backward and forward–backward frameworks correspond to things already tried here.

### Cited Findings

**Problem and classic heuristics**
- The problem is to compute a set of linear forms over GF(2) with the fewest XORs; it is MaxSNP-complete. Programs that exploit cancellation (x ⊕ x = 0) can be strictly shorter than cancellation-free ones: the paper's example needs 6 lines with cancellation and 8 without. [V-read] — [Fuhs & Schneider-Kamp, SAT 2010](https://www.imada.sdu.dk/u/petersk/papers/SAT10-slp.pdf)
- Boyar–Peralta (BP) heuristic: keep a base of computed signals and, for each target, the distance = fewest further XORs of base elements needed; repeatedly add the pairwise sum that minimises the total distance, break ties by the largest Euclidean norm of the distance vector, and emit a target immediately when it is one XOR away. [U-bg] — [Boyar, Matthews & Peralta, J. Cryptology](https://rd.springer.com/content/pdf/10.1007/s00145-012-9124-7.pdf)
- Kranz, Leander, Stoffelen & Wiemer (FSE 2018) applied global SLP heuristics (including Paar's and BP) to MDS matrices and reported the best AES MixColumns implementation at the time. [V-abs] — [ePrint 2017/1151](https://eprint.iacr.org/2017/1151) That count was 97 XORs. [V-abs] — [stated in the abstract of ePrint 2019/856](https://eprint.iacr.org/2019/856)

**Randomisation and new selection criteria**
- Banik, Funabiki & Isobe (IWSEC 2019): "By suitably including random bits in the instances of the above algorithms" (BP and Paar) they reached 95 XORs for AES MixColumns and improved almost all matrices of the earlier study. [V-abs] — [ePrint 2019/856](https://eprint.iacr.org/2019/856)
- Tan & Peyrin (TCHES 2020(1)): revisits BP, argues that randomising the selection phases gives large improvements, and adds new selection criteria (search summaries and later papers name the resulting algorithms RNBP, A1 and A2; the names were not on the abstract page). AES MixColumns at 94 XORs; better than Paar, BP and Yosys on random matrices of various densities; applicable up to about 32×32. [V-abs] — [ePrint 2019/847](https://eprint.iacr.org/2019/847)
- The benefit of randomisation grew with matrix size and density. [U-search] — [Tan & Peyrin, TCHES](https://tches.iacr.org/index.php/TCHES/article/view/8398)
- Huang, Sun, Wu & Chen (ePrint, October 2026): a meet-in-the-middle step lowers the time complexity of BP and its variants (A1, A2, BP-LSL), and a GPU implementation with candidate pruning solves a 26-dimensional density-0.5 matrix in 9.44 s on a GTX 1650, over 6,200x faster than the existing single-threaded implementation; an RTX 4090 extends the range to 64-dimensional sparse matrices. New records were set with accelerated A1. [V-abs] — [ePrint 2026/2520](https://eprint.iacr.org/2026/2520)

**Decomposition, reduction rules and local re-optimisation**
- Xiang, Zeng, Lin, Bao & Zhang (ToSC 2020(2)): in the sequential-XOR metric the cost of an invertible matrix is tied to its decomposition into elementary matrices; the method generates "various matrix decompositions", optimises each with matrix-multiplication rules over F2, and keeps the best. It "performs equally good or outperforms Paar's and Boyar-Peralta's heuristics in most cases". [V-abs] — [ePrint 2020/903](https://eprint.iacr.org/2020/903)
- There are seven such rules, and the AES MixColumns result was 92 XORs. [U-search for "seven"; U-bg for 92] — [ePrint 2020/903](https://eprint.iacr.org/2020/903)
- A ToSC 2024 follow-up starts from an existing implementation, uses several reduction rules and iteratively searches for subsequences that satisfy them; it reports 91 XORs at depth 13 for AES MixColumns. [U-search] — [A Framework to Improve the Implementations of Linear Layers](https://tosc.iacr.org/index.php/ToSC/article/view/11633)
- Sun, Yang & Li (ePrint 2025/1493, revised November 2025): a faster BP implementation based on linear combinations, plus "a new strategy for selecting subsequences during local optimization" that replaces the random selection of earlier work; first 89 g-XOR implementation of the AES linear layer, previous best 91. [V-abs] — [ePrint 2025/1493](https://eprint.iacr.org/2025/1493)

**Backward and combined frameworks**
- Liu et al. (ToSC 2022): backward search that starts from the outputs and repeatedly splits each output into an XOR of two signals until all inputs appear, aimed at low depth; AES MixColumns with 103 XORs at depth 3; better XOR counts for 54.3% of 4,256 MDS matrices from an earlier study. [V-abs] — [ePrint 2022/231](https://eprint.iacr.org/2022/231)
- A 2023 ToSC paper combines forward and backward search to enlarge the search space. [U-search; the URL-to-paper attribution was not confirmed] — [ePrint 2023/174](https://eprint.iacr.org/2023/174.pdf)

**Other tools named in the brief**
- Maximov & Ekdahl (TCHES 2019): methods to find the smallest circuit for a linear map under a maximum-depth constraint, with inputs arriving at different delays; applied to AES S-boxes. [V-abs] — [ePrint 2019/802](https://eprint.iacr.org/2019/802)
- LIGHTER (Jean, Peyrin, Sim & Tourteaux, FSE 2018): tool for optimal implementations of 4- and 8-bit mappings under a weighted instruction set, keyword meet-in-the-middle; beats ABC's area-optimised synthesis on 4-bit permutations. [V-abs] — [ePrint 2017/101](https://eprint.iacr.org/2017/101)
- Stoffelen (FSE 2016): SAT solvers used to optimise small functions such as S-boxes for several criteria (non-linear gate count, total gates, depth). [V-abs] — [ePrint 2016/198](https://eprint.iacr.org/2016/198)

### Inferences
- What transfers, in order of how new it is relative to what we have tried:
  1. **Global selection by total distance** (inference). Choose the next instruction that most reduces the sum, over all remaining targets, of an estimated remaining cost given the current pool, with the Euclidean-norm tie-break (prefer bringing a few targets very close over bringing all slightly closer). This is the GF(2) cousin of Hcub's cumulative benefit, which notes/research.md already covers, so the new parts are the tie-break and the next item.
  2. **Random tie-breaking with many restarts** (inference). The SLP record went from 97 to 95/94 with this alone. For us it means: every time the constructive heuristic has candidates within a small margin, pick at random, and run thousands of restarts per puzzle. This overlaps with "per-puzzle best-of over several configurations" but at a much larger restart count and finer granularity.
  3. **Speed of one greedy run as the main lever** (inference). The 2026 GPU paper exists because the community concluded that more and faster randomised runs keep paying. A distance oracle for integers can be made cheap for distance ≤ 2: keep a hash set of all one-step results of the pool (about 4·48²/2 ≈ 4,600 values); a target t is at distance ≤ 2 if, for some pool value c and operation, the required partner (t − c, t + c, c − t, t/c, t·c, c/t, t/2, √t) is in that set.
  4. **Many equal-cost starting points before rewriting** (inference). Xiang et al. apply reduction rules to many different decompositions rather than to one solution. Rewrite rules applied to a single 130,000-level solution gave nothing in public reports; applying them across thousands of diverse constructions is the variant the SLP literature supports.
- What does not add anything new (inference): the backward framework is top-down reduction, and forward plus backward is meet-in-the-middle; both are on the already-tried list. Maximov–Ekdahl and LIGHTER address depth or tiny bit-widths and have no obvious counterpart here.
- Main obstacle (inference). In GF(2) with at most 32 inputs, the distance of a target is computed exactly by a bounded search. For 40–60-bit integers under + − × ÷ it cannot be computed beyond distance 2–3. Early in a construction most targets are 4 or more steps away, so a capped distance sum is flat exactly when guidance is needed. An upper-bound estimate (length of the best derivation our reduction search finds from the current pool) can stand in, but then the method is only as good as that search.
- Expected benefit (inference): low single-digit percent over the constructive heuristic it is attached to, by analogy with 97 → 94; no published number exists for integer programs. Compute cost: restarts × one construction; scales linearly and parallelises trivially.

### Gaps
- The exact definitions of RNBP, A1 and A2, the number of random runs Tan and Peyrin used, and their random-matrix tables could not be read (journal site and ePrint PDF both refused automated access).
- Xiang et al.'s rule list and the internals of the 2024 and 2025 local-optimisation papers were not read; how they pick subsequences is known only at abstract level.
- The Maximov–Ekdahl search algorithm and the LIGHTER graph search are verified only as existing, not in detail.
- No paper was found that ports the BP distance heuristic to integer arithmetic with multiplication.

## 4. SAT, SMT, CP, ASP and integer programming encodings for shortest straight-line programs with multiplication

### Takeaway
I found no published SAT, SMT, CP or ASP result for shortest integer straight-line programs with multiplication between computed values, and none for addition chains. In neighbouring problems, proofs of optimality stop at roughly 12–13 XOR lines for a small GF(2) instance, 12 gates for Boolean circuits, 7 shift/add instructions for a 17-bit constant and about 12-bit coefficients for constant multiplication, so exact solving of 40–60-bit windows beyond about 4–6 instructions is unlikely to beat the exhaustive enumeration already in use.

### Cited Findings

**GF(2) linear programs by SAT (Fuhs & Schneider-Kamp, SAT 2010)**
- Encoding: the decision problem "is there a program of length k" uses a k×n matrix B (which inputs line i reads), a k×k lower-triangular matrix C (which earlier lines it reads), exactly two ones per line, and a mapping from outputs to lines; size O(n·k²). Linearity removes the universal quantifier over inputs: two linear forms are equal iff their coefficients are. [V-read] — [Fuhs & Schneider-Kamp](https://www.imada.sdu.dk/u/petersk/papers/SAT10-slp.pdf)
- Search over k: start from a high k, and after each SAT answer set k to (used length − 1), so that only the final call is UNSAT. The authors note that solutions returned for k above the minimum typically use fewer than k lines, so the descent takes large steps. They rejected MaxSAT because the decision problems near the optimum were already too hard. [V-read] — [Fuhs & Schneider-Kamp](https://www.imada.sdu.dk/u/petersk/papers/SAT10-slp.pdf)
- Results: for a 21×8 matrix from the AES S-box, a length-23 program (equal to the best known) was found in under one minute with MiniSAT 2.1, but UNSAT for k = 22 was not proved after more than 40 days on several solvers. For the first 8 of the 21 forms, the minimum is 13; UNSAT for k = 12 took 76.8 s with symmetry breaking and was not finished in 4 days without it. [V-read] — [Fuhs & Schneider-Kamp](https://www.imada.sdu.dk/u/petersk/papers/SAT10-slp.pdf)
- What helped and what did not: forbidding duplicate values and trivial lines, implied cardinality constraints and ordering independent lines by a lexicographic order on their values (symmetry breaking) helped. Unary encodings were "prohibitively expensive"; pseudo-Boolean solvers (MiniSat+, Pueblo, SAT4J, SCIP) gave no improvement. The authors' summary: such synthesis problems are "a major challenge for today's SAT solvers even on instances with 'just' 1500 variables". [V-read] — [Fuhs & Schneider-Kamp](https://www.imada.sdu.dk/u/petersk/papers/SAT10-slp.pdf)

**Boolean circuits by SAT**
- State of exact synthesis in 2022: circuits of size ≤ 6 in seconds; sizes 7–12 "sometimes" in days; size ≥ 13 out of reach. Proving non-existence takes much longer than finding a circuit: for one 4-input function, size 7 was found in 0.2 s and size 6 refuted in 1,178.8 s. [V-read] — [Kulikov, Pechenev & Slezkin, arXiv 2102.12579](https://arxiv.org/abs/2102.12579)

**Integer arithmetic by SMT**
- A Z3 model for the shortest shift/add/subtract program multiplying by a constant: 32-bit bit-vector registers, a fixed step count increased until satisfiable, per-step selectors for operation and operands, and two parallel chains (starting from 0 and from 1) to pin the function. Reported times: constant 1234, 6 instructions, about 23 s; 12345, 7 instructions, about 150 s; 123456, 7 instructions, about 17 minutes. The author notes the solver gets "slower and slower" as operations are added. [V-fetch] — [SAT/SMT by Example, constant multiplication](https://smt.st/current_tree/synth/pgm/mult/main.tex)
- In stochastic superoptimisation of x86 code, the bit-vector validator "diverges with several multiplications", which were therefore treated as uninterpreted functions. [V-fetch] — [Schkufza, Sharma & Aiken, Stochastic Superoptimization](https://ar5iv.arxiv.org/html/1211.0557)
- Component-based synthesis of loop-free bit-vector programs with SMT, and EVM superoptimisation where 256-bit width is a major difficulty, are the nearest program-synthesis references. [U-search] — [Gulwani et al., PLDI 2011](https://www.csl.sri.com/~tiwari/papers/pldi2011-bitvector.pdf), [Blockchain Superoptimizer](https://arxiv.org/pdf/2005.05912)

**Constant multiplication (shift-and-add) by CP, SAT and ILP beyond what research.md covers**
- Cantaloube, Fiege, Volkova & Solnon (arXiv, May 2026): optimal multiple-constant-multiplication methods handle only moderate sizes, about 12 bits. For word lengths from tens to thousands of bits they decompose constants into (possibly overlapping) patterns, solve the pattern set with optimal models, and reconstruct optimally, using a mix of constraint programming and SAT at each step; they report consistently beating existing baselines. [V-abs] — [arXiv 2605.23998](https://arxiv.org/abs/2605.23998)
- Other exact encodings exist: a SAT-based bit-level formulation by Fiege, Kumm & Zipf (IEEE TCAS), a SAT-based constraint engine for single and multiple constants by Lagoon & Metodi (ModRef 2020), and a pseudo-Boolean formulation by Lopes, Aksoy, Manquinho & Monteiro. [U-search] — [dataset record for Fiege et al.](https://daks.uni-kassel.de/entities/dataset/23c8ed64-09b6-479a-b9b0-50442ee45302), [Lopes et al.](https://www.academia.edu/144313492/Optimally_Solving_the_MCM_Problem_Using_Pseudo_Boolean_Satisfiability)

**Summary of what has been solved to optimality (from the findings above)**

| Problem | Largest size with a proof or exact answer | Source tag |
|---|---|---|
| GF(2) linear program, 8 outputs × 8 inputs | 13 lines proved minimal | [V-read] |
| GF(2) linear program, 21 outputs × 8 inputs | 23 lines found, minimality open after 40 days | [V-read] |
| Boolean circuit, any binary gates | ≤ 12 gates, sometimes, in days | [V-read] |
| Shift/add/sub constant multiplier, 32-bit | 7 instructions for a 17-bit constant, 17 minutes | [V-fetch] |
| Multiple constant multiplication, optimal | about 12-bit coefficients | [V-abs] |
| Integer program with × and ÷ on computed values | nothing found | — |

### Inferences
- Our instance is easier than general synthesis in one way and harder in another (inference). Easier: there are no inputs, so no universal quantifier and no test vectors; an encoding only needs k instructions with operand selectors and 60-bit value variables. Harder: a multiplication of two computed 60-bit values is a full 60×60 multiplier per instruction in a bit-level encoding, and asking a solver for a and b with a·b equal to a target is a factoring-type query. Every piece of evidence above points to solver trouble with wide multiplication.
- Realistic exact window (inference): about 4–6 instructions over the current pool, which the existing exhaustive short-window resynthesis already covers faster. A CP-SAT model with 60-bit integer variables is legal only while products stay inside 64 bits, and its multiplication propagation is bounds-based, so I expect it to be slower than enumeration.
- The useful solver formulation is over a finite candidate set, not over bit-vectors (inference). Collect, per puzzle, every derivation `v = a op b` seen in any run of any heuristic (thousands of restarts) into one hypergraph. Then solve: binary variable per value (computed or not) and per derivation; each target needs one chosen derivation; a chosen derivation needs both operands computed or initial; acyclicity by order variables or lazy cycle cuts; minimise the number of computed values. This is optimal recombination at instruction granularity. Caveat: a public repository reported zero gain from recombining 656 whole-program alternatives at 132,542, so the benefit depends on the pooled derivations being diverse, which is what sections 1 and 3 would supply.
- Transferable encoding tricks if a solver is used anyway (inference): forbid duplicate values; impose a canonical order on independent instructions; descend in k from a known solution rather than bisecting, so that almost all calls are satisfiable; do not expect optimality proofs.
- The 2026 "decompose, optimise, reconstruct" pattern for very large constants is windowing plus an exact chain on the digit set. Horner/windowing is already known to be poor here (two instructions per digit), so it does not help.
- Expected benefit (inference): pure exact synthesis, none beyond current enumeration; candidate-set recombination, unknown and possibly zero. Compute cost: one ILP/CP-SAT solve per puzzle with 10^4–10^6 derivation variables, minutes each.

### Gaps
- No SAT, SMT, CP, ASP or ILP paper on shortest addition chains or on integer straight-line programs with multiplication was found in two targeted searches.
- Limb splitting of 60-bit values and modular-hash (fingerprint) constraints for this purpose: nothing found in the literature; I cannot say whether anyone has tried them.
- The Fiege–Kumm–Zipf, Lagoon–Metodi and Lopes et al. encodings and their solved sizes were not read.
- How fast modern SAT solvers handle a single 60-bit factoring-type constraint was not checked against a source.

## 5. Anytime frameworks: large-neighbourhood search with exact sub-solvers, ruin-and-recreate on DAGs, iterated greedy, restarts and portfolios

### Takeaway
Two frameworks with real evidence differ from what was tried: SAT-based local improvement over connected multi-output sub-DAGs (new circuit-size upper bounds, but each exact call is limited to about 5–7 gates), and plateau random walks with a solution pool as in flip graphs for matrix multiplication (records found by 10^6–10^8 equal-cost moves with rare reductions). Stochastic superoptimisation by MCMC is a poor fit because exact integer targets give its cost function nothing to climb.

### Cited Findings

**SAT-based local improvement (SLIM) on circuits**
- Method: go through all subcircuits of a fixed moderate size in a given circuit and ask a SAT solver whether a smaller subcircuit computes the same outputs; the authors call it local search "in a ball around a given circuit". Their library call uses connected subcircuits of size 5; the paper's stated aim is size 7. [V-read] — [Kulikov, Pechenev & Slezkin](https://arxiv.org/abs/2102.12579)
- Results: a size-11 circuit for the 5-input sum function is found in a few seconds from the standard size-12 one; the upper bound for MOD-3 functions improves from 3n − 4 to 3n − 5 − [(n + r) ≡ 0 mod 3], matching a conjecture of Knuth; new bounds for threshold functions. Improvements on small circuits are then generalised by hand to all input sizes. [V-read] — [Kulikov, Pechenev & Slezkin](https://arxiv.org/abs/2102.12579)
- The same scheme had earlier been applied to branchwidth, treewidth, treedepth, Bayesian network structure learning and decision trees. [V-read] — [Kulikov, Pechenev & Slezkin](https://arxiv.org/abs/2102.12579)
- eSLIM (SAT 2024): exact resynthesis of multi-output subcircuits with don't-cares computed relative to an enclosing window instead of the whole circuit, trading completeness for speed; second place on the IWLS 2023 functions and improvements over the best known implementations of some of the largest EPFL benchmark circuits. [V-abs] — [Reichl, Slivovsky & Szeider, eSLIM](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2024.23)
- The same group partitions a circuit into layers so that windows can be optimised independently and in parallel without creating cycles; an earlier version used QBF. [U-search] — [TU Wien technical report AC-TR-24-001](https://www.ac.tuwien.ac.at/files/tr/ac-tr-24-001.pdf)

**Plateau random walks with a pool (flip graphs, Kauers & Moosbauer 2022)**
- Method: vertices are multiplication schemes; a flip is a reversible move that keeps the number of multiplications; a reduction lowers it by one. A random walk takes flips and checks at every step whether the current scheme or a neighbour is reducible. The pool variant keeps a set of schemes at rank r, walks from random members with a path limit, collects the first schemes found at rank r − 1 until it has s of them, and recurses; the experiments used a path limit of 10^6 and s = 20,000, starting from the standard algorithm only. [V-fetch] — [Flip Graphs for Matrix Multiplication](https://ar5iv.labs.arxiv.org/html/2212.01175)
- Reductions are rare: in one small component, 7 of 1,183 edges were reductions; for 3×3, no scheme within distance 2–4 of the standard algorithm was reducible. A C implementation explores paths of length 10^8 in minutes with almost no memory. [V-fetch] — [Flip Graphs for Matrix Multiplication](https://ar5iv.labs.arxiv.org/html/2212.01175)
- Results: (4,4,5) from 63 to 60 over Z2 and to 62 over any field; (5,5,5) from 96 to 95 over Z2 and from 98 to 97 over any field; all other formats up to 5 matched the best known. Starting from an existing rank-96 scheme, rank 95 was found "within seconds". For 3×3 no rank-22 scheme was found. [V-fetch] — [Flip Graphs for Matrix Multiplication](https://ar5iv.labs.arxiv.org/html/2212.01175)
- A symmetry-restricted version later gave 93 multiplications for 5×5 and 153 for 6×6. [U-search] — [Moosbauer & Poole, arXiv 2502.04514](https://arxiv.org/html/2502.04514v1)

**Stochastic superoptimisation (STOKE, ASPLOS 2013)**
- Method: Metropolis–Hastings over fixed-length programs (50 slots padded with an UNUSED token); moves change an opcode, change an operand, swap two instructions or replace an instruction; cost = graded incorrectness on test cases (Hamming distance of outputs) plus a performance term; a synthesis phase from random code uses correctness only, an optimisation phase from a correct program uses both and may pass through incorrect programs. [V-fetch] — [Stochastic Superoptimization](https://ar5iv.arxiv.org/html/1211.0557)
- Results and limits: matched or beat gcc and icc at full optimisation on its benchmarks, with 30 minutes per phase on 40 dual-core machines. Synthesis failed on three benchmarks whose outputs differ from a trivial wrong function by a single bit, because the cost gives little guidance; the authors say synthesis works best when a correct program can be found piece by piece. [V-fetch] — [Stochastic Superoptimization](https://ar5iv.arxiv.org/html/1211.0557)

**Restarts and portfolios**
- Spread across independent runs is wide and the records sit in the tail: 2 of 28 NRPA runs reached the Morpion 5T record of 177, against a median of 171. [V-read] — [Rosin, NRPA](https://cs.uwaterloo.ca/~jhoey/rgwiki/uploads/11IJCAI-NRPA-Rosin.pdf)
- For the SAT descent in k, solutions for k above the minimum are plentiful and found in seconds, while the last step is the hard one. [V-read] — [Fuhs & Schneider-Kamp](https://www.imada.sdu.dk/u/petersk/papers/SAT10-slp.pdf)

### Inferences
- **Connected multi-output neighbourhoods** (inference). The circuit literature removes a connected sub-DAG of 5–7 nodes and re-solves for all values the rest of the program needs from it, given the values that feed it. Our tried neighbourhoods were contiguous instruction windows and one node's private ancestors. The difference is joint re-derivation of several needed values from a shared boundary. A public repository reported zero gain from 6–10-target cluster optimisation, so this may already be exhausted; the remaining untested part is choosing clusters by DAG connectivity rather than by target similarity. Expected benefit: small. Cost: one bounded exhaustive search per cluster, thousands of clusters per puzzle.
- **Plateau walks with a pool** (inference). This is the framework most unlike what has been tried. Define neutral moves that keep length and validity: swap the derivation of a value for another of equal cost; reassociate `(a+b)+c` to `a+(b+c)` or `(a·b)·c` to `a·(b·c)`, which replaces one intermediate value by another; replace an intermediate x by x′ where both x and its single consumer can be re-derived in the same number of steps. After each move, test for a reduction: a value that now duplicates another, or a value now reachable in one step from the others so that an instruction dies. Keep a pool of distinct programs at the best length, walk from random members, and when a shorter program appears start a new pool. Occasionally accepting a +1 move is a natural extension.
  - Why it might work: reports that local search yields nothing at 130,000 are what a plateau with very rare improving moves looks like, and the flip-graph result is that such plateaus give way only to walks of 10^6–10^8 cheap steps, far beyond what a strictly improving search visits.
  - Cost: needs an incremental evaluator at microseconds per move; then 10^7 moves per puzzle is seconds to minutes, and 1,000 puzzles fit in a few CPU-days.
  - Why it might fail: matrix multiplication schemes have a large symmetry group, so neutral moves are abundant and the flip graph is connected. A program for random-looking 40–60-bit targets may have very few equal-length alternatives per value, so the plateau could be thin and walks short. Validity (value_limit, positivity, exact division, 48 registers) further restricts moves. No source tests this on integer programs.
- **MCMC with graded correctness** (inference): not recommended. STOKE's own failure case is a needle-like cost, and "is this exact 50-bit integer produced" is a needle. A graded proxy such as numeric closeness to a target is only informative when the remaining difference is small, which the reduction search already exploits.
- **Restart policy** (inference). Given heavy-tailed outcomes, many short independent runs per puzzle with different seeds, keeping the per-puzzle best, should come before any long single run; puzzles where the best-of-N curve is still falling deserve more restarts.
- **Overall ranking of the catalogue for this problem** (inference; ordered by evidence strength times novelty relative to the tried list):
  1. NRPA or NMCS level 1–2 wrapped around the existing reduction heuristic, move code = (value, decomposition). Section 1.
  2. Boyar–Peralta-style total-distance selection with norm tie-break, random tie-breaking and thousands of restarts, with a fast distance-≤2 oracle. Section 3.
  3. Plateau random walks with a pool and cheap reduction checks. This section. Highest variance: could be the only thing that moves a 130,000-level solution, or could do nothing.
  4. Instruction-level optimal recombination of all derivations seen across runs, by ILP or CP-SAT. Section 4. Only worth doing after 1 or 2 supply diverse derivations.
  5. Not recommended: GA/AIS/PSO/ACO on chains, plain UCT, STOKE-style MCMC, bit-level SAT/SMT synthesis of windows longer than about 6 instructions.
- Calibration (inference): in the best-studied analogue, eight years of all these ideas together moved the benchmark by about 8%. Our current gap to public notebooks (147,310 against roughly 128,500–132,500) is larger than that, so reproducing the public constructive methods is likely worth more than any single framework here; the frameworks matter for going below the public level.

### Gaps
- No source was found for ruin-and-recreate or iterated greedy applied specifically to addition chains, addition sequences or arithmetic straight-line programs.
- A follow-up to the flip-graph work reportedly adds rank-increasing moves to escape local minima and cuts run time sharply; I saw this only in a search summary and could not tie it to a specific paper, so it is not cited above.
- eSLIM's window-selection rule, exact-synthesis size limit and percentage savings were not on the abstract page.
- Nothing found quantifies how many equal-length neighbours a typical integer straight-line program has, which is the fact that decides whether plateau walks can work here.
