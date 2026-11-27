# Start-up phase of a multi-target arithmetic program: theory and algorithms

Evidence labels used throughout:

- **[verified]** read in the source text (directly, or through a full-text fetch of the paper or page)
- **[abstract]** abstract or search-result summary only
- **[unverified]** background knowledge, no source read in this round
- **[estimate]** my own computation, run in memory on `data/puzzles.csv` or on the OEIS terms; nothing was written to the project
- **[inference]** my mapping onto the competition setting

Terms: an *instruction* is one `a op b`. A *state* is the set of values a program has computed so far. *Depth d* means reachable within d instructions of the start values. The *later rate* is the per-target cost after the fifth target (6.88 for 56–63-bit puzzles, 5.75 for 48–55 bits). The *excess* is the cost of the first five targets minus five times the later rate (34.1 and 36.3 instructions in those two classes).

Nothing here repeats the four earlier reports or `notes/research.md`. Integer complexity, the OEIS counts, the smallest-grammar link and Bertsekas's rollout theory do not appear in them.

## 1. Integer-complexity algorithms: what makes them fast, and does it suggest better reductions?

### Takeaway
The algorithms are fast because an optimal sum almost never needs a smaller summand above 9, so the search collapses to "divide, or subtract a tiny constant then divide". This confirms the shape of our `v = q·b ± c` reduction and does not supply a new rule. The transferable parts are a memo table keyed by near-quotients and a complete cost table for all small integers.

### Cited Findings
- Integer complexity ‖n‖ is the fewest ones needed to write n with + and ×. It satisfies ‖n‖ = min of ‖a‖+‖b‖ over a+b=n or a·b=n. Brute force is O(N²). [verified] — [Arias de Reyna & van de Lune, arXiv:1404.2183](https://arxiv.org/abs/1404.2183)
- Only summands up to `kMax` need testing. With target = ‖n−1‖ and E(k) the largest number of complexity k, lower t from target/2 while E(t)+E(target−t) < n, then kMax = E(t). They prove kMax ≤ 2·n^0.585. For 2 ≤ n ≤ 50, kMax is 1 except at n = 24 and 48. [verified] — [same paper](https://ar5iv.arxiv.org/html/1404.2183)
- E(3j) = 3^j, E(3j+1) = 4·3^(j−1), E(3j−1) = 2·3^(j−1). The size a formula can reach grows multiplicatively in its cost, which is why two comparable summands are wasteful. [verified] — [same paper](https://ar5iv.arxiv.org/html/1404.2183)
- Only "solid" numbers need testing as the smaller summand (b is solid if no split b = u+v has ‖u‖+‖v‖ = ‖b‖). They begin 1, 6, 8, 9, 12. [verified] — [same paper](https://ar5iv.arxiv.org/html/1404.2183)
- Running time is O(N^1.230175). Fuller's variant has the same time with O(N^0.79) space and reached N = 10^11 in about 106 hours. [verified] — [same paper](https://ar5iv.arxiv.org/html/1404.2183)
- Up to 10^12, "the smaller addendum does not exceed 9". Only 21,360 numbers need 6, 8 or 9 (8 for exactly 3 numbers, 9 for 119), and 12 or more was never needed. The proven bound is a ≤ 2·n^0.585 for n ≥ 29. [verified] — [Iraids et al., arXiv:1203.6462](https://ar5iv.labs.arxiv.org/html/1203.6462)
- The rule "‖p‖ = 1 + ‖p−1‖ for primes" first fails at p = 353,942,783. Bounds are 3·log₃n ≤ ‖n‖ ≤ 3·log₂n, and the worst observed ratio ‖n‖/log₃n is 3.928 at n = 1439. [verified] — [Iraids et al.](https://ar5iv.labs.arxiv.org/html/1203.6462)
- Running the same analysis in higher bases gives O(N^1.222911236); the sums are the rate-limiting step. [abstract] — [Cordwell et al., arXiv:1706.08424](https://arxiv.org/abs/1706.08424)
- All n ≤ N can be done in O(N·polylog N), by treating the sum step as an online (min,+)-convolution with entries bounded by O(log n). [verified] — [He, arXiv:2308.10301](https://ar5iv.labs.arxiv.org/html/2308.10301)
- A single n can be done in O(n^0.6154), the first sublinear method. The smaller summand is at most L(n) = n^ℓ with ℓ ≤ 0.3749. The only values needed lie in intervals [n/d − L, n/d] for integers d ≥ 1. Values up to n^t are tabulated once and the intervals are filled by recursion. [verified] — [He](https://ar5iv.labs.arxiv.org/html/2308.10301)
- Average complexity is about 3.29·log₃n, sampled up to about 10^25. The paper does not treat subtraction or straight-line programs. [verified] — [He](https://ar5iv.labs.arxiv.org/html/2308.10301)

### Inferences
- **Why the small-summand fact holds, and what survives reuse.** In a formula each value is used once, so a sum of two large parts is bounded by E(k₁)+E(k₂), far below E(k₁+k₂). With reuse this argument weakens: adding two values already in the pool costs one instruction. For a fresh large value at start-up the same pressure remains, for a different reason. Cheap table values are abundant at mid size and sparse near target size (section 2), so a target-size value is best reached as a product of abundant mid-size values plus small corrections.
- **Mapping.** He's interval structure is our `v = q·b ± c` rule applied recursively: every useful sub-value of t is a near-quotient ⌊t/d⌋ − j with j small. Because ⌊⌊t/a⌋/b⌋ = ⌊t/(ab)⌋, different reduction orders reach the same sub-problem. A memo keyed by (divisor product, small offset) would stop a best-first search re-exploring them.
- **Second mapping.** The near-linear all-n method suggests a complete cost table for every integer below N (say 2^24 to 2^27) built from the puzzle's own start values. It would price any remainder or quotient below N, where the breadth-first table knows only 10^4 to 10^5 values.
- **Expected benefit.** Small for the reduction rules, since they already match. Unknown for the full cost table. It is a tree cost that ignores sharing, so it is an upper bound.
- **Why it might not transfer.** The theorems are for {1, +, ×} formulas. With subtraction, exact division, start values other than 1 and reuse, the "summand ≤ 9" fact is unproven. It would have to be checked against the exhaustive table at depth ≤ 5 before being used to prune.

### Gaps
- Altman's and Altman–Zelinsky's papers were not read. They classify numbers by defect ‖n‖ − 3·log₃n and I expect no bearing on search, but that is unchecked.
- The sequel by Čerņenoks et al. ([arXiv:1409.0446](https://arxiv.org/abs/1409.0446)), which allows subtraction, was not read. Whether the small-summand fact survives subtraction is open here.

## 2. How many integers are reachable in n operations, and how are they spread over magnitudes?

### Takeaway
From the single start value 1 the count of reachable integers is known exactly to 11 steps (4.8·10^8) and multiplies by about 23 at that point. Extrapolated, a random 57–60-bit target needs about 13–16 instructions from typical start values, roughly twice the later rate. Every magnitude is reachable by depth 4–5, but large values are sparse, so density is the bottleneck.

### Cited Findings
- The number of integers obtainable from 1 in n steps of +, −, × is 1, 3, 6, 13, 38, 153, 867, 6930, 75986, 1109442, 20693262, 477815647 for n = 0..11. Negative values and zero are allowed. [verified] — [OEIS A216999](https://oeis.org/A216999)
- The number of distinct value sets produced by n-step programs from 1 (same operations, no repeated value) is 2, 5, 20, 149, 1852, 34354, 873386, 28671789, 1166062774, 56973937168, 3266313635225, 215667757729237 for n = 1..12, with a(n) ≥ 2(n−1)·a(n−1). [verified] — [OEIS A229662](https://oeis.org/A229662)
- Variants exist with division (rational values, A288849), positive values only (A214872) and non-zero values only (A229673). [abstract] — [OEIS A288849](https://oeis.org/A288849), [OEIS A214872](https://oeis.org/A214872)

### Inferences
- **Growth from the seed 1 [estimate].** Successive ratios of A216999 are 4.0, 5.7, 8.0, 11.0, 14.6, 18.7, 23.1 for n = 5..11, rising about 4.4 per step. Continuing that trend, the count passes 2^60 at about n = 17.
- **Collision loss [estimate].** A state with m values offers 2m²+m candidate instructions. The A229662 ratios are 2.05–2.2 bits below log₂ of that, steadily from step 5 to step 12. About 2 bits of each instruction's nominal choice are lost because different programs give the same set.
- **Our own tables [estimate].** Two real puzzles, values positive and within the limit, exact division:

  | | start values 5, 20, 33 (typical; median largest start value is 32 among the 231 puzzles with ≥ 20 targets and a 56–63-bit largest target) | start values 1270, 1675, 1917 |
  |---|---|---|
  | States at depth 1–4 | 16, 275, 5,698, 144,595 | 16, 280, 5,912, 150,853 |
  | Distinct values at depth ≤ 1..5 | 19, 126, 909, 8,501, 104,379 | 19, 139, 1,276, 14,516, 195,520 |
  | Loss against 2m²+1 candidates, depth 1–4 | 0.25, 0.94, 1.30, 1.52 bits | 0.25, 0.92, 1.27, 1.52 bits |
  | Values of 56–60 bits at depth ≤ 4 and ≤ 5 | 2 and 198 | 99 and 5,501 |

  This matches what we already measured (states ×20–35, values ×10, about 10^4 values at depth 4).
- **Magnitude profile [estimate].** With start values 5, 20, 33 the depth ≤ 5 table peaks at 16–20 bits (35,158 values) and thins by about half per 5 bits: 12,043 at 26–30 bits, 3,247 at 36–40, 761 at 46–50, 198 at 56–60. With 11-bit start values the mass sits at multiples of 11 bits. Reaching a magnitude is cheap. Having many values there is not.
- **Minimum cost of one target [estimate].** In the typical puzzle the count of 44-bit values goes from 4 to 296 between depth 4 and 5. Filling that band needs a further factor of 3·10^10, so depth 11–13 at growth ×20 to ×60 per instruction. The same sum for 57–60-bit targets gives depth 13–16 in both puzzles, in line with the OEIS extrapolation (17 from one seed, less about three steps of head start).
- **Fastest ladders.** One instruction makes one value, so a ladder with a value at each of k magnitudes costs at least k minus the number of start values. A squaring chain reaches 60 bits in 3–4 instructions from 5–11-bit start values. No published result improves on this, and the tables show it is not the constraint.

### Gaps
- No exact counts exist for several start values, exact division or a value limit. The figures above are mine, and the growth beyond depth 5 is extrapolated.
- No source gives the distribution of reachable values over magnitudes.

## 3. Three- and five-term table-driven decompositions for the first target

### Takeaway
I found no published work on this search. A test on real targets shows it works: with the depth ≤ 4 table alone, `t = (x·y ± z)·w ± u` built two 44-bit targets from scratch in 13 and 16 instructions, close to the 11–13 estimated minimum. The three-term form `x·y ± z` covers targets only up to about 45 bits, and only with a depth ≤ 5 table.

### Cited Findings
- The closest published method is He's single-target algorithm: a complete table of small values plus recursion over near-quotient intervals [n/d − L, n/d]. [verified] — [He, arXiv:2308.10301](https://ar5iv.labs.arxiv.org/html/2308.10301)
- Two searches for meet-in-the-middle or bidirectional search for shortest integer programs returned only the exhaustive-search papers already in `notes/research.md`. [abstract] — [Markström, arXiv:1306.3091](https://arxiv.org/abs/1306.3091)

### Inferences
- **Coverage rule [estimate].** A random target in a band of 2^(B−1) integers is expected to have (number of table products in the band) × (2·|T|)^(number of additive terms) / 2^(B−1) representations. Measured:

  | Form, table | 44-bit target, start values 5, 20, 33 | 60-bit target, start values 1270, 1675, 1917 |
  |---|---|---|
  | x·y ± z, depth ≤ 4 | 0.0009 | 6·10^-8 |
  | x·y ± z, depth ≤ 5 | 4.5 | 0.00015 |
  | (x·y ± z)·w ± u, depth ≤ 4 | 5·10^5 | about 9 |
  | (x·y ± z)·w ± u, depth ≤ 5 | 3·10^10 | 6·10^5 |

- **Test on real targets [estimate].** Typical puzzle, depth ≤ 4 table of 8,501 values, u restricted to below 2^22, pure Python.
  - Target 8,943,326,500,325: 183,123 representations found with 80% of the search done. The best is ((100·120 + 66)·741,200,605) + 395. It costs 14 counting each value separately and 13 after merging shared derivations.
  - Target 12,857,071,160,593: 57,307 representations. The best costs 20 separately and 16 merged.
  - Merging lowered the typical cost by about 2. Our best programs show their first target at instruction 32–37, but those instructions also build pool values, so the figures are not like for like.
- **Using shared derivations.** For each table value I stored the non-start values of the state in which it was first found. The joint cost of a form is the size of the union of those sets plus the combining instructions. Storing several derivations per value, or searching per state, would tighten it.
- **Expected benefit.** It gives hundreds of thousands of alternative ways to build the first target at 13–20 instructions each. The value lies in that choice. The cheapest form alone is not the goal, because what matters is which by-products it leaves for later targets.
- **Why it might not transfer.** A cheap first target does not lower the total unless its by-products are useful. For 56+-bit targets with small start values, large table values are scarce, so the depth ≤ 4 table may give no five-term hit. That case needs depth-5 values for some terms or one more level.

### Gaps
- The five-term search was not run on 56+-bit targets with small start values.
- No literature was found on choosing among many decompositions by the usefulness of their by-products.

## 4. Building several large targets together, and what sharing can save

### Takeaway
No algorithm with a guarantee exists for joint construction, and the nearest theory says a good one would settle an old open problem on addition chains. Counting gives a hard floor of 31 instructions for five unrelated 59.5-bit targets, which is below the 34.4 they would cost at the later rate. So counting does not prove any of the excess inherent.

### Cited Findings
- The smallest grammar for a string is hard to approximate within a small constant unless P = NP. An o(log n / log log n) approximation "would require progress on the well-studied addition chain problem". The paper's own algorithm achieves O(log(n/g*)). [verified] — [Charikar et al., STOC 2002](https://compression.ru/download/articles/grammar/charikar_2002_approximating_the_smallest_grammar.pdf)
- A compressor with that ratio would beat Yao's method for an addition chain containing a prescribed set of integers. Upper and lower bounds on the ratios of the practical compressors do not match for any of them. [abstract] — [Bannai et al., arXiv:1908.06428](https://arxiv.org/abs/1908.06428)
- A September 2026 preprint proves an Ω(log n / log log n) lower bound on the ratio of the Greedy grammar compressor, open for over twenty years. [abstract] — [Hucke, arXiv:2609.12106](https://arxiv.org/pdf/2609.12106)
- For directed Steiner trees, the greedy family repeatedly adds a low-density subtree (cost per newly connected terminal) and gives a tunable approximation ratio. The best quasi-polynomial ratio is O(log²k / log log k). [abstract] — [Charikar, Chekuri et al.](https://chekuri.cs.illinois.edu/papers/dir-steiner-talg.pdf), [Grandoni, Laekhanukit & Li](https://cse.buffalo.edu/~shil/papers/DST-STOC2019.pdf)

### Inferences
- **Mapping of the grammar result.** A set of targets built with + alone is a grammar for unary strings. Even there, no polynomial method is known to beat generic sharing by more than a log/log-log factor, and the common greedy compressors are provably off by that factor on some inputs. Do not look for an off-the-shelf joint constructor.
- **Mapping of the Steiner result.** Building targets one at a time, cheapest first, is the nearest-terminal rule. The density rule says to pick the bundle (shared intermediates plus the j targets they serve) with the lowest cost per target. It is a heuristic template only. Our derivation structure is a hypergraph, so the ratios do not carry over.
- **Hard floor [estimate].** A program of L instructions from 3 start values is one of at most ∏(2m²+m) programs, m = 3..L+2, and holds C(L+3, 5) five-subsets. Five independent random targets need about 5·(B−1) − log₂120 bits. This gives L ≥ 31 for 59.5-bit targets and L ≥ 27 for 51.5 bits.
- **Calibrated schedules [estimate].** At the later rate each instruction uses 72–75% of the nominal log₂(2·45²+45) = 12.0 bits. Applying the same efficiency to a pool growing from 3 values gives the instruction at which targets 1 to 5 appear:

  | Model | 59.5-bit targets | 51.5-bit targets |
  |---|---|---|
  | Measured | first 37.5, fifth 68.5 | first 32.0, fifth 65.0 |
  | Nominal capacity, later-rate efficiency | 12, 21, 29, 36, 43 | 11, 18, 25, 31, 38 |
  | Same, minus the 2-bit collision loss | 16, 26, 35, 44, 52 | 14, 23, 31, 38, 45 |
  | Five times the later rate | 34.4 | 28.8 |

  The first row of models reproduces our earlier 38–44 estimate. The second is the pessimistic end, since part of the 2-bit loss may already be inside the measured efficiency.
- **Reading.** Of the 34–36 instructions of excess per large puzzle, the models call 9–18 inherent (a quarter to a half) and 16–27 recoverable in principle. Both models count operand choices only. They ignore that few early values lie near target size, so the inherent share is probably higher than they say.

### Gaps
- No bound specific to several start values, four operations and 48 registers exists in the literature. The numbers above are mine.
- The Steiner and follow-up grammar papers were seen only as search summaries.
- The selection rules of RePair, Greedy and LongestMatch were not read in the journal version. [unverified]

## 5. Prefix optimisation with look-ahead

### Takeaway
Rollout is the published method that fits. It re-runs the existing solver from each candidate next decision and keeps the best, and its "fortified" form is proven never to be worse than the base solver. It costs one solver run per candidate per decision. I found no two-stage or bilevel formulation specific to this kind of problem.

### Cited Findings
- Rollout: at each step, run the base heuristic H from every neighbour of the current partial solution and move to the neighbour whose completed solution is cheapest. [verified] — [Bertsekas, Rollout Algorithms for Discrete Optimization: A Survey](https://www.mit.edu/~dimitrib/Rollouts_Survey.pdf)
- H is *sequentially consistent* if, restarted from any node on a path it generated, it generates the rest of that path. It is *sequentially improving* if H(i) ≥ min of H(j) over neighbours j. In either case the rollout solution costs no more than H's (Propositions 1 and 2). [verified] — [same survey](https://www.mit.edu/~dimitrib/Rollouts_Survey.pdf)
- *Fortified rollout* also carries the best complete solution found so far and follows it when no candidate beats it. This gives the improvement guarantee for any base heuristic. [verified] — [same survey](https://www.mit.edu/~dimitrib/Rollouts_Survey.pdf)
- Several base heuristics can be combined by taking the best, which keeps the guarantee. Two-step look-ahead may drop neighbours "judged less promising" to limit the number of runs. [verified] — [same survey](https://www.mit.edu/~dimitrib/Rollouts_Survey.pdf)
- Cost: the extra computation is the base heuristic's time multiplied by a low-order polynomial of problem size. In the worked example, rollout has O(N) times the greedy's success probability for O(N) times the computation. [verified] — [same survey](https://www.mit.edu/~dimitrib/Rollouts_Survey.pdf)
- The original paper is Bertsekas, Tsitsiklis & Wu, Journal of Heuristics 3 (1997). The "pilot method" is described as the same approach under another name. [abstract] — [paper](https://www.mit.edu/~jnt/Papers/J066-97-rollout.pdf), [arXiv:1210.0374](https://arxiv.org/pdf/1210.0374.pdf)

### Inferences
- **Mapping.** Our constructive solver is H. A decision is "which target next, by which decomposition". A local search on the finished program cannot change the early part, so re-running H from alternative prefixes is the only way to measure what an early choice does to everything after it.
- **What is new against the earlier reports.** They record a public engine gaining 1.1% (34,560 → 34,181) from choosing only the first target by look-ahead, and they cover NRPA, a different, policy-learning method. Rollout over the first three to five decisions, with section 3's alternatives as candidates and the fortified rule, has not been tried.
- **Truncation.** The rate is steady after about five targets. A candidate can therefore be scored by its cost through target 8 plus the later rate times the remaining targets, which cuts each run to about a quarter.
- **Expected benefit.** Bounded above by the recoverable share in section 4. The only measured point is the 1.1% for a one-step version.
- **Why it might not transfer.** Our solver is neither sequentially consistent nor deterministic across settings, so only the fortified form carries a guarantee, and that guarantee is merely "not worse". If H's later rate hardly depends on the early pool, all candidates score alike.

### Gaps
- Two-stage, bilevel and grammar seed-selection formulations were not searched for lack of budget.
- No published measurement of rollout on arithmetic-program construction was found.

## 6. Is the start-up cost inherent, and what should be tried, in order?

### Takeaway
The literature does not settle it. No theorem makes the excess inherent, and the hard counting floor (31) is below the later-rate cost (34.4). My calibrated models put a quarter to a half of the excess as inherent, and likely more because early large values are sparse. A table search already builds a single first target within about 3 instructions of its estimated floor, so making that target cheaper is not the lever. Any gain must come from which by-products the first targets leave behind.

### Cited Findings
- Fortified rollout never does worse than its base heuristic. [verified] — [Bertsekas survey](https://www.mit.edu/~dimitrib/Rollouts_Survey.pdf)
- Distinct value sets from one seed number 2.2·10^14 at 12 steps, so exact joint search stops near 10–12 instructions. [verified] — [OEIS A229662](https://oeis.org/A229662)
- Good approximation of joint additive construction would need progress on the addition-chain problem. [verified] — [Charikar et al.](https://compression.ru/download/articles/grammar/charikar_2002_approximating_the_smallest_grammar.pdf)

### Inferences
Everything below is my inference. The 23,477-instruction excess is the ceiling. If the two measured classes are representative, the models allow at most half to three quarters of it in principle, and realistic gains are a fraction of that.

**1. Diagnostic first: optimise the prefix as its own puzzle.** This uses existing tools and decides whether the gap is real. On a five-target sub-puzzle the whole program is "early", so the local search can change it.

```
for a sample of large puzzles:
    for k in (1, 3, 5, 8):
        sub   = puzzle restricted to the k targets our best program builds first
        p_k   = best program for sub, using every tool including local search
        full  = solve(puzzle, forced_prefix = p_k)
        record len(p_k), len(full), and the per-target rate after target k
compare len(p_5) with 68.5 (65.0), and len(full) with the current best
```
If `len(p_5)` is near 45–52 and the later rate is unchanged, the gap is recoverable and items 2–4 are worth building. If `len(p_5)` stays near 65, or the later rate rises by what the prefix saved, the excess is pool investment and the topic can be closed.

**2. Fortified rollout over the first decisions.**

```
best   = solve(puzzle)
prefix = []
for step in 1..K:                                  # K = 3 to 5 decisions
    cands = top-M (target, decomposition) choices given prefix
    for c in cands:
        prog = solve(puzzle, forced_prefix = prefix + c)     # or the truncated score
        if len(prog) < len(best): best = prog
    c* = candidate with the shortest prog
    if that prog is longer than best and best starts with prefix:
        c* = the decision best makes at this step            # fortified rule
    prefix = prefix + c*
return best
```
Cost is K·M solver runs per puzzle. Start with M = 8, K = 3 on the 231 puzzles with a 56–63-bit largest target.

**3. Five-term table search as the candidate generator for item 2.**

```
T  = values within 4 instructions, with depth[v] and deriv[v]
     (deriv[v] = non-start values of one program that makes v)
Us = values of T below 2^22;  Xs = sorted values of T that are >= 2
for w in T:
    r = t mod w
    for (u, s) with u in Us, s in {+1, -1}, u ≡ s·r (mod w):
        q = (t - s·u) / w                          # keep if 1 <= q <= value_limit
        if q in T: emit (q, w, u)
        for x in Xs with x <= sqrt(q):
            for y in (q div x, q div x + 1):
                if y in T and |q - x·y| in T or 0: emit (x, y, q - x·y, w, u)
joint_cost(form) = |union of deriv over its values| + combining instructions
keep the few hundred forms of lowest joint_cost per target
```
In my test, stage one gave about 10^5 divisibility hits in 4 s and stage two took about 100 s in pure Python. Compiled code should need well under a second per target.

**4. Bundle selection by density, before the first target.** Keep the top 50–200 decompositions per target. Then repeatedly add the intermediate value v that maximises (sum over targets of the drop in estimated cost with v in the pool) minus the cost of v, and stop when the gain is not positive. This overlaps the "shared within two steps" step of public engines. The differences are deep alternatives from item 3 and cost per target served as the criterion.

**5. Complete cost table below N, and a near-quotient memo.** Compute a tree cost for every integer below 2^24–2^27 from the puzzle's start values, level by level. Take products by enumerating multiples. Take sums and differences only against a small cheap set, after checking that restriction against the exhaustive depth ≤ 5 table. Use it to price remainders and quotients during start-up, and key the reduction memo by (divisor product, offset). Benefit is unknown and probably modest.

**Not worth trying.**
- Generic magnitude ladders: every magnitude is already reached by depth 4–5.
- Exact joint search beyond about 10 instructions: 2·10^14 sets at 12 steps from a single seed.
- Grammar-style global compressors on digit strings: digit tables already measured as no help, and the theory shows the greedy rules are provably weak.
- More work on making the single first target cheaper for its own sake: the table search is within about 3 instructions of the estimated floor.

### Gaps
- Whether the later rate depends on the early pool is unmeasured. It decides everything in this section, and item 1 measures it.
- The 2-bit collision loss is calibrated only to 12 steps from one seed and to depth 4 from real start values. Its value at depth 30–50 is unknown, which is why the model range is as wide as 43–52.
- The share called inherent is a model output and has no proof behind it.
